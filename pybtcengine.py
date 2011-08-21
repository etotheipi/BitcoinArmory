################################################################################
#
# Project: PyBtcEngine
# Author:  Alan Reiner
# Date:    11 July, 2011
# Descr:   Modified from the Sam Rushing code.   The original header comments
#          of the original code is below, maintaining reference to the original 
#          source code, for reference.  The code was pulled from his git repo
#          on 10 July, 2011.
#
################################################################################

#
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
#import lisecdsa

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
USE_TESTNET = False

if USE_TESTNET:
   ##### TESTNET #####
   BITCOIN_PORT = 18333
   BITCOIN_MAGIC = '\xfa\xbf\xb5\xda'
   GENESIS_BLOCK_HASH_HEX = '08b067b31dc139ee8e7a76a4f2cfcca477c4c06e1ef89f4ae308951907000000'
   GENESIS_BLOCK_HASH = '\x08\xb0g\xb3\x1d\xc19\xee\x8ezv\xa4\xf2\xcf\xcc\xa4w\xc4\xc0n\x1e\xf8\x9fJ\xe3\x08\x95\x19\x07\x00\x00\x00'
   ADDRBYTE = '\x6f'
else:
   ##### MAIN NETWORK #####
   BITCOIN_PORT = 8333
   BITCOIN_MAGIC = '\xf9\xbe\xb4\xd9'
   GENESIS_BLOCK_HASH_HEX = '6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000'
   GENESIS_BLOCK_HASH = 'o\xe2\x8c\n\xb6\xf1\xb3r\xc1\xa6\xa2F\xaec\xf7O\x93\x1e\x83e\xe1Z\x08\x9ch\xd6\x19\x00\x00\x00\x00\x00'
   ADDRBYTE = '\x00'

b58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
NOHASH = '00'*32

LITTLEENDIAN = '<';
BIGENDIAN = '>';
COIN = 1e8
UNINITIALIZED = None
UNKNOWN = -2


def default_error_function(msg):
   print ''
   print '***ERROR*** : ', msg
   print 'Aborting run'
   exit(0)

def prettyHex(theStr, indent='', withAddr=True, major=8, minor=8):
   outStr = ''
   sz = len(theStr)
   nchunk = int((sz-1)/minor) + 1;
   for i in range(nchunk):
      if i%major==0:
         outStr += '\n'  + indent 
         if withAddr:
            locStr = int_to_hex(i*minor/2, widthBytes=2, endOut=BIGENDIAN)
            outStr +=  '0x' + locStr + ':  '
      outStr += theStr[i*minor:(i+1)*minor] + ' '
   return outStr

def pprintHex(theStr, indent='', major=8, minor=8):
   print prettyHex(theStr, indent, major, minor)


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
 

'''
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
'''

# Accidentally took a shortcut through the Base58 procedure, so
# the old code won't work with non-main-network addresses.  Here
# I replace int_to_base58Str(), etc, with the correct conversion
# directly to and from Binary.
def binary_to_addrStr(binstr):
   padding = 0;
   for b in binstr:
      if b=='\x00':
         padding+=1
      else:
         break

   n = 0
   for ch in binstr:
      n *= 256
      n += ord(ch)
  
   b58 = '' 
   while n > 0:
      n, r = divmod (n, 58)
      b58 = b58_digits[r] + b58
   return '1'*padding + b58


def addrStr_to_binary(addr):
   # Count the zeros ('1' characters) at the beginning
   padding = 0;
   for c in addr:
      if c=='1':
         padding+=1
      else:
         break

   n = 0
   for ch in addr:
      n *= 58
      n += b58_digits.index(ch)
   
   binOut = ''
   while n>0:
      d,m = divmod(n,256)
      binOut = chr(m) + binOut 
      n = d
   return '\x00'*padding + binOut
   
     

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



# Taken directly from rpc.cpp in reference bitcoin client, 0.3.24
def binaryBits_to_difficulty(b):
   i = binary_to_int(b)
   nShift = (i >> 24) & 0xff
   dDiff = float(0x0000ffff) / float(i & 0x00ffffff)
   while nShift < 29:
      dDiff *= 256.0
      nShift += 1
   while nShift > 29:
      dDiff /= 256.0
      nShift -= 1
   return dDiff

# TODO:  I don't actually know how to do this, yet...
def difficulty_to_binaryBits(i):
   pass
   

################################################################################
################################################################################
#  Classes for reading and writing large binary objects
################################################################################
################################################################################
UBYTE, USHORT, UINT32, UINT64, VAR_INT, FLOAT, BINARY_CHUNK = range(7)

# Seed this object with binary data, then read in its pieces sequentially
class BinaryUnpacker(object):
   def __init__(self, binaryStr):
      self.binaryStr = binaryStr
      self.pos = 0

   def getSize(self): return len(self.binaryStr)
   def getRemainingSize(self): return len(self.binaryStr) - self.pos
   def getBinaryString(self): return self.binaryStr
   def append(self, binaryStr): self.binaryStr += binaryStr
   def advance(self, bytesToAdvance): self.pos += bytesToAdvance
   def rewind(self, bytesToRewind): self.pos -= bytesToRewind
   def resetPosition(self, toPos=0): self.pos = toPos
   def getPosition(self): return self.pos

   def get(self, varType, sz=0, endianness=LITTLEENDIAN):
      pos = self.pos
      if varType == UINT32:
         value = unpack('<I', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == UINT64:
         value = unpack('<Q', self.binaryStr[pos:pos+8])[0]
         self.advance(8)
         return value
      elif varType == UBYTE:
         value = unpack('<B', self.binaryStr[pos:pos+1])[0]
         self.advance(1)
         return value
      elif varType == USHORT:
         value = unpack('<H', self.binaryStr[pos:pos+2])[0]
         self.advance(2)
         return value
      elif varType == VAR_INT:
         [value, nBytes] = unpackVarInt(self.binaryStr[pos:pos+9])
         self.advance(nBytes)
         return value
      elif varType == FLOAT:
         value = unpack('<f', self.binaryStr[pos:pos+4])
         self.advance(4)
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
      elif varType == FLOAT:
         self.binaryConcat += pack('<f', theData)
      elif varType == BINARY_CHUNK:
         self.binaryConcat += theData
      else:
         print 'Var Type not recognized!  VarType =', varType
         assert(False)

################################################################################


################################################################################
# ECDSA CLASSES
#
#    Based on the ECDSA code posted by Lis on the Bitcoin forums: 
#    http://forum.bitcoin.org/index.php?topic=23241.0
#
################################################################################


 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

################################################################################

# ECDSA Import from Lis http://bitcointalk.org/index.php?topic=23241.0
#
################################################################################
class lisecdsa:
   @staticmethod
   def inverse_mod( a, m ):
      if a < 0 or m <= a: a = a % m
      c, d = a, m
      uc, vc, ud, vd = 1, 0, 0, 1
      while c != 0:
         q, c, d = divmod( d, c ) + ( c, )
         uc, vc, ud, vd = ud - q*uc, vd - q*vc, uc, vc
      assert d == 1
      if ud > 0: return ud
      else: return ud + m

   class CurveFp( object ):
      def __init__( self, p, a, b ):
         self.__p = p
         self.__a = a
         self.__b = b
   
      def p( self ):
         return self.__p
   
      def a( self ):
         return self.__a
   
      def b( self ):
         return self.__b
   
      def contains_point( self, x, y ):
         return ( y * y - ( x * x * x + self.__a * x + self.__b ) ) % self.__p == 0
   
   class Point( object ):
      def __init__( self, curve, x, y, order = None ):
         self.__curve = curve
         self.__x = x
         self.__y = y
         self.__order = order
         if self.__curve: assert self.__curve.contains_point( x, y )
         if order: assert self * order == INFINITY
    
      def __add__( self, other ):
         if other == INFINITY: return self
         if self == INFINITY: return other
         assert self.__curve == other.__curve
         if self.__x == other.__x:
            if ( self.__y + other.__y ) % self.__curve.p() == 0:
               return INFINITY
            else:
               return self.double()
   
         p = self.__curve.p()
         l = ( ( other.__y - self.__y ) * lisecdsa.inverse_mod(other.__x - self.__x, p) ) % p
         x3 = ( l * l - self.__x - other.__x ) % p
         y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
         return lisecdsa.Point( self.__curve, x3, y3 )
   
      def __mul__( self, other ):
         def leftmost_bit( x ):
            assert x > 0
            result = 1L
            while result <= x: result = 2 * result
            return result / 2
   
         e = other
         if self.__order: e = e % self.__order
         if e == 0: return INFINITY
         if self == INFINITY: return INFINITY
         assert e > 0
         e3 = 3 * e
         negative_self = lisecdsa.Point( self.__curve, self.__x, -self.__y, self.__order )
         i = leftmost_bit( e3 ) / 2
         result = self
         while i > 1:
            result = result.double()
            if ( e3 & i ) != 0 and ( e & i ) == 0: result = result + self
            if ( e3 & i ) == 0 and ( e & i ) != 0: result = result + negative_self
            i = i / 2
         return result
   
      def __rmul__( self, other ):
         return self * other
   
      def __str__( self ):
         if self == INFINITY: return "infinity"
         return "(%d,%d)" % ( self.__x, self.__y )
   
      def double( self ):
         if self == INFINITY:
            return INFINITY
   
         p = self.__curve.p()
         a = self.__curve.a()
         l = ( (3 * self.__x * self.__x + a) * lisecdsa.inverse_mod(2 * self.__y, p) ) % p
         x3 = ( l * l - 2 * self.__x ) % p
         y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
         return lisecdsa.Point( self.__curve, x3, y3 )
   
      def x( self ):
         return self.__x
   
      def y( self ):
         return self.__y
   
      def curve( self ):
         return self.__curve
      
      def order( self ):
         return self.__order
         
   
   
   # secp256k1
   _p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
   _r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
   _b = 0x0000000000000000000000000000000000000000000000000000000000000007L
   _a = 0x0000000000000000000000000000000000000000000000000000000000000000L
   _Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
   _Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L
   
   class Signature( object ):
      def __init__( self, r, s ):
         self.r = r
         self.s = s
         
   class Public_key( object ):
      def __init__( self, generator, point ):
         self.curve = generator.curve()
         self.generator = generator
         self.point = point
         n = generator.order()
         if not n:
            raise RuntimeError, "Generator point must have order."
         if not n * point == INFINITY:
            raise RuntimeError, "Generator point order is bad."
         if point.x() < 0 or n <= point.x() or point.y() < 0 or n <= point.y():
            raise RuntimeError, "Generator point has x or y out of range."
   
      def verifies( self, hash, signature ):
         G = self.generator
         n = G.order()
         r = signature.r
         s = signature.s
         if r < 1 or r > n-1: return False
         if s < 1 or s > n-1: return False
         c = lisecdsa.inverse_mod( s, n )
         u1 = ( hash * c ) % n
         u2 = ( r * c ) % n
         xy = u1 * G + u2 * self.point
         v = xy.x() % n
         return v == r
   
   class Private_key( object ):
      def __init__( self, public_key, secret_multiplier ):
         self.public_key = public_key
         self.secret_multiplier = secret_multiplier
   
      def der( self ):
         hex_der_key = '06052b8104000a30740201010420' + \
                       '%064x' % self.secret_multiplier + \
                       'a00706052b8104000aa14403420004' + \
                       '%064x' % self.public_key.point.x() + \
                       '%064x' % self.public_key.point.y()
         return hex_der_key.decode('hex')
   
      def sign( self, hash, random_k ):
         G = self.public_key.generator
         n = G.order()
         k = random_k % n
         p1 = k * G
         r = p1.x()
         if r == 0: raise RuntimeError, "amazingly unlucky random number r"
         s = ( lisecdsa.inverse_mod( k, n ) * \
                  ( hash + ( self.secret_multiplier * r ) % n ) ) % n
         if s == 0: raise RuntimeError, "amazingly unlucky random number s"
         return lisecdsa.Signature( r, s )
   
INFINITY = lisecdsa.Point( None, None, None )
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
   



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

def isValidEcPoint(x,y):
   return EC_Curve.contains_point(x,y)


# We can identify an address string by its first byte upon conversion
# back to binary.  Return -1 if checksum doesn't match
def checkAddrType(addrBin):
   first20, chk4 = addrBin[:-4], addrBin[-4:]
   chkBytes = hash256(first20)
   if chkBytes[:4] == chk4:
      return addrBin[0]

# Check validity of a BTC address in its binary form, as would
# be found inside a pkScript.  Usually about 24 bytes
def checkAddrBinValid(addrBin, netbyte=ADDRBYTE):
   return checkAddrType(addrBin) == netbyte

# Check validity of a BTC address in "1Ghfk38dDF..." form
def checkAddrStrValid(addrStr):
   return checkAddrBinValid(addrStr_to_binary(addrStr))

SCRIPT_STANDARD = 0
SCRIPT_COINBASE = 1
SCRIPT_UNKNOWN  = 2

def getTxOutScriptType(binScript):
   if binScript[:2] == hex_to_binary('4104'):
      is65B = len(binScript) == 67
      lastByteMatch = binScript[-1] == int_to_binary(172)
      if (is65B and lastByteMatch):
         return SCRIPT_COINBASE
   else:
      is1 = binScript[ 0] == int_to_binary(118)
      is2 = binScript[ 1] == int_to_binary(169)
      is3 = binScript[-2] == int_to_binary(136)
      is4 = binScript[-1] == int_to_binary(172)
      if (is1 and is2 and is3 and is4):
         return SCRIPT_STANDARD

   return SCRIPT_UNKNOWN
   
def TxInScriptExtractKeyAddr(binScript):
   try:
      pubKeyBin = binScript[-65:]
      newAcct = BtcAddress().createFromPublicKey(pubKeyBin)
      return (newAcct.calculateAddrStr(), \
              binary_to_hex(pubKeyBin[1:], BIGENDIAN)) # LITTLE_ENDIAN
   except:
      # No guarantee that this script is meaningful (like in the genesis block)
      return ('SignatureForCoinbaseTx', 'SignatureForCoinbaseTx')

def TxOutScriptExtractKeyAddr(binScript):
   txoutType = getTxOutScriptType(binScript)
   if txoutType == SCRIPT_UNKNOWN:
      return '<Non-standard TxOut script>'

   if txoutType == SCRIPT_COINBASE:
      newAcct = BtcAddress().createFromPublicKey(binScript[1:66])
      return newAcct.calculateAddrStr()
   elif txoutType == SCRIPT_STANDARD:
      newAcct = BtcAddress().createFromPublicKeyHash160(binScript[3:23])
      return newAcct.getAddrStr()


# BtcAccount -- I gotta come up with a better name for this
# Store all information about an address string.  
# Having the privateKey is the most data.  Public key is next
# Finally, you frequently just have someone's address, without
# even having their public key
#
# The "createFrom" methods actually calculate the data below it
# The serialize/unserialize methods do no extra calculation, or
# consistency checks, because the lisecdsa library is slow, and 
# we don't want to spend the time verifying thousands of keypairs
# There's a reason we wrote out the pubkey and addresses...
class BtcAddress(object):
   def __init__(self):
      self.privKeyInt = UNINITIALIZED
      self.pubKeyXInt = UNINITIALIZED
      self.pubKeyYInt = UNINITIALIZED
      self.addrStr    = UNINITIALIZED 
      self.lisPubKey  = UNINITIALIZED  # the underlying ECDSA objects from Lis
      self.lisPrivKey = UNINITIALIZED  # the underlying ECDSA objects from Lis
      # All other information can always be computed on the fly
      self.hasPubKey  = False
      self.hasPrivKey = False

   def generateNew(self):
      # TODO:  check for python <=2.3 to warn if randrange gens "small" numbers
      self.createFromPrivateKey(random.randrange(EC_Order))
      return self

   def createFromPrivateKey(self, privKeyInt):
      self.privKeyInt = privKeyInt
      pubKeyPoint  = EC_GenPt * self.privKeyInt
      self.pubKeyXInt = pubKeyPoint.x()
      self.pubKeyYInt = pubKeyPoint.y()
      self.lisPubKey  = lisecdsa.Public_key(EC_GenPt, pubKeyPoint)
      self.lisPrivKey = lisecdsa.Private_key(self.lisPubKey, self.privKeyInt)
      self.hasPubKey  = True
      self.hasPrivKey = True
      self.addrStr = self.calculateAddrStr()
      return self

   def createFromPublicKey(self, pubkey):
      if isinstance(pubkey, EC_Point):
         self.pubKeyXInt = pubkey.x()
         self.pubKeyYInt = pubkey.y()
      elif isinstance(pubkey, tuple):
         self.pubKeyXInt = pubkey[0]
         self.pubKeyYInt = pubkey[1]
      elif isinstance(pubkey, str):
         # assume 65-byte binary string
         assert( len(pubkey) == 65 )
         leadByte        = binary_to_int(pubkey[:1    ], BIGENDIAN)
         self.pubKeyXInt = binary_to_int(pubkey[ 1:33 ], BIGENDIAN)
         self.pubKeyYInt = binary_to_int(pubkey[   33:], BIGENDIAN)
         assert( leadByte == 4 )
      # If "contains_point" error... the supplied XY-coords are not
      # on the secp256k1 elliptic curve
      pubKeyPoint = EC_Point(EC_Curve, self.pubKeyXInt, self.pubKeyYInt)
      self.lisPubKey  = lisecdsa.Public_key(EC_GenPt, pubKeyPoint)
      self.hasPubKey  = True
      self.hasPrivKey = False
      self.addrStr = self.calculateAddrStr()
      return self

   def createFromPublicKeyHash160(self, pubkeyHash160, netbyte=ADDRBYTE):
      chkSum  = hash256(netbyte + pubkeyHash160)[:4]
      self.addrStr = binary_to_addrStr( netbyte + pubkeyHash160 + ckhSum)
      self.hasPubKey  = False
      self.hasPrivKey = False
      return self

   def createFromAddrStr(self, addrStr):
      self.addrStr = addrStr
      assert(self.checkAddressValid())
      self.hasPubKey  = False
      self.hasPrivKey = False
      return self

   def calculateAddrStr(self, netbyte=ADDRBYTE):
      assert( self.hasPubKey )
      xBinBE     = int_to_binary(self.pubKeyXInt, widthBytes=32, endOut=BIGENDIAN)
      yBinBE     = int_to_binary(self.pubKeyYInt, widthBytes=32, endOut=BIGENDIAN)
      binPubKey  = '\x04' + xBinBE + yBinBE
      keyHash    = hash160(binPubKey)
      chkSum     = hash256(netbyte + keyHash)[:4]
      return       binary_to_addrStr(netbyte + keyHash + chkSum)

   def getAddrStr(self):
      if self.addrStr==UNINITIALIZED:
         return self.calculateAddrStr()
      return self.addrStr

   def generateDERSignature(self, binToSign):
      assert( self.hasPrivKey )
      self.prepareKeys()
      intSign = binary_to_int(binToSign)
      sig = self.lisPrivKey.sign(intSign, random.randrange(EC_Order))
      rBin   = int_to_binary(sig.r, endOut=BIGENDIAN)
      sBin   = int_to_binary(sig.s, endOut=BIGENDIAN)
      rSize  = int_to_binary(len(rBin))
      sSize  = int_to_binary(len(sBin))
      rsSize = int_to_binary(len(rBin) + len(sBin) + 4)
      return '\x30' + rsSize + '\x02' + rSize + rBin + '\x02' + sSize + sBin

   def verifyDERSignature(self, binToVerify, derToVerify):
      assert(self.hasPubKey)
      self.prepareKeys()
      codeByte = derToVerify[0]
      nBytes   = binary_to_int(derToVerify[1])
      rsStr    = derToVerify[2:]
      assert(codeByte == '\x30')
      assert(nBytes == len(rsStr))
      # Read r
      codeByte  = rsStr[0]
      rBytes    = binary_to_int(rsStr[1])
      r         = binary_to_int(rsStr[2:2+rBytes], endIn=BIGENDIAN)
      assert(codeByte == '\x02')
      sStr      = rsStr[2+rBytes:]
      # Read s
      codeByte  = sStr[0]
      sBytes    = binary_to_int(sStr[1])
      s         = binary_to_int(sStr[2:2+sBytes], endIn=BIGENDIAN)
      assert(codeByte == '\x02')
      # Now we have the (r,s) values of the 
      lisSignature = EC_Sig(r,s)
      intVerify = binary_to_int(binToVerify)
      return self.lisPubKey.verifies(intVerify, lisSignature)

   def prepareKeys(self, checkKeyMatch=True):
      # We may have the key data, but may not have created the lisecdsa objects
      if self.hasPubKey and self.lisPubKey==UNINITIALIZED:
         pubKeyPoint     = EC_Point(EC_Curve, self.pubKeyXInt, self.pubKeyYInt)
         self.lisPubKey  = lisecdsa.Public_key(EC_GenPt, pubKeyPoint)

      if self.hasPrivKey and self.lisPrivKey==UNINITIALIZED:
         self.lisPrivKey = lisecdsa.Private_key(self.lisPubKey, self.privKeyInt)

      # If we already had both a public and private key, we might consider
      # checking that they are a match
      if self.hasPubKey and self.hasPrivKey and checkKeyMatch:
         assert(self.checkPubPrivKeyPairMatch())


   # We make this pseudo-static so that we can use it for arbitrary address
   def checkAddressValid(self):
      return checkAddrStrValid(self.addrStr);

   def checkPubPrivKeyPairMatch(self):
      assert( self.hasPubKey and self.hasPrivKey )
      privToPubPoint = EC_GenPt * self.privKeyInt
      xMatches = privToPubPoint.x() == self.pubKeyXInt
      yMatches = privToPubPoint.y() == self.pubKeyYInt
      return (xMatches and yMatches)

   
   def addrStr_serialize(self):
      # Address string has a maximum length of 34 bytes... so let's left-pad
      # the address with \x00 bytes and start reading at the first 1
      addrLen = len(self.addrStr)
      return int_to_binary(addrLen) + self.addrStr  # append reg string to binary string...okay
   def addrStr_unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         addrData = toUnpack
      else:
         addrData = BinaryUnpacker(toUnpack)
      addrLen      = addrData.get(UBYTE)
      self.addrStr = addrDate.get(BINARY_CHUNK, addrLen)
   

   def pubKey_serialize(self):
      if not self.hasPubKey:
         return '\x00'
      else:
         xBinBE = int_to_binary(self.pubKeyXInt, widthBytes=32, endOut=BIGENDIAN)
         yBinBE = int_to_binary(self.pubKeyYInt, widthBytes=32, endOut=BIGENDIAN)
         return '\x01' + '\x04' + xBinBE + yBinBE
   def pubKey_unserialize(self, toUnpack):
      # Does not recompute addrStr
      if isinstance(toUnpack, BinaryUnpacker):
         keyData = toUnpack
      else:
         keyData = BinaryUnpacker(toUnpack)

      leadByte = keyData.get(UBYTE)
      if leadByte==0:
         self.pubKeyXInt == UNINITIALIZED
         self.pubKeyYInt == UNINITIALIZED
         self.hasPubKey = False
      else:
         leadByte = keyData.get(UBYTE)
         assert(leadByte == 4)
         self.pubKeyXInt = binary_to_int(keyData.get(BINARY_CHUNK, 32), BIGENDIAN)
         self.pubKeyYInt = binary_to_int(keyData.get(BINARY_CHUNK, 32), BIGENDIAN)
         self.hasPubKey = True



   def privKey_serialize(self):
      if not self.hasPrivKey:
         return '\x00'
      else:
         privKeyBin = int_to_binary(self.privKeyInt, widthBytes=32, endOut=BIGENDIAN)
         return '\x01' + privKeyBin
   def privKey_unserialize(self, toUnpack):
      # Does not recompute public key and addr -- run consistency check
      if isinstance(toUnpack, BinaryUnpacker):
         keyData = toUnpack
      else:
         keyData = BinaryUnpacker(toUnpack)
      leadByte = keyData.get(UBYTE)
      if leadByte==0:
         self.privKeyInt = UNINITIALIZED
         self.hasPrivKey = False
      else:
         privKeyBin = keyData.get(BINARY_CHUNK, 32)
         self.privKeyInt = binary_to_int(privKeyBin, BIGENDIAN)
         self.hasPrivKey = True

   
   def serialize(self):
      # We should ALWAYS have an address available.  But not necessary pub and
      # and priv keys.  Use 0 to
      addrBin = self.addrStr_serialize()
      pubkBin = self.pubKey_serialize()
      prvkBin = self.privKey_serialize()
      return addrBin + pubkBin + prvkBin

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         theData = toUnpack
      else:
         theData = BinaryUnpacker(toUnpack)
      self.addrStr_unserialize( theData ) 
      self.pubKey_unserialize( theData ) 
      self.privKey_unserialize( theData ) 

   def pprint(self, withPrivKey=False):
      print '  BTC Address:     ', 
      if self.addrStr==UNINITIALIZED:
         print 'UNINITIALIZED'
      else:
         print self.addrStr
         print '  Have Public Key: ', self.hasPubKey
         print '  Have Private Key:', self.hasPrivKey
         if self.hasPubKey:
            print '  Public Key Hex (Big-Endian):  '
            print '     04', int_to_hex(self.pubKeyXInt, 32, BIGENDIAN)
            print '       ', int_to_hex(self.pubKeyYInt, 32, BIGENDIAN)
         if withPrivKey and self.hasPrivKey:
            print '  Private Key Hex (Big-Endian): '
            print '       ', int_to_hex(self.privKeyInt, 32, BIGENDIAN)
      
      



# Finally done with all the base conversion functions and ECDSA code
# Now define the classes for the objects that will use this


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
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.txOutHash, BIGENDIAN), \
                  '(BE)'
      print indstr + indent + 'TxOutIndex:', self.index
      

#####
class TxIn(object):
   def __init__(self):
      self.outpoint   = UNINITIALIZED
      self.binScript  = UNINITIALIZED
      self.intSeq     = UNINITIALIZED
      self.isCoinbase = UNKNOWN

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
      #self.outpoint.pprint(nIndent+1)
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.outpoint.txOutHash, BIGENDIAN), '(BE)'
      print indstr + indent + 'TxOutIndex:', self.outpoint.index
      source = TxInScriptExtractKeyAddr(self.binScript)[0]
      if 'Sign' in source:
         print indstr + indent + 'Script:    ', '('+source+')'
      else:
         print indstr + indent + 'Source:    ', '('+source+')'
      print indstr + indent + 'Seq:       ', self.intSeq
      

#####
class TxOut(object):
   def __init__(self):
      self.value       = UNINITIALIZED
      self.binPKScript = UNINITIALIZED

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
      print indstr + indent + 'Value:   ', self.value, '(', float(self.value) / COIN, ')'
      txoutType = getTxOutScriptType(self.binPKScript)
      if txoutType == SCRIPT_COINBASE:
         print indstr + indent + 'Script:   PubKey(%s) OP_CHECKSIG' % \
                              (TxOutScriptExtractKeyAddr(self.binPKScript),)
      elif txoutType == SCRIPT_STANDARD:
         print indstr + indent + 'Script:   OP_DUP OP_HASH (%s) OP_EQUAL OP_CHECKSIG' % \
                              (TxOutScriptExtractKeyAddr(self.binPKScript),)
      else:
         print indstr + indent + 'Script:   <Non-standard script!>'

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

      startPos = txData.getPosition()
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
      endPos = txData.getPosition()
      self.nBytes = endPos - startPos
      self.thisHash = hash256(self.serialize())
      return self
      
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      thisHash = hash256(self.serialize())
      print indstr + 'Transaction:'
      print indstr + indent + 'TxHash:   ', binary_to_hex(thisHash, BIGENDIAN), '(BE)'
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
   def __init__(self):
      self.theHash      = UNINITIALIZED 
      self.version      = UNINITIALIZED 
      self.prevBlkHash  = UNINITIALIZED 
      self.merkleRoot   = UNINITIALIZED 
      self.timestamp    = UNINITIALIZED 
      self.diffBits     = UNINITIALIZED 
      self.nonce        = UNINITIALIZED 
      # Use these fields for storage of block information, but are not otherwise
      # part of the serialized data structure
      self.numTx        = UNINITIALIZED 
      self.blkHeight    = UNINITIALIZED 
      self.fileByteLoc  = UNINITIALIZED 
      self.nextBlkHash  = UNINITIALIZED 
      self.intDifficult = UNINITIALIZED 
      self.sumDifficult = UNINITIALIZED 
      self.isMainChain  = False  # true until proven innocent
      self.isOrphan     = True  # true until proven innocent

   def serialize(self):
      assert( not self.version == UNINITIALIZED)
      binOut = BinaryPacker()
      binOut.put(UINT32, self.version)
      binOut.put(BINARY_CHUNK, self.prevBlkHash)
      binOut.put(BINARY_CHUNK, self.merkleRoot)
      binOut.put(UINT32, self.timestamp)
      binOut.put(BINARY_CHUNK, self.diffBits)
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
      self.diffBits    = blkData.get(BINARY_CHUNK, 4)
      self.nonce       = blkData.get(UINT32)
      self.theHash     = hash256(self.serialize())
      return self

   ##### Serialize the header with all the extra information not normally
   #     considered to be part of the header
   def serializeWithExtra(self):
      binData = BinaryPacker()
      binData.put(BINARY_CHUNK, self.serialize() )

      def putData(dtype, theData, nBytes):
         unInit = theData==UNINITIALIZED
         binData.put(UBYTE, 0 if unInit else 1)
         if unInit:
            binData.put(BINARY_CHUNK, '\xff'*nBytes)
         else:
            if dtype == BINARY_CHUNK:
               binData.put(BINARY_CHUNK, theData, nBytes)
            else:
               binData.put(dtype, theData)
             
      # TODO: should figure out a better way to store difficulty values
      putData(UINT32, self.numTx,        4)
      putData(BINARY_CHUNK, self.nextBlkHash,  32)
      putData(UINT64, self.fileByteLoc,  8)
      putData(FLOAT,  self.sumDifficult, 4)
      putData(UINT32, self.blkHeight,    4)
      putData(UBYTE,  self.isMainChain,  1)
      putData(UBYTE,  self.isOrphan,     1)
      return binData.getBinaryString()

   def unserializeWithExtra(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         binData = toUnpack 
      else: 
         binData = BinaryUnpacker( toUnpack )

      self.unserialize( binData )

      def getData(dtype, nBytes):
         unInit = binData.get(UBYTE)
         if unInit == 0:
            binData.advance(nBytes)
            return UNINITIALIZED 
         else:
            return binData.get(dtype, nBytes)
            

      self.numTx        = getData(UINT32, 4)
      self.nextBlkHash  = getData(BINARY_CHUNK, 32)
      self.fileByteLoc  = getData(UINT64, 8)
      self.sumDifficult = getData(FLOAT, 4)
      self.blkHeight    = getData(UINT32, 4)
      self.isMainChain  = getData(UBYTE, 1)
      self.isOrphan     = getData(UBYTE, 1)
      #getData(self.numTx,        4)
      #getData(self.nextBlkHash,  32)
      #getData(self.fileByteLoc,  8)
      #getData(self.intDifficult, 8)
      #getData(self.sumDifficult, 8)
      #getData(self.blkHeight,    4)
      #getData(self.isOrphan,     1)
      #self.numTx         = binary_to_int(self.numTx)
      #self.fileByteLoc   = binary_to_int(self.fileByteLoc)
      #self.intDifficult  = binary_to_int(self.intDifficult)
      #self.sumDifficult  = binary_to_int(self.sumDifficult)
      #self.blkHeight     = binary_to_int(self.blkHeight)
      #self.isOrphan      = binary_to_int(self.isOrphan)
      return self

   def getHash(self, endian=LITTLEENDIAN):
      assert( not self.version == UNINITIALIZED)
      if len(self.theHash) < 32:
         self.theHash = hash256(self.serialize())
      outHash = self.theHash 
      if endian==BIGENDIAN: 
         outHash = binary_switchEndian(outHash)
      return outHash

   def getHashHex(self, endian=LITTLEENDIAN):
      assert( not self.version == UNINITIALIZED)
      if len(self.theHash) < 32:
         self.theHash = hash256(self.serialize())
      return binary_to_hex(self.theHash, endian)

   def getDifficulty(self):
      assert(not self.diffBits == UNINITIALIZED)
      self.intDifficult = binaryBits_to_difficulty(self.diffBits)
      return self.intDifficult

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'BlockHeader:'
      print indstr + indent + 'Hash:      ', binary_to_hex( self.theHash, endOut=BIGENDIAN), '(BE)'
      print indstr + indent + 'Version:   ', self.version     
      print indstr + indent + 'PrevBlock: ', binary_to_hex(self.prevBlkHash, endOut=BIGENDIAN), '(BE)'
      print indstr + indent + 'MerkRoot:  ', binary_to_hex(self.merkleRoot, endOut=BIGENDIAN), '(BE)'
      print indstr + indent + 'Timestamp: ', self.timestamp 
      fltDiff = binaryBits_to_difficulty(self.diffBits)
      print indstr + indent + 'Difficulty:', fltDiff, '('+binary_to_hex(self.diffBits)+')'
      print indstr + indent + 'Nonce:     ', self.nonce    
      if not self.blkHeight==UNINITIALIZED:
         print indstr + indent + 'BlkHeight: ', self.blkHeight    
      if not self.blkHeight==UNINITIALIZED:
         print indstr + indent + 'BlkFileLoc:', self.fileByteLoc    
      if not self.nextBlkHash==UNINITIALIZED:
         #print indstr + indent + 'NextBlock: ', binary_to_hex(self.nextBlkHash)
         print indstr + indent + 'NextBlock: ', self.nextBlkHash
      if not self.numTx==UNINITIALIZED:
         print indstr + indent + 'NumTx:     ', self.numTx    
      if not self.intDifficult==UNINITIALIZED:
         print indstr + indent + 'Difficulty:', self.intDifficult    
      if not self.sumDifficult==UNINITIALIZED:
         print indstr + indent + 'DiffSum:   ', self.sumDifficult    


class BlockData(object):
   def __init__(self):
      self.numTx      = UNINITIALIZED
      self.txList     = UNINITIALIZED
      self.merkleTree = UNINITIALIZED
      self.merkleRoot = UNINITIALIZED

   def serialize(self):
      assert( not self.numTx == UNINITIALIZED )
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


   def getTxHashList(self):
      if( self.numTx == UNINITIALIZED ):
         self.getMerkleRoot()
      return self.merkleTree[:self.numTx]
      

   def getMerkleRoot(self):
      assert( not self.numTx == UNINITIALIZED )
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
   def __init__(self):
      self.blockHeader = UNINITIALIZED
      self.blockData   = UNINITIALIZED

   def serialize(self):
      assert( not self.blockHeader == UNINITIALIZED )
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

      return SCRIPT_NO_ERROR
      
      

   def executeOpCode(self, opcode, scriptUnpacker, stack):

      stackSizeAtLeast = lambda n: (len(self.stack) >= n)

      #print 'OP_CODE: ', opcode

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

         if not hashtype == 1:
            print 'Non-unity hashtypes not implemented yet! ( hashtype =', hashtype,')'
            assert(False)

         # 5. Make a copy of the transaction -- we will be hashing a modified version
         txCopy = Tx().unserialize( self.txNew.serialize() )

         # 6. Remove all OP_CODESEPARATORs
         subscript.replace( int_to_binary(OP_CODESEPARATOR), '')

         # 7. All the TxIn scripts in the copy are blanked (set to empty string)
         for txin in txCopy.inputs:
            txin.binScript = ''

         # 8. Script for the current input in the copy is set to subscript
         txCopy.inputs[self.txInIndex].binScript = subscript

         # 9. Prepare the signature and public key
         senderAddr = BtcAddress().createFromPublicKey(binPubKey)
         binHashCode = int_to_binary(hashtype, widthBytes=4)
         toHash = txCopy.serialize() + binHashCode
         hashToVerify = hash256(toHash)

         hashToVerify = binary_switchEndian(hashToVerify)
         if senderAddr.verifyDERSignature(hashToVerify, binSig):
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
      
   
         

   

# This is the remaining "end" of Sam Rushing's original code.  I'm not using any
# of it right now.  But I will eventually dissect it and take advantage of the work
# he's already done on networking and protocol
"""
   
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

"""


