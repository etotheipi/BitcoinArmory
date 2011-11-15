################################################################################
#
# Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    PyBtcEngine
# Author:     Alan Reiner
# Orig Date:  11 July, 2011
# Descr:      A mostly-complete BTC computational engine in Python.  Does not 
#             do any Blockchain management, but includes just about everything
#             else, including all the ECDSA signatures and verification.  
#             
#             Blockchain management is handled by the CppBlockUtils, C++ code
#             compiled with g++ and using SWIG to convert it to a .so/.dll.  
#             Please see Using_PyBtcEngine.README file for more information.
#
#             The file pybtcengine.methods.py has a fairly complete list of
#             methods available in this file, though it needs to be manually 
#             generated so it's sometimes lagging the code.
#       
#
################################################################################

import copy
import hashlib
import random
import socket
import time
import os
import pickle
import string
import sys
import shutil
import math


from struct import pack, unpack
import hashlib 
from pprint import pprint as pp
from datetime import datetime

VERSION = (0,5,0,0)  # (Major, Minor, Minor++, even-more-minor)


def sha1(bits):
   return hashlib.new('sha1', bits).digest()
def sha256(bits):
   return hashlib.new('sha256', bits).digest()
def ripemd160(bits):
   return hashlib.new('ripemd160', bits).digest()
def hash256(s):
   """ Double-SHA256 """
   return sha256(sha256(s))
def hash160(s):
   """ RIPEMD160( SHA256( binaryStr ) ) """
   return ripemd160(sha256(s))


################################################################################
# Load the C++ utilites here 
# If we have them, we can use them for accessing the blockchain, and efficient
# ECDSA operations (not implemented yet)
################################################################################
useCpp = False
try:
   import CppBlockUtils as Cpp
   useCpp = True
   # Was planning to throw in C++ hashing here, for speed.
   # But it's not actually faster -- probably slowed down
   # by the typemap and overhead of exchanging data with C++
except:
   print '***WARNING:  C++ block utilities not available.'
   print '             defaulting to [slower] python methods'
   print '             (blockchain will not be available'
print 'Using CppBlockUtils: ', useCpp
   



def getVersionString(vquad=VERSION, numPieces=4):
   vstr = '%d.%02d' % vquad[:2]
   if (vquad[2] > 0 or vquad[3] > 0) and numPieces>2:
      vstr += '.%02d' % vquad[2]
   if vquad[3] > 0 and numPieces>3:
      vstr += '.%03d' % vquad[3]
   return vstr

def getVersionInt(vquad=VERSION, numPieces=4):
   vint  = int(vquad[0] * 1e7)
   if numPieces>1:
      vint += int(vquad[1] * 1e5)
   if numPieces>2:
      vint += int(vquad[2] * 1e3)
   if numPieces>3:
      vint += int(vquad[3])
   return vint
   


class UnserializeError(Exception):
   pass
class BadAddressError(Exception):
   pass
class VerifyScriptError(Exception):
   pass
class FileExistsError(Exception):
   pass
class ECDSA_Error(Exception):
   pass
class PackerError(Exception):
   pass
class UnitializedBlockDataError(Exception):
   pass

# These are overriden for testnet
USE_TESTNET = False

##### MAIN NETWORK IS DEFAULT #####
if not USE_TESTNET:
   BITCOIN_PORT = 8333
   MAGIC_BYTES = '\xf9\xbe\xb4\xd9'
   GENESIS_BLOCK_HASH_HEX = '6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000'
   GENESIS_BLOCK_HASH = 'o\xe2\x8c\n\xb6\xf1\xb3r\xc1\xa6\xa2F\xaec\xf7O\x93\x1e\x83e\xe1Z\x08\x9ch\xd6\x19\x00\x00\x00\x00\x00'
   ADDRBYTE = '\x00'
else:
   BITCOIN_PORT = 18333
   MAGIC_BYTES  = '\xfa\xbf\xb5\xda'
   GENESIS_BLOCK_HASH_HEX = '08b067b31dc139ee8e7a76a4f2cfcca477c4c06e1ef89f4ae308951907000000'
   GENESIS_BLOCK_HASH = '\x08\xb0g\xb3\x1d\xc19\xee\x8ezv\xa4\xf2\xcf\xcc\xa4w\xc4\xc0n\x1e\xf8\x9fJ\xe3\x08\x95\x19\x07\x00\x00\x00'
   ADDRBYTE = '\x6f'


BLOCKCHAINS = {}
BLOCKCHAINS['\xf9\xbe\xb4\xd9'] = "Main Network"
BLOCKCHAINS['\xfa\xbf\xb5\xda'] = "Test Network"

NETWORKS = {}
BLOCKCHAINS['\x00'] = "Main Network"
BLOCKCHAINS['\x6f'] = "Test Network"
BLOCKCHAINS['\x34'] = "Namecoin"


   
def coin2str(nSatoshi, ndec=8, rJust=False):
   """
   Converts a raw value (1e-8 BTC) into a formatted string for display
   """
   # We make sure that when we truncate digits, it's actually applying rounding
   if ndec<8: 
      nSatoshi += 5 * 10**(7-ndec)
   s = str(long(nSatoshi))
   if len(s)<9: 
      s = s.rjust(9,'0')
   s = s.rjust(16,' ')
   s = s[:8] + '.' + s[8:8+ndec]
   if ndec==0: 
      s = s.strip('.')
   if not rJust: 
      s = s.strip(' ')
   return s
   

# Some useful constants to be used throughout everything
BASE58DIGITS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
LITTLEENDIAN = '<';
BIGENDIAN = '>';
COIN = long(1e8)
CENT = long(1e8/100.)
UNINITIALIZED = None
UNKNOWN = -2
MIN_TX_FEE = 50000
MIN_RELAY_TX_FEE = 10000



def prettyHex(theStr, indent='', withAddr=True, major=8, minor=8):
   """
   This is the same as pprintHex(), but returns the string instead of
   printing it to console.  This is useful for redirecting output to
   files, or doing further modifications to the data before display
   """
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

def pprintHex(theStr, indent='', withAddr=True, major=8, minor=8):
   """
   This method takes in a long hex string and prints it out into rows
   of 64 hex chars, in chunks of 8 hex characters, and with address
   markings on each row.  This means that each row displays 32 bytes,
   which is usually pleasant.  
   
   The format is customizable: you can adjust the indenting of the 
   entire block, remove address markings, or change the major/minor 
   grouping size (major * minor = hexCharsPerRow) 
   """
   print prettyHex(theStr, indent, withAddr, major, minor)




##### Switch endian-ness #####
def hex_switchEndian(s):
   """ Switches the endianness of a hex string (in pairs of hex chars) """
   pairList = [s[i]+s[i+1] for i in xrange(0,len(s),2)]
   return ''.join(pairList[::-1])
def binary_switchEndian(s):
   """ Switches the endianness of a binary string """
   return s[::-1]
 

##### INT/HEXSTR #####
def int_to_hex(i, widthBytes=0, endOut=LITTLEENDIAN):
   """ 
   Convert an integer (int() or long()) to hexadecimal.  Default behavior is 
   to use the smallest even number of hex characters necessary, and using
   little-endian.   Use the widthBytes argument to add 0-padding where needed
   if you are expecting constant-length output.
   """
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
   """
   Convert hex-string to integer (or long).  Default behavior is to interpret
   hex string as little-endian
   """
   hstr = h[:]  # copies data, no references
   if endIn==LITTLEENDIAN:
      hstr = hex_switchEndian(hstr)
   return( int(hstr, 16) )
 

##### HEXSTR/BINARYSTR #####
def hex_to_binary(h, endIn=LITTLEENDIAN, endOut=LITTLEENDIAN):
   """
   Converts hexadecimal to binary (in a python string).  Endianness is 
   only switched if (endIn != endOut)
   """
   bout = h[:]  # copies data, no references
   if not endIn==endOut:
      bout = hex_switchEndian(bout) 
   return bout.decode('hex_codec')
def binary_to_hex(b, endOut=LITTLEENDIAN, endIn=LITTLEENDIAN):
   """
   Converts binary to hexadecimal.  Endianness is only switched 
   if (endIn != endOut)
   """
   hout = b.encode('hex_codec')
   if not endOut==endIn:
      hout = hex_switchEndian(hout) 
   return hout

 
##### INT/BINARYSTR #####
def int_to_binary(i, widthBytes=0, endOut=LITTLEENDIAN):
   """
   Convert integer to binary.  Default behavior is use as few bytes
   as necessary, and to use little-endian.  This can be changed with
   the two optional input arguemnts.
   """
   h = int_to_hex(i,widthBytes)
   return hex_to_binary(h, endOut=endOut)

def binary_to_int(b, endIn=LITTLEENDIAN):
   """
   Converts binary to integer (or long).  Interpret as LE by default
   """
   h = binary_to_hex(b, endIn, LITTLEENDIAN)
   return hex_to_int(h)


EmptyHash = hex_to_binary('00'*32)
 

# BINARY/BASE58 CONVERSIONS
def binary_to_base58(binstr):
   """
   This method applies the Bitcoin-specific conversion from binary to Base58
   which may includes some extra "zero" bytes, such as is the case with the 
   main-network addresses.
   
   This method is labeled as outputting an "addrStr", but it's really this
   special kind of Base58 converter, which makes it usable for encoding other
   data, such as ECDSA keys or scripts.
   """
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
      b58 = BASE58DIGITS[r] + b58
   return '1'*padding + b58


def base58_to_binary(addr):
   """
   This method applies the Bitcoin-specific conversion from Base58 to binary
   which may includes some extra "zero" bytes, such as is the case with the 
   main-network addresses.
   
   This method is labeled as inputting an "addrStr", but it's really this
   special kind of Base58 converter, which makes it usable for encoding other
   data, such as ECDSA keys or scripts.
   """
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
      n += BASE58DIGITS.index(ch)
   
   binOut = ''
   while n>0:
      d,m = divmod(n,256)
      binOut = chr(m) + binOut 
      n = d
   return '\x00'*padding + binOut
   

   
     


def hash160_to_addrStr(binStr):
   """ 
   Converts the 20-byte pubKeyHash to 25-byte binary Bitcoin address
   which includes the network byte (prefix) and 4-byte checksum (suffix) 
   """
   addr21 = ADDRBYTE + binStr
   addr25 = addr21 + hash256(addr21)[:4]
   return binary_to_base58(addr25);

def addrStr_to_hash160(binStr):
   return base58_to_binary(binStr)[1:-4]





##### FLOAT/BTC #####
# https://en.bitcoin.it/wiki/Proper_Money_Handling_(JSON-RPC)
def ubtc_to_floatStr(n):
   return '%d.%08d' % divmod (n, COIN)
def floatStr_to_ubtc(s):
   return long(round(float(s) * COIN))
def float_to_btc (f):
   return long (round(f * COIN))


##### And a few useful utilities #####
def unixTimeToFormatStr(unixTime, formatStr='%Y-%b-%d %I:%M%p'):
   """ 
   Converts a unix time (like those found in block headers) to a 
   pleasant, human-readable format
   """
   dtobj = datetime.fromtimestamp(unixTime)
   dtstr = dtobj.strftime(formatStr)
   return dtstr[:-2] + dtstr[-2:].lower()


##### HEXSTR/VARINT #####
def packVarInt(n):
   """ Writes 1,3,5 or 9 bytes depending on the size of n """
   if   n < 0xfd:  return [chr(n), 1]
   elif n < 1<<16: return ['\xfd'+pack('<H',n), 3]
   elif n < 1<<32: return ['\xfe'+pack('<I',n), 5]
   else:           return ['\xff'+pack('<Q',n), 9]

def unpackVarInt(hvi):
   """ Returns a pair: the integer value and number of bytes read """
   code = unpack('<B', hvi[0])[0]
   if   code  < 0xfd: return [code, 1]
   elif code == 0xfd: return [unpack('<H',hvi[1:3])[0], 3]
   elif code == 0xfe: return [unpack('<I',hvi[1:5])[0], 5]
   elif code == 0xff: return [unpack('<Q',hvi[1:9])[0], 9]
   else: assert(False)




def fixChecksumError(binaryStr, chkSum, hashFunc=hash256):
   """ 
   Will only try to correct one byte, as that would be the most
   common error case.  Correcting two bytes is feasible, but I'm
   not going to bother implementing it until I need it.  If it's
   not a one-byte error, it's most likely a different problem
   """
   check = lambda b:  hashFunc(b).startswith(chkSum)

   # Maybe just the endian is off?
   if check(binary_switchEndian(binaryStr)):
      return binary_switchEndian(binaryStr)

   binaryArray = [b[i] for b in privKeyBinary]
   for byte in range(len(binaryArray)):
      origByte = binaryArray[byte]
      for val in range(256):
         binaryArray[byte] = chr(val)
         if check(''.join(binaryArray)):
            return ''.join(binaryArray)



# Taken directly from rpc.cpp in reference bitcoin client, 0.3.24
def binaryBits_to_difficulty(b):
   """ Converts the 4-byte binary difficulty string to a float """
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
UINT8, UINT16, UINT32, UINT64, VAR_INT, FLOAT, BINARY_CHUNK = range(7)

# Seed this object with binary data, then read in its pieces sequentially
class BinaryUnpacker(object):
   """
   Class for helping unpack binary streams of data.  Typical usage is
      >> bup     = BinaryUnpacker(myBinaryData)
      >> int32   = bup.get(UINT32)
      >> int64   = bup.get(VAR_INT)
      >> bytes10 = bup.get(BINARY_CHUNK, 10)
      >> ...etc...
   """
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
      """
      First argument is the data-type:  UINT32, VAR_INT, etc.
      If BINARY_CHUNK, need to supply a number of bytes to read, as well
      """
      pos = self.pos
      if varType == UINT32:
         value = unpack('<I', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == UINT64:
         value = unpack('<Q', self.binaryStr[pos:pos+8])[0]
         self.advance(8)
         return value
      elif varType == UINT8:
         value = unpack('<B', self.binaryStr[pos:pos+1])[0]
         self.advance(1)
         return value
      elif varType == UINT16:
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
      raise PackerError, "Var type not recognized!  VarType="+str(varType)
         
         

# Start a buffer for concatenating various blocks of binary data
class BinaryPacker(object):
   """
   Class for helping load binary data into a stream.  Typical usage is
      >> binpack = BinaryPacker()
      >> bup.put(UINT32, 12)
      >> bup.put(VAR_INT, 78)
      >> bup.put(BINARY_CHUNK, '\x9f'*10)
      >> ...etc...
      >> result = bup.getBinaryString()
   """
   def __init__(self):
      self.binaryConcat = []

   def getSize(self):
      return sum([len(a) for a in self.binaryConcat])

   def getBinaryString(self):
      return ''.join(self.binaryConcat)

   def __str__(self):
      return self.getBinaryString()
      

   def put(self, varType, theData, endianness=LITTLEENDIAN):
      """
      Need to supply the argument type you are put'ing into the stream.
      Values of BINARY_CHUNK will automatically detect the size as necessary
      """
      if   varType == UINT8:
         self.binaryConcat += int_to_binary(theData, 1, endianness)
      elif varType == UINT16:
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
         raise PackerError, "Var type not recognized!  VarType="+str(varType)

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
   """
   This is the underlying ECDSA code for all Bitcoin signature/verification
   methods.  These are really only called by PyBtcAddress objects, which act
   as wrappers around the lisecdsa objects

   Based on the ECDSA code posted by Lis on the Bitcoin forums: 
   http://forum.bitcoin.org/index.php?topic=23241.0

   NOTE:  these methods are *very* slow in a relative sense.  I believe an
          "average" computer can do 500 ECDSA signatures/verifications per
          second, when done in efficient C++/ASM code.  Using the python
          code below, we achieve about 4/sec.  This is fine for regular
          users who won't be verifying the entire blockchain, but not a 
          good solution for more heavy-weight applications.
   """
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
            raise ECDSA_Error, "Generator point must have order."
         if not n * point == INFINITY:
            raise ECDSA_Error, "Generator point order is bad."
         if point.x() < 0 or n <= point.x() or point.y() < 0 or n <= point.y():
            raise ECDSA_Error, "Generator point has x or y out of range."
   
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
         if r == 0: raise ECDSA_Error, "amazingly unlucky random number r"
         s = ( lisecdsa.inverse_mod( k, n ) * \
                  ( hash + ( self.secret_multiplier * r ) % n ) ) % n
         if s == 0: raise ECDSA_Error, "amazingly unlucky random number s"
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
   """ This method can be used to determine if a Public key is valid """
   return EC_Curve.contains_point(x,y)


# We can identify an address string by its first byte upon conversion
# back to binary.  Return -1 if checksum doesn't match
def checkAddrType(addrBin):
   """ Gets the network byte of the address.  Returns -1 if chksum fails """
   first21, chk4 = addrBin[:-4], addrBin[-4:]
   chkBytes = hash256(first21)
   if chkBytes[:4] == chk4:
      return addrBin[0]
   else:
      return -1

# Check validity of a BTC address in its binary form, as would
# be found inside a pkScript.  Usually about 24 bytes
def checkAddrBinValid(addrBin, netbyte=ADDRBYTE):
   """ 
   Checks whether this address is valid for the given network
   (set at the top of pybtcengine.py)
   """
   return checkAddrType(addrBin) == netbyte

# Check validity of a BTC address in Base58 form
def checkAddrStrValid(addrStr):
   """ Check that a Base58 address-string is valid on this network """
   return checkAddrBinValid(base58_to_binary(addrStr))



class PyBtcAddress(object):
   """
   PyBtcAddress --

   Encapsulate an address, regardless of whether it includes the 
   private key or just an address we've seen on the network.

   Having the privateKey is the most data.  Public key is next
   Finally, you frequently just have someone's address, without
   even having their public key. 
   
   The "createFrom" methods actually calculate the data below it
   The serialize/unserialize methods do no extra calculation, or
   consistency checks, because the lisecdsa library is slow, and 
   we don't want to spend the time verifying thousands of keypairs
   if we've precomputed them before.
   """
   def __init__(self):
      self.privKeyInt = UNINITIALIZED
      self.pubKeyXInt = UNINITIALIZED
      self.pubKeyYInt = UNINITIALIZED
      self.addrStr    = UNINITIALIZED 
      self.lisPubKey  = UNINITIALIZED  # the underlying ECDSA objects from Lis
      self.lisPrivKey = UNINITIALIZED  # the underlying ECDSA objects from Lis

   def hasPrivKey(self):
      return ((not self.privKeyInt == UNINITIALIZED))

   def hasPubKey(self):
      return ((not self.pubKeyXInt == UNINITIALIZED) and \
              (not self.pubKeyYInt == UNINITIALIZED))

   def isInitialized(self):
      return not (self.addrStr    == UNINITIALIZED and\
                  self.privKeyInt == UNINITIALIZED and\
                  self.pubKeyXInt == UNINITIALIZED and\
                  self.pubKeyYInt == UNINITIALIZED     )

   def generateNew(self):
      """
      Generates a new PyBtcAddress by using python's "random" module.  This 
      may not be the most reliable PRNG (especially in python <=2.3), but is
      perfectly sufficient for experimental purposes.

      If the user wishes to supply his own entropy, he may provide 32 bytes
      of random binary data in the following manner:

         pkRandInt = ExternalGenRandomInteger(0, EC_Order)
         newAddr = PyBtcAddress().createFromPrivateKey(pkRandInt

      Or if the entropy is in binary:

         pkRandInt = binary_to_int(ExternalGenRandomBytes)
         newAddr = PyBtcAddress().createFromPrivateKey(pkRandInt
      """
      self.createFromPrivateKey(random.randrange(EC_Order))
      return self

   def createFromPrivateKey(self, privKey):
      """ 
      Creates address from a user-supplied random INTEGER.  
      This method DOES perform elliptic-curve operations to 
      calculate the public key, which may be 0.1 to 1 sec
      depending on your hardware
      """
      if isinstance(privKey, str) and len(privKey)==32:
         self.privKeyInt = binary_to_int(privKey)
      elif isinstance(privKey, int) or isinstance(privKey, long):
         self.privKeyInt = privKey
      else:
         raise BadAddressError, 'Private Key format unknown'
      pubKeyPoint  = EC_GenPt * self.privKeyInt
      self.pubKeyXInt = pubKeyPoint.x()
      self.pubKeyYInt = pubKeyPoint.y()
      self.lisPubKey  = lisecdsa.Public_key(EC_GenPt, pubKeyPoint)
      self.lisPrivKey = lisecdsa.Private_key(self.lisPubKey, self.privKeyInt)
      self.addrStr = self.calculateAddrStr()
      return self

   def createFromPublicKey(self, pubkey):
      """ 
      Creates address from a user-supplied ECDSA public key.

      The key can be supplied as an (x,y) pair of integers, an EC_Point
      as defined in the lisecdsa class, or as a 65-byte binary string
      (the 64 public key bytes with a 0x04 prefix byte)

      This method will fail if the supplied pair of points is not
      on the secp256k1 curve.
      """
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
         if leadByte != 4:
            raise BadAddressError, 'Invalid leading byte on Public key'
      # If "contains_point" error... the supplied XY-coords are not
      # on the secp256k1 elliptic curve
      pubKeyPoint = EC_Point(EC_Curve, self.pubKeyXInt, self.pubKeyYInt)
      self.lisPubKey  = lisecdsa.Public_key(EC_GenPt, pubKeyPoint)
      self.addrStr = self.calculateAddrStr()
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
      chkSum  = hash256(netbyte + pubkeyHash160)[:4]
      self.addrStr = binary_to_base58( netbyte + pubkeyHash160 + chkSum)
      return self

   def createFromKeyData(self, privKeyStr, pubKeyStr, verifyMatch=True):
      """
      Generally, when we read in a wallet from file, we get both a private
      key and public key at the same time.  Here we can plug them both in
      and skip cryptographic-match verification if we expect this to be 
      slow.  If it is skipped here, you should call "prepareKeys" before
      using these keys for anything, which will do the verification.
      """
      if not verifyMatch:
         self.privKeyInt = binary_to_int(privKeyStr)
         self.pubKeyXInt = binary_to_int(pubKeyStr[1:33 ], BIGENDIAN)
         self.pubKeyYInt = binary_to_int(pubKeyStr[  33:], BIGENDIAN)
      else:
         self.createFromPrivateKey(privKeyStr)
         if not self.pubKey_serialize == pubKeyStr:
            raise BadAddressError, 'Supplied Priv/Pub keypair do not match!'
      return self

   def createFromAddrStr(self, addrStr):
      """
      Creates an address from a Base58 address string.  Since the address 
      string includes a checksum, this method will fail if there was any
      errors entering/copying the address
      """
      self.addrStr = addrStr
      if not self.checkAddressValid():
         raise BadAddressError, 'Invalid address string: '+addrStr
      return self

   def calculateAddrStr(self, netbyte=ADDRBYTE):
      """
      Forces a recalculation of the address string from the public key
      """
      if not self.hasPubKey():
         raise BadAddressError, 'Cannot compute address string without PublicKey'
      keyHash = self.getAddr160()
      chkSum  = hash256(netbyte + keyHash)[:4]
      return  binary_to_base58(netbyte + keyHash + chkSum)

   def getAddrStr(self):
      """
      Gets the current address string, calculates it if not available
      """
      if self.addrStr==UNINITIALIZED:
         return self.calculateAddrStr()
      return self.addrStr

   def generateDERSignature(self, binToSign, extraEntropy=None):
      """
      Applies ECDSA magic to sign a message with the private key.
      This method fails if this address doesn't contain a private
      key.  The input argument should be the hash of the message 
      you are signing.  Returns a DER-encoded siganture, (r,s)

      This method relies on a random number, and using the same
      random number on two different signatures is FATAL:  an
      attacker can VERY QUICKLY compute your private key.

      Optionally, you can provide your own random number 
      """
      if not self.hasPrivKey():
         raise BadAddressError, 'Cannot execute ECDSA signature without private key!'
      self.prepareKeys()
      intSign = binary_to_int(binToSign)
      if extraEntropy:
         if isinstance(extraEntropy, int) and extraEntropy>2**250:
            sig = self.lisPrivKey.sign(intSign, extraEntropy)
         elif len(extraEntropy) >= 30:
            sig = self.lisPrivKey.sign(intSign, binary_to_int(extraEntropy))
         else:
            print "***WARNING: extra entropy provided to ECDSA signing function"
            print "            did not contain enough entropy.  Defaulting to "
            print "            using python's random number generator..."
            sig = self.lisPrivKey.sign(intSign, random.randrange(EC_Order))
      else:
         sig = self.lisPrivKey.sign(intSign, random.randrange(EC_Order))
      # The extra 0x00 bytes are to guarantee the r-s values are 
      # interpretted as unsigned integers:  it's a DER-thing
      rBin   = '\x00' + int_to_binary(sig.r, endOut=BIGENDIAN)
      sBin   = '\x00' + int_to_binary(sig.s, endOut=BIGENDIAN)
      rSize  = int_to_binary(len(rBin))
      sSize  = int_to_binary(len(sBin))
      rsSize = int_to_binary(len(rBin) + len(sBin) + 4)
      sigScr = '\x30' + rsSize + \
               '\x02' + rSize + rBin + \
               '\x02' + sSize + sBin
       
      return sigScr



   def verifyDERSignature(self, binToVerify, derToVerify):
      """
      Applies ECDSA magic to verify a message using a PUBLIC key.
      """
      if not self.hasPubKey():
         raise BadAddressError, 'Cannot verify ECDSA signature without public key!'
      self.prepareKeys()
      codeByte = derToVerify[0]
      nBytes   = binary_to_int(derToVerify[1])
      rsStr    = derToVerify[2:2+nBytes]
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
      """ 
      We may have the key data, but may not have created the underlying 
      lisecdsa objects.  Additionally, we may have skipped checking whether
      the keypair matches, due to computational restraints (if we're reading
      in a large wallet).  However, we DO want to check that they match
      before we use these keys for anything, so we will call this method first.
      """
      if self.hasPubKey() and self.lisPubKey==UNINITIALIZED:
         pubKeyPoint     = EC_Point(EC_Curve, self.pubKeyXInt, self.pubKeyYInt)
         self.lisPubKey  = lisecdsa.Public_key(EC_GenPt, pubKeyPoint)

      if self.hasPrivKey() and self.lisPrivKey==UNINITIALIZED:
         self.lisPrivKey = lisecdsa.Private_key(self.lisPubKey, self.privKeyInt)

      # If we already had both a public and private key, we might consider
      # checking that they are a match
      if self.hasPubKey() and self.hasPrivKey() and checkKeyMatch:
         if not self.checkPubPrivKeyPairMatch():
            raise BadAddressError, 'Private key and public key do not match!'


   def checkAddressValid(self):
      return checkAddrStrValid(self.addrStr);

   def checkPubPrivKeyPairMatch(self):
      """ Verify that the stored public and private keys match """
      assert( self.hasPubKey() and self.hasPrivKey() )
      privToPubPoint = EC_GenPt * self.privKeyInt
      xMatches = (privToPubPoint.x() == self.pubKeyXInt)
      yMatches = (privToPubPoint.y() == self.pubKeyYInt)
      return (xMatches and yMatches)

   def getAddr160(self):
      if self.hasPubKey():
         return hash160(self.pubKey_serialize())
      elif not self.addrStr == UNINITIALIZED:
         return addrStr_to_hash160(self.addrStr);
      else:
         return '' 
   
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
      addrLen      = addrData.get(UINT8)
      self.addrStr = addrDate.get(BINARY_CHUNK, addrLen)
   

   def pubKey_serialize(self):
      if not self.hasPubKey():
         return '\x00'
      else:
         xBinBE = int_to_binary(self.pubKeyXInt, widthBytes=32, endOut=BIGENDIAN)
         yBinBE = int_to_binary(self.pubKeyYInt, widthBytes=32, endOut=BIGENDIAN)
         return  '\x04' + xBinBE + yBinBE

   def pubKey_unserialize(self, toUnpack):
      # Does not recompute addrStr
      if isinstance(toUnpack, BinaryUnpacker):
         keyData = toUnpack
      else:
         keyData = BinaryUnpacker(toUnpack)

      leadByte = keyData.get(UINT8)
      if leadByte==0:
         self.pubKeyXInt == UNINITIALIZED
         self.pubKeyYInt == UNINITIALIZED
      else:
         leadByte = keyData.get(UINT8)
         assert(leadByte == 4)
         self.pubKeyXInt = binary_to_int(keyData.get(BINARY_CHUNK, 32), BIGENDIAN)
         self.pubKeyYInt = binary_to_int(keyData.get(BINARY_CHUNK, 32), BIGENDIAN)


   def privKey_serialize(self):
      if not self.hasPrivKey():
         return '\x00'
      else:
         privKeyBin = '\x80' + int_to_binary(self.privKeyInt, widthBytes=32, endOut=BIGENDIAN)
         return privKeyBin
   def privKey_unserialize(self, toUnpack):
      # Does not recompute public key and addr -- run consistency check
      if isinstance(toUnpack, BinaryUnpacker):
         keyData = toUnpack
      else:
         keyData = BinaryUnpacker(toUnpack)
      leadByte = keyData.get(UINT8)
      if leadByte==0:
         self.privKeyInt = UNINITIALIZED
      else:
         privKeyBin = keyData.get(BINARY_CHUNK, 32)
         self.privKeyInt = binary_to_int(privKeyBin, BIGENDIAN)

   
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
         print self.addrStr, '(BinaryLE=%s)' % binary_to_hex(self.getAddr160())
         print '  Have Public Key: ', self.hasPubKey()
         print '  Have Private Key:', self.hasPrivKey()
         if self.hasPubKey():
            print '  Public Key Hex (Big-Endian):  '
            print '     04', int_to_hex(self.pubKeyXInt, 32, BIGENDIAN)
            print '       ', int_to_hex(self.pubKeyYInt, 32, BIGENDIAN)
         if withPrivKey and self.hasPrivKey():
            print '  Private Key Hex (Big-Endian): '
            print '       ', int_to_hex(self.privKeyInt, 32, BIGENDIAN)
      


      
            

TXOUT_SCRIPT_STANDARD      = 0
TXOUT_SCRIPT_COINBASE      = 1
TXOUT_SCRIPT_MULTISIG      = 2
TXOUT_SCRIPT_MULTISIG_1OF2 = 3
TXOUT_SCRIPT_MULTISIG_2OF2 = 4
TXOUT_SCRIPT_MULTISIG_1OF3 = 5
TXOUT_SCRIPT_MULTISIG_2OF3 = 6
TXOUT_SCRIPT_MULTISIG_3OF3 = 7
TXOUT_SCRIPT_OP_EVAL       = 8
TXOUT_SCRIPT_UNKNOWN       = 9

TXIN_SCRIPT_STANDARD = 0
TXIN_SCRIPT_COINBASE = 1
TXIN_SCRIPT_SPENDCB  = 2
TXIN_SCRIPT_UNKNOWN  = 3  

################################################################################
def getTxOutScriptType(binScript):
   if binScript[:2] == hex_to_binary('4104'):
      is65B = len(binScript) == 67
      lastByteMatch = binScript[-1] == int_to_binary(172)
      if (is65B and lastByteMatch):
         return TXOUT_SCRIPT_COINBASE
   else:
      is1 = binScript[ 0] == int_to_binary(118)
      is2 = binScript[ 1] == int_to_binary(169)
      is3 = binScript[-2] == int_to_binary(136)
      is4 = binScript[-1] == int_to_binary(172)
      if (is1 and is2 and is3 and is4):
         return TXOUT_SCRIPT_STANDARD
   return TXOUT_SCRIPT_UNKNOWN

################################################################################
def TxOutScriptExtractAddrStr(binScript):
   txoutType = getTxOutScriptType(binScript)
   if txoutType == TXOUT_SCRIPT_UNKNOWN:
      return '<Non-standard TxOut script>'

   if txoutType == TXOUT_SCRIPT_COINBASE:
      newAddr = PyBtcAddress().createFromPublicKey(binScript[1:66])
      return newAddr.calculateAddrStr()
   elif txoutType == TXOUT_SCRIPT_STANDARD:
      newAddr = PyBtcAddress().createFromPublicKeyHash160(binScript[3:23])
      return newAddr.getAddrStr()

################################################################################
def TxOutScriptExtractAddr160(binScript):
   return addrStr_to_hash160(TxOutScriptExtractAddrStr(binScript))

################################################################################
def getTxInScriptType(txinObj):
   """
   NOTE: this method takes a TXIN object, not just the script itself.  This 
         is because this method needs to see the OutPoint to distinguish an
         UNKNOWN TxIn from a coinbase-TxIn
   """ 
   binScript = txinObj.binScript
   if txinObj.outpoint.txHash == EmptyHash or len(binScript) < 1:
      return TXIN_SCRIPT_COINBASE

   b0,b1,b2,b3,b4 = binScript[:5]
   if not (b1=='\x03' and b3=='\x02'):
      return TXIN_SCRIPT_UNKNOWN

   SigSize = binary_to_int(b2) + 3
   PubkeySize = 66  # 0x4104[Pubx][Puby]

   if len(binScript)==SigSize:
      return TXIN_SCRIPT_SPENDCB
   elif len(binScript)==(SigSize + PubkeySize):
      return TXIN_SCRIPT_STANDARD
   
   return TXIN_SCRIPT_UNKNOWN

   
################################################################################
def TxInScriptExtractKeyAddr(txinObj):
   scrType = getTxInScriptType(txinObj)
   if scrType == TXIN_SCRIPT_STANDARD:
      pubKeyBin = txinObj.binScript[-65:] 
      newAddr = PyBtcAddress().createFromPublicKey(pubKeyBin)
      return (newAddr.calculateAddrStr(), newAddr.pubKey_serialize) # LITTLE_ENDIAN
   elif scrType == TXIN_SCRIPT_COINBASE:
      return ('[COINBASE-NO-ADDR: %s]'%binary_to_hex(txinObj.binScript), '[COINBASE-NO-PUBKEY]')
      #return ('[COINBASE-NO-ADDR]', '[COINBASE-NO-PUBKEY]')
   elif scrType == TXIN_SCRIPT_SPENDCB:
      return ('[SPENDCOINBASE]', '[SPENDCOINBASE]')
   else:
      return ('[UNKNOWN-TXIN]', '[UNKNOWN-TXIN]')


def multiSigExtractAddr160List(binScript):
   """ 
   This naively searches the script for all the addresses/public keys,
   returns a list of the addresses.  Could easily be modified to pass
   out public keys if they are in the script

   This method should work for ALL scripts, actually, not just multisig
   scripts.  For future simplicity, I might consider removing the 
   TxOutScriptExtractAddrStr() and TxInScriptExtractKeyAddr() and use
   this method for every script, instead.
   """
   addr160List = []
   bup = BinaryUnpacker(binScript)
   while bup.getRemainingSize() > 0:
      nextByte = bup.get(UINT8)
      binChunk = ''
      if 0 < nextByte < 76: 
         nBytes = nextByte
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA1: 
         nBytes = scriptUnpacker.get(UINT8)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA2: 
         nBytes = scriptUnpacker.get(UINT16)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA4:
         nBytes = scriptUnpacker.get(UINT32)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      else:
         pass
   
      if len(binChunk) == 20:
         addr160List.append(binChunk)
      elif len(binChunk) == 65:
         newAddr = PyBtcAddress().createFromPublicKey(binChunk)
         addr160List.append(newAddr.getAddr160())

   return addr160List
   

# Finally done with all the base conversion functions and ECDSA code
# Now define the classes for the objects that will use this


################################################################################
#  Transaction Classes
################################################################################

indent = ' '*3

#####
class PyOutPoint(object):
   #def __init__(self, txHash, txOutIndex):
      #self.txHash = txHash
      #self.txOutIndex     = outIndex

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         opData = toUnpack 
      else: 
         opData = BinaryUnpacker( toUnpack )

      if opData.getRemainingSize() < 36: raise UnserializeError
      self.txHash = opData.get(BINARY_CHUNK, 32)
      self.txOutIndex     = opData.get(UINT32)
      return self

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.txHash)
      binOut.put(UINT32, self.txOutIndex)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'OutPoint:'
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.txHash, endian), \
                  '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'TxOutIndex:', self.txOutIndex
      

#####
class PyTxIn(object):
   def __init__(self):
      self.outpoint   = UNINITIALIZED
      self.binScript  = UNINITIALIZED
      self.intSeq     = 2**32-1
      self.isCoinbase = UNKNOWN

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txInData = toUnpack 
      else: 
         txInData = BinaryUnpacker( toUnpack )

      self.outpoint  = PyOutPoint().unserialize( txInData.get(BINARY_CHUNK, 36) ) 
      scriptSize     = txInData.get(VAR_INT)
      if txInData.getRemainingSize() < scriptSize+4: raise UnserializeError
      self.binScript = txInData.get(BINARY_CHUNK, scriptSize)
      self.intSeq    = txInData.get(UINT32)
      return self

   def getScript(self):
      return self.binScript

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.outpoint.serialize() )
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      binOut.put(UINT32, self.intSeq)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'PyTxIn:'
      #self.outpoint.pprint(nIndent+1)
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.outpoint.txHash, endian), \
                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'TxOutIndex:', self.outpoint.txOutIndex
      source = TxInScriptExtractKeyAddr(self)[0]
      print indstr + indent + 'Script:    ', \
                  '('+binary_to_hex(self.binScript)[:32]+'...)'
      print indstr + indent + 'Seq:       ', self.intSeq
      

#####
class PyTxOut(object):
   def __init__(self):
      self.value     = UNINITIALIZED
      self.binScript = UNINITIALIZED

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txOutData = toUnpack 
      else: 
         txOutData = BinaryUnpacker( toUnpack )

      self.value       = txOutData.get(UINT64)
      scriptSize       = txOutData.get(VAR_INT) 
      if txOutData.getRemainingSize() < scriptSize: raise UnserializeError
      self.binScript = txOutData.get(BINARY_CHUNK, scriptSize)
      return self

   def getScript(self):
      return self.binScript

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT64, self.value)
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'TxOut:'
      print indstr + indent + 'Value:   ', self.value, '(', float(self.value) / COIN, ')'
      txoutType = getTxOutScriptType(self.binScript)
      if txoutType == TXOUT_SCRIPT_COINBASE:
         print indstr + indent + 'Script:   PubKey(%s) OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript),)
      elif txoutType == TXOUT_SCRIPT_STANDARD:
         print indstr + indent + 'Script:   OP_DUP OP_HASH (%s) OP_EQUAL OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript),)
      else:
         print indstr + indent + 'Script:   <Non-standard script!>'

#####
class PyTx(object):
   def __init__(self):
      self.version    = UNINITIALIZED
      self.inputs     = UNINITIALIZED
      self.outputs    = UNINITIALIZED
      self.lockTime   = 0
      self.thisHash   = UNINITIALIZED
      self.isSigned   = False

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT32, self.version)
      binOut.put(VAR_INT, len(self.inputs))
      for txin in self.inputs:
         binOut.put(BINARY_CHUNK, txin.serialize())
      binOut.put(VAR_INT, len(self.outputs))
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
      numInputs  = txData.get(VAR_INT)
      for i in xrange(numInputs):
         self.inputs.append( PyTxIn().unserialize(txData) )
      numOutputs = txData.get(VAR_INT)
      for i in xrange(numOutputs):
         self.outputs.append( PyTxOut().unserialize(txData) )
      self.lockTime   = txData.get(UINT32)
      endPos = txData.getPosition()
      self.nBytes = endPos - startPos
      self.thisHash = hash256(self.serialize())
      return self

   def getHash(self):
      if self.thisHash == UNINITIALIZED:
         self.thisHash = hash256(self.serialize())
      return self.thisHash
      
   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'Transaction:'
      print indstr + indent + 'TxHash:   ', binary_to_hex(self.getHash(), endian), \
                                    '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'Version:  ', self.version
      print indstr + indent + 'nInputs:  ', len(self.inputs)
      print indstr + indent + 'nOutputs: ', len(self.outputs)
      print indstr + indent + 'LockTime: ', self.lockTime
      print indstr + indent + 'Inputs: '
      for inp in self.inputs:
         inp.pprint(nIndent+2, endian=endian)
      print indstr + indent + 'Outputs: '
      for out in self.outputs:
         out.pprint(nIndent+2, endian=endian)

      
   def pprintHex(self, nIndent=0):
      bu = BinaryUnpacker(self.serialize())
      theSer = self.serialize()
      print binary_to_hex(bu.get(BINARY_CHUNK, 4))
      nTxin = bu.get(VAR_INT)
      print 'VAR_INT(%d)' % nTxin
      for i in range(nTxin):
         print binary_to_hex(bu.get(BINARY_CHUNK,32))
         print binary_to_hex(bu.get(BINARY_CHUNK,4))
         scriptSz = bu.get(VAR_INT)
         print 'VAR_IN(%d)' % scriptSz
         print binary_to_hex(bu.get(BINARY_CHUNK,scriptSz))
         print binary_to_hex(bu.get(BINARY_CHUNK,4))
      nTxout = bu.get(VAR_INT)
      print 'VAR_INT(%d)' % nTxout
      for i in range(nTxout):
         print binary_to_hex(bu.get(BINARY_CHUNK,8))
         scriptSz = bu.get(VAR_INT)
         print binary_to_hex(bu.get(BINARY_CHUNK,scriptSz))
      print binary_to_hex(bu.get(BINARY_CHUNK, 4))
         
      


################################################################################
#  Block Information
################################################################################


class PyBlockHeader(object):
   def __init__(self):
      self.version      = 1
      self.prevBlkHash  = ''
      self.merkleRoot   = UNINITIALIZED 
      self.timestamp    = UNINITIALIZED 
      self.diffBits     = UNINITIALIZED 
      self.nonce        = UNINITIALIZED 
      # Use these fields for storage of block information, but are not otherwise
      # part of the serialized data structure
      self.theHash      = ''
      self.numTx        = UNINITIALIZED 
      self.blkHeight    = UNINITIALIZED 
      self.fileByteLoc  = UNINITIALIZED 
      self.nextBlkHash  = UNINITIALIZED 
      self.intDifficult = UNINITIALIZED 
      self.sumDifficult = UNINITIALIZED 
      self.isMainChain  = False  
      self.isOrphan     = True  

   def serialize(self):
      if self.version == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
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


   def getHash(self, endian=LITTLEENDIAN):
      if self.version == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
      if len(self.theHash) < 32:
         self.theHash = hash256(self.serialize())
      outHash = self.theHash 
      if endian==BIGENDIAN: 
         outHash = binary_switchEndian(outHash)
      return outHash

   def getHashHex(self, endian=LITTLEENDIAN):
      if self.version == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
      if len(self.theHash) < 32:
         self.theHash = hash256(self.serialize())
      return binary_to_hex(self.theHash, endian)

   def getDifficulty(self):
      if self.diffBits == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
      self.intDifficult = binaryBits_to_difficulty(self.diffBits)
      return self.intDifficult

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'BlockHeader:'
      print indstr + indent + 'Hash:      ', binary_to_hex( self.theHash, endOut=endian), \
                                                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'Version:   ', self.version     
      print indstr + indent + 'PrevBlock: ', binary_to_hex(self.prevBlkHash, endOut=endian), \
                                                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'MerkRoot:  ', binary_to_hex(self.merkleRoot, endOut=endian), \
                                                      '(BE)' if endian==BIGENDIAN else '(LE)'
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


################################################################################
################################################################################
class PyBlockData(object):
   def __init__(self, txList=[]):
      self.txList     = txList
      self.numTx      = len(txList)
      self.merkleTree = []
      self.merkleRoot = UNINITIALIZED
      

   def serialize(self):
      if self.numTx == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockData object not initialized!'
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
      for i in xrange(self.numTx):
         self.txList.append( PyTx().unserialize(blkData) )
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
         

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'BlockData:'
      print indstr + indent + 'MerkleRoot:  ', binary_to_hex(self.getMerkleRoot(), endian), \
                                               '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'NumTx:       ', self.numTx
      for tx in self.txList:
         tx.pprint(nIndent+1, endian=endian)
      

################################################################################
################################################################################
class PyBlock(object):
   def __init__(self, prevHeader=None, txlist=[]):
      self.blockHeader = PyBlockHeader()
      self.blockData   = PyBlockData()
      if prevHeader:
         self.setPrevHeader(prevHeader)
      if txlist:
         self.setTxList(txlist)

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
      self.blockHeader = PyBlockHeader().unserialize(blkData)
      self.blockData   = PyBlockData().unserialize(blkData)
      return self

   def getNumTx(self):
      return len(self.blockData.txList)

   def getSize(self):
      return len(self.serialize())

   # Not sure how useful these manual block-construction methods
   # are.  For now, I just need something with non-ridiculous vals
   def setPrevHeader(self, prevHeader, copyAttr=True):
      self.blockHeader.prevBlkHash = prevHeader.theHash
      self.blockHeader.nonce       = 0
      if copyAttr:
         self.blockHeader.version     = prevHeader.version
         self.blockHeader.timestamp   = prevHeader.timestamp+600
         self.blockHeader.diffBits    = prevHeader.diffBits

   def setTxList(self, txlist):
      self.blockData = PyBlockData(txlist)
      if not self.blockHeader == UNINITIALIZED:
         self.blockHeader.merkleRoot = self.blockData.getMerkleRoot()

   def tx(self, idx):
      return self.blockData.txList[idx]

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'Block:'
      self.blockHeader.pprint(nIndent+1, endian=endian)
      self.blockData.pprint(nIndent+1, endian=endian)






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
OP_2 = 82
OP_3 = 83
OP_4 = 84
OP_5 = 85
OP_6 = 86
OP_7 = 87
OP_8 = 88
OP_9 = 89
OP_10 = 90
OP_11 = 91
OP_12 = 92
OP_13 = 93
OP_14 = 94
OP_15 = 95
OP_16 = 96
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

opnames = ['']*256
opnames[0] =   'OP_0'
for i in range(1,76):
   opnames[i] ='OP_PUSHDATA'
opnames[76] =	'OP_PUSHDATA1'
opnames[77] =	'OP_PUSHDATA2'
opnames[78] =	'OP_PUSHDATA4'
opnames[79] =	'OP_1NEGATE'
opnames[81] =  'OP_1'
opnames[81] =	'OP_TRUE'
for i in range(1,17):
   opnames[80+i] = 'OP_' + str(i)
opnames[97] =	'OP_NOP'
opnames[99] =	'OP_IF'
opnames[100] =	'OP_NOTIF'
opnames[103] = 'OP_ELSE'
opnames[104] = 'OP_ENDIF'
opnames[105] =	'OP_VERIFY'
opnames[106] = 'OP_RETURN'
opnames[107] =	'OP_TOALTSTACK'
opnames[108] =	'OP_FROMALTSTACK'
opnames[115] =	'OP_IFDUP'
opnames[116] =	'OP_DEPTH'
opnames[117] =	'OP_DROP'
opnames[118] =	'OP_DUP'
opnames[119] =	'OP_NIP'
opnames[120] =	'OP_OVER'
opnames[121] =	'OP_PICK'
opnames[122] =	'OP_ROLL'
opnames[123] =	'OP_ROT'
opnames[124] =	'OP_SWAP'
opnames[125] =	'OP_TUCK'
opnames[109] =	'OP_2DROP'
opnames[110] =	'OP_2DUP'
opnames[111] =	'OP_3DUP'
opnames[112] =	'OP_2OVER'
opnames[113] =	'OP_2ROT'
opnames[114] =	'OP_2SWAP'
opnames[126] =	'OP_CAT'
opnames[127] = 'OP_SUBSTR'
opnames[128] =	'OP_LEFT'
opnames[129] =	'OP_RIGHT'
opnames[130] =	'OP_SIZE'
opnames[131] =	'OP_INVERT'
opnames[132] =	'OP_AND'
opnames[133] =	'OP_OR'
opnames[134] = 'OP_XOR'
opnames[135] = 'OP_EQUAL'
opnames[136] =	'OP_EQUALVERIFY'
opnames[139] =	'OP_1ADD'
opnames[140] =	'OP_1SUB'
opnames[141] =	'OP_2MUL'
opnames[142] =	'OP_2DIV'
opnames[143] =	'OP_NEGATE'
opnames[144] =	'OP_ABS'
opnames[145] =	'OP_NOT'
opnames[146] =	'OP_0NOTEQUAL'
opnames[147] =	'OP_ADD'
opnames[148] =	'OP_SUB'
opnames[149] =	'OP_MUL'
opnames[150] =	'OP_DIV'
opnames[151] =	'OP_MOD'
opnames[152] =	'OP_LSHIFT'
opnames[153] =	'OP_RSHIFT'
opnames[154] =	'OP_BOOLAND'
opnames[155] =	'OP_BOOLOR'
opnames[156] =	'OP_NUMEQUAL'
opnames[157] =	'OP_NUMEQUALVERIFY'
opnames[158] =	'OP_NUMNOTEQUAL'
opnames[159] =	'OP_LESSTHAN'
opnames[160] =	'OP_GREATERTHAN'
opnames[161] =	'OP_LESSTHANOREQUAL'
opnames[162] = 'OP_GREATERTHANOREQUAL'
opnames[163] =	'OP_MIN'
opnames[164] =	'OP_MAX'
opnames[165] = 'OP_WITHIN'
opnames[166] =	'OP_RIPEMD160'
opnames[167] =	'OP_SHA1'
opnames[168] =	'OP_SHA256'
opnames[169] =	'OP_HASH160'
opnames[170] =	'OP_HASH256'
opnames[171] =	'OP_CODESEPARATOR'
opnames[172] =	'OP_CHECKSIG'
opnames[173] =	'OP_CHECKSIGVERIFY'
opnames[174] =	'OP_CHECKMULTISIG'
opnames[175] =	'OP_CHECKMULTISIGVERIFY'


opCodeLookup = {}
opCodeLookup['OP_FALSE'] = 0  
opCodeLookup['OP_PUSHDATA1'] =	76
opCodeLookup['OP_PUSHDATA2'] =	77
opCodeLookup['OP_PUSHDATA4'] =	78
opCodeLookup['OP_1NEGATE'] =	79
opCodeLookup['OP_1'] =  81
for i in range(1,17):
   opCodeLookup['OP_'+str(i)] =  80+i
opCodeLookup['OP_TRUE'] =	81
opCodeLookup['OP_NOP'] =	97
opCodeLookup['OP_IF'] =	99
opCodeLookup['OP_NOTIF'] =	100
opCodeLookup['OP_ELSE'] = 103
opCodeLookup['OP_ENDIF'] = 104
opCodeLookup['OP_VERIFY'] =	105
opCodeLookup['OP_RETURN'] = 106
opCodeLookup['OP_TOALTSTACK'] =	107
opCodeLookup['OP_FROMALTSTACK'] =	108
opCodeLookup['OP_IFDUP'] =	115
opCodeLookup['OP_DEPTH'] =	116
opCodeLookup['OP_DROP'] =	117
opCodeLookup['OP_DUP'] =	118
opCodeLookup['OP_NIP'] =	119
opCodeLookup['OP_OVER'] =	120
opCodeLookup['OP_PICK'] =	121
opCodeLookup['OP_ROLL'] =	122
opCodeLookup['OP_ROT'] =	123
opCodeLookup['OP_SWAP'] =	124
opCodeLookup['OP_TUCK'] =	125
opCodeLookup['OP_2DROP'] =	109
opCodeLookup['OP_2DUP'] =	110
opCodeLookup['OP_3DUP'] =	111
opCodeLookup['OP_2OVER'] =	112
opCodeLookup['OP_2ROT'] =	113
opCodeLookup['OP_2SWAP'] =	114
opCodeLookup['OP_CAT'] =	126
opCodeLookup['OP_SUBSTR'] = 127
opCodeLookup['OP_LEFT'] =	128
opCodeLookup['OP_RIGHT'] =	129
opCodeLookup['OP_SIZE'] =	130
opCodeLookup['OP_INVERT'] =	131
opCodeLookup['OP_AND'] =	132
opCodeLookup['OP_OR'] =	133
opCodeLookup['OP_XOR'] = 134
opCodeLookup['OP_EQUAL'] = 135
opCodeLookup['OP_EQUALVERIFY'] =	136
opCodeLookup['OP_1ADD'] =	139
opCodeLookup['OP_1SUB'] =	140
opCodeLookup['OP_2MUL'] =	141
opCodeLookup['OP_2DIV'] =	142
opCodeLookup['OP_NEGATE'] =	143
opCodeLookup['OP_ABS'] =	144
opCodeLookup['OP_NOT'] =	145
opCodeLookup['OP_0NOTEQUAL'] =	146
opCodeLookup['OP_ADD'] =	147
opCodeLookup['OP_SUB'] =	148
opCodeLookup['OP_MUL'] =	149
opCodeLookup['OP_DIV'] =	150
opCodeLookup['OP_MOD'] =	151
opCodeLookup['OP_LSHIFT'] =	152
opCodeLookup['OP_RSHIFT'] =	153
opCodeLookup['OP_BOOLAND'] =	154
opCodeLookup['OP_BOOLOR'] =	155
opCodeLookup['OP_NUMEQUAL'] =	156
opCodeLookup['OP_NUMEQUALVERIFY'] =	157
opCodeLookup['OP_NUMNOTEQUAL'] =	158
opCodeLookup['OP_LESSTHAN'] =	159
opCodeLookup['OP_GREATERTHAN'] =	160
opCodeLookup['OP_LESSTHANOREQUAL'] =	161
opCodeLookup['OP_GREATERTHANOREQUAL'] = 162
opCodeLookup['OP_MIN'] =	163
opCodeLookup['OP_MAX'] =	164
opCodeLookup['OP_WITHIN'] = 165
opCodeLookup['OP_RIPEMD160'] =	166
opCodeLookup['OP_SHA1'] =	167
opCodeLookup['OP_SHA256'] =	168
opCodeLookup['OP_HASH160'] =	169
opCodeLookup['OP_HASH256'] =	170
opCodeLookup['OP_CODESEPARATOR'] =	171
opCodeLookup['OP_CHECKSIG'] =	172
opCodeLookup['OP_CHECKSIGVERIFY'] =	173
opCodeLookup['OP_CHECKMULTISIG'] =	174
opCodeLookup['OP_CHECKMULTISIGVERIFY'] =	175
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


def getOpCode(name):
   return int_to_binary(opCodeLookup[name], widthBytes=1)

def convertScriptToOpStrings(binScript):
   opList = []

   i = 0;
   sz = len(binScript)
   error = False;
   while i < sz:
      nextOp = ord(binScript[i]);
      if nextOp == 0:
         opList.append("0")
         i+=1
      elif nextOp < 76:
         opList.append("[PUSHDATA -- " + str(nextOp) + " BYTES:]")
         binObj = binScript[i+1:i+1+nextOp]
         opList.append(binary_to_hex(binObj))
         i += nextOp+1
      elif nextOp == 76:
         nb = binary_to_int(binScript[i+1:i+2])
         if i+1+1+nb > sz: 
            error = True;
            break
         binObj = binScript[i+2:i+2+nb]
         opList.append("[OP_PUSHDATA1 -- " + str(nb) + " BYTES:]");
         opList.append(binary_to_hex(binObj))
         i += nb+2
      elif nextOp == 77:
         nb = binScript[i+1:i+3];
         if i+1+2+nb > sz: 
            error = True;
            break
         nbprint = min(nb,256)
         binObj = binScript[i+3,i+3+nbprint]
         opList.append("[OP_PUSHDATA2 -- " + str(nb) + " BYTES:]");
         opList.append(binary_to_hex(binObj) + '...')
         i += nb+3
      elif nextOp == 78:
         nb = binScript[i+1:i+5];
         if i+1+4+nb > sz: 
            error = True;
            break
         nbprint = min(nb,256)
         binObj = binScript[i+5,i+5+nbprint]
         opList.append("[OP_PUSHDATA4 -- " + str(nb) + " BYTES:]");
         opList.append(binary_to_hex(binObj) + '...')
         i += nb+5
      else:
         opList.append(opnames[nextOp]);
         i += 1

   if error:
      opList.append("ERROR PROCESSING SCRIPT");

   return opList;


def pprintScript(binScript, nIndent=0):
   indstr = indent*nIndent
   print indstr + 'Script:'
   opList = convertScriptToOpStrings(binScript)
   for op in opList:
      print indstr + indent + op



TX_INVALID = 0
OP_NOT_IMPLEMENTED = 1
OP_DISABLED = 2
SCRIPT_STACK_SIZE_ERROR = 3
SCRIPT_ERROR = 4
SCRIPT_NO_ERROR = 5

   
class PyScriptProcessor(object):
   """
   Use this class to evaluate a script.  This method is more complicated
   than some might expect, due to the fact that any OP_CHECKSIG or
   OP_CHECKMULTISIG code requires the full transaction of the TxIn script
   and also needs the TxOut script being spent.  Since nearly every useful
   script will have one of these operations, this class/method assumes
   that all that data will be supplied.

   To simply execute a script not requiring any crypto operations:

      scriptIsValid = PyScriptProcessor().executeScript(binScript)
   """

   def __init__(self, txOldData=None, txNew=None, txInIndex=None):
      self.stack   = []
      self.txNew   = None
      self.script1 = None
      self.script2 = None
      if txOldData and txNew and txInIndex:
         self.setTxObjects(txOldData, txNew, txInIndex)
   

   def setTxObjects(self, txOldData, txNew, txInIndex):
      """
      The minimal amount of data necessary to evaluate a script that
      has an signature check is the TxOut script that is being spent
      and the entire Tx of the TxIn that is spending it.  Thus, we
      must supply at least the txOldScript, and a txNew with its 
      TxIn index (so we know which TxIn is spending that TxOut).  
      It is acceptable to pass in the full TxOut or the tx of the 
      TxOut instead of just the script itself.
      """
      self.txNew = PyTx().unserialize(txNew.serialize())
      self.script1 = txNew.inputs[txInIndex].binScript
      self.txInIndex  = txInIndex
      self.txOutIndex = txNew.inputs[txInIndex].outpoint.txOutIndex
      self.txHash  = txNew.inputs[txInIndex].outpoint.txHash

      if isinstance(txOldData, PyTx):
         if not self.txHash == hash256(txOldData.serialize()):
            print '*** Supplied incorrect pair of transactions!'
         self.script2 = txOldData.outputs[self.txOutIndex].binScript
      elif isinstance(txOldData, PyTxOut):
         self.script2 = txOldData.binScript
      elif isinstance(txOldData, str):
         self.script2 = txOldData



   def verifyTransactionValid(self, txOldData=None, txNew=None, txInIndex=-1):
      if txOldData and txNew and txInIndex != -1:
         self.setTxObjects(txOldData, txNew, txInIndex)

      if self.script1==None or self.txNew==None:
         raise VerifyScriptError, 'Cannot verify transactions, without setTxObjects call first!'

      # Execute TxIn script first
      self.stack = []
      exitCode1 = self.executeScript(self.script1, self.stack) 

      if not exitCode1 == SCRIPT_NO_ERROR:
         raise VerifyScriptError, ('First script failed!  Exit Code: ' + str(exitCode1))

      exitCode2 = self.executeScript(self.script2, self.stack) 

      if not exitCode2 == SCRIPT_NO_ERROR:
         raise VerifyScriptError, ('Second script failed!  Exit Code: ' + str(exitCode2))

      return self.stack[-1]==1


   def executeScript(self, binaryScript, stack=[]):
      self.stack = stack
      self.stackAlt  = []
      scriptData = BinaryUnpacker(binaryScript)
      self.lastOpCodeSepPos = None
   
      while scriptData.getRemainingSize() > 0:
         opcode = scriptData.get(UINT8)
         exitCode = self.executeOpCode(opcode, scriptData, self.stack, self.stackAlt)
         if not exitCode == SCRIPT_NO_ERROR:
            if exitCode==OP_NOT_IMPLEMENTED:
               print '***ERROR: OpCodes OP_IF, OP_NOTIF, OP_ELSE, OP_ENDIF,'
               print '          have not been implemented, yet.  This script'
               print '          could not be evaluated.'
            if exitCode==OP_DISABLED:
               print '***ERROR: This script included an op code that has been'
               print '          disabled for security reasons.  Script eval'
               print '          failed'
            return exitCode

      return SCRIPT_NO_ERROR
      
      
   # Implementing this method exactly as in the client because it looks like
   # there could be some subtleties with how it determines "true"
   def castToBool(self, binData):
      if isinstance(binData, int): 
         binData = int_to_binary(binData)

      for i,byte in enumerate(binData):
         if not ord(byte) == 0:
            # This looks like it's assuming LE encoding (?)
            if (i == len(binData)-1) and (byte==0x80):
               return False
            return True
      return False
         

   def checkSig(self,binSig, binPubKey, txOutScript, txInTx, txInIndex, lastOpCodeSep=None):
      """ 
      Generic method for checking Bitcoin tx signatures.  This needs to be used for both
      OP_CHECKSIG and OP_CHECKMULTISIG.  Step 1 is to pop signature and public key off
      the stack, which must be done outside this method and passed in through the argument
      list.  The remaining steps do not require access to the stack.
      """

      # 2. Subscript is from latest OP_CODESEPARATOR until end... if DNE, use whole script
      subscript = txOutScript
      if lastOpCodeSep:
         subscript = subscript[lastOpCodeSep:]
      
      # 3. Signature is deleted from subscript
      #    I'm not sure why this line is necessary - maybe for non-standard scripts?
      lengthInBinary = int_to_binary(len(binSig))
      subscript = subscript.replace( lengthInBinary + binSig, "")

      # 4. Hashtype is popped and stored
      hashtype = binary_to_int(binSig[-1])
      justSig = binSig[:-1]

      if not hashtype == 1:
         print 'Non-unity hashtypes not implemented yet! ( hashtype =', hashtype,')'
         assert(False)

      # 5. Make a copy of the transaction -- we will be hashing a modified version
      txCopy = PyTx().unserialize( txInTx.serialize() )

      # 6. Remove all OP_CODESEPARATORs
      subscript.replace( int_to_binary(OP_CODESEPARATOR), '')

      # 7. All the TxIn scripts in the copy are blanked (set to empty string)
      for txin in txCopy.inputs:
         txin.binScript = ''

      # 8. Script for the current input in the copy is set to subscript
      txCopy.inputs[txInIndex].binScript = subscript

      # 9. Prepare the signature and public key
      senderAddr = PyBtcAddress().createFromPublicKey(binPubKey)
      binHashCode = int_to_binary(hashtype, widthBytes=4)
      toHash = txCopy.serialize() + binHashCode

      print 'BinToSign:', binary_to_hex(toHash)
      print 'PubKey:', binary_to_hex(senderAddr.pubKey_serialize())
      print 'Sig:', binary_to_hex(justSig)
      hashToVerify = hash256(toHash)
      hashToVerify = binary_switchEndian(hashToVerify)

      # 10. Apply ECDSA signature verification
      if senderAddr.verifyDERSignature(hashToVerify, justSig):
         return True
      else:
         return False
         
      
   

   def executeOpCode(self, opcode, scriptUnpacker, stack, stackAlt):
      """ 
      Executes the next OP_CODE given the current state of the stack(s)
      """

      # TODO: Gavin clarified the effects of OP_0, and OP_1-OP_16.  
      #       OP_0 puts an empty string onto the stack, which evaluateses to 
      #            false and is plugged into HASH160 as ''
      #       OP_X puts a single byte onto the stack, 0x01 to 0x10
      #
      #       I haven't implemented it this way yet, because I'm still missing 
      #       some details.  Since this "works" for available scripts, I'm going
      #       to leave it alone for now.

      ##########################################################################
      ##########################################################################
      ### This block produces very nice debugging output for script eval!
      #def pr(s):
         #if isinstance(s,int):
            #return str(s)
         #elif isinstance(s,str):
            #if len(s)>8:
               #return binary_to_hex(s)[:8]
            #else:
               #return binary_to_hex(s)

      #print '  '.join([pr(i) for i in stack])
      #print opnames[opcode][:12].ljust(12,' ') + ':',
      ##########################################################################
      ##########################################################################


      stackSizeAtLeast = lambda n: (len(self.stack) >= n)

      if   opcode == OP_FALSE:  
         stack.append(0)
      elif 0 < opcode < 76: 
         stack.append(scriptUnpacker.get(BINARY_CHUNK, opcode))
      elif opcode == OP_PUSHDATA1: 
         nBytes = scriptUnpacker.get(UINT8)
         stack.append(scriptUnpacker.get(BINARY_CHUNK, nBytes))
      elif opcode == OP_PUSHDATA2: 
         nBytes = scriptUnpacker.get(UINT16)
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
         if not self.castToBool(stack.pop()):
            stack.append(0)
            return TX_INVALID
      elif opcode == OP_RETURN:
         return TX_INVALID
      elif opcode == OP_TOALTSTACK:
         stackAlt.append( stack.pop() ) 
      elif opcode == OP_FROMALTSTACK:
         stack.append( stackAlt.pop() ) 

      elif opcode == OP_IFDUP:
         # Looks like this method duplicates the top item if it's not zero
         if not stackSizeAtLeast(1): return SCRIPT_STACK_SIZE_ERROR
         if self.castToBool(stack[-1]):
            stack.append(stack[-1]);

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
         stack.append(stack[-(n+1)])
         del stack[-(n+2)]
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
         if isinstance(stack[-1], int):
            stack.append(0)
         else:
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
         top = stack.pop()
         if top==0: 
            stack.append(0)
         else:
            stack.append(1)
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
         stack.append( 1 if (self.castToBool(a) or self.castToBool(b)) else 0 )
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
         if isinstance(bits, int):
            bits = ''
         stack.append( hash160(bits) )
      elif opcode == OP_HASH256:
         bits = stack.pop()
         if isinstance(bits, int):
            bits = ''
         stack.append( sha256(sha256(bits) ) )
      elif opcode == OP_CODESEPARATOR:
         self.lastOpCodeSepPos = scriptUnpacker.getPosition()
      elif opcode == OP_CHECKSIG or opcode == OP_CHECKSIGVERIFY:

         # 1. Pop key and sig from the stack 
         binPubKey = stack.pop()
         binSig    = stack.pop()

         # 2-10. encapsulated in sep method so CheckMultiSig can use it too
         txIsValid = self.checkSig(  binSig, \
                                     binPubKey, \
                                     scriptUnpacker.getBinaryString(), \
                                     self.txNew, \
                                     self.txInIndex, \
                                     self.lastOpCodeSepPos)
         stack.append(1 if txIsValid else 0)
         if opcode==OP_CHECKSIGVERIFY:
            verifyCode = self.executeOpCode(OP_VERIFY)
            if verifyCode == TX_INVALID:
               return TX_INVALID
            
      elif opcode == OP_CHECKMULTISIG or opcode == OP_CHECKMULTISIGVERIFY:
         # OP_CHECKMULTISIG procedure ported directly from Satoshi client code
         # Location:  bitcoin-0.4.0-linux/src/src/script.cpp:775
         i=1
         if len(stack) < i:
            return TX_INVALID

         nKeys = int(stack[-i])
         if nKeys < 0 or nKeys > 20:
            return TX_INVALID

         i += 1
         iKey = i
         i += nKeys
         if len(stack) < i:
            return TX_INVALID

         nSigs = int(stack[-i])
         if nSigs < 0 or nSigs > nKeys:
            return TX_INVALID

         iSig = i
         i += 1
         i += nSigs
         if len(stack) < i:
            return TX_INVALID

         stack.pop()

         # Apply the ECDSA verification to each of the supplied Sig-Key-pairs
         enoughSigsMatch = True
         while enoughSigsMatch and nSigs > 0:
            binSig = stack[-iSig]
            binKey = stack[-iKey]

            if( self.checkSig(binSig, \
                              binKey, \
                              scriptUnpacker.getBinaryString(), \
                              self.txNew, \
                              self.txInIndex, \
                              self.lastOpCodeSepPos) ):
               iSig  += 1
               nSigs -= 1
            
            iKey +=1
            nKeys -=1

            if(nSigs > nKeys):
               enoughSigsMatch = False

         # Now pop the things off the stack, we only accessed in-place before
         while i > 1:
            i -= 1
            stack.pop()


         stack.append(1 if enoughSigsMatch else 0)

         if opcode==OP_CHECKMULTISIGVERIFY:
            verifyCode = self.executeOpCode(OP_VERIFY)
            if verifyCode == TX_INVALID:
               return TX_INVALID

      else:
         return SCRIPT_ERROR

      return SCRIPT_NO_ERROR
      
   
         

################################################################################
# NOTE:  This method was actually used to create the Blockchain-reorg unit-
#        test, and hence why coinbase transactions are supported.  However,
#        for normal transactions supported by PyBtcEngine, this support is
#        unnecessary.  
#
#        Additionally, this method both creates and signs the tx:  however
#        PyBtcEngine employs TxDistProposals which require the construction
#        and signing to be two separate steps.  This method is not suited
#        for most of the PyBtcEngine CONOPS.
#     
#        On the other hand, this method DOES work, and there is no reason
#        not to use it if you already have PyBtcAddress-w-PrivKeys avail
#        and have a list of inputs and outputs as described below.
#
# This method will take an already-selected set of TxOuts, along with 
# PyBtcAddress objects containing necessary the private keys
#
#    Src TxOut ~ {PyBtcAddr, PrevTx, PrevTxOutIdx}  --OR--  COINBASE = -1
#    Dst TxOut ~ {PyBtcAddr, value}
#
# Of course, we usually don't have the private keys of the dst addrs...
#
def PyCreateAndSignTx(srcTxOuts, dstAddrsVals):
   newTx = PyTx()
   newTx.version    = 1
   newTx.lockTime   = 0
   newTx.inputs     = []
   newTx.outputs    = []


   numInputs  = len(srcTxOuts)
   numOutputs = len(dstAddrsVals)

   coinbaseTx = False
   if numInputs==1 and srcTxOuts[0] == -1:
      coinbaseTx = True
      
   
   #############################
   # Fill in TxOuts first
   for i in range(numOutputs):
      txout       = PyTxOut()
      txout.value = dstAddrsVals[i][1]
      dstAddr     = dstAddrsVals[i][0]
      if(coinbaseTx):
         txout.binScript = ''.join([  '\x41',                      \
                                      dstAddr.pubKey_serialize(),  \
                                      getOpCode('OP_CHECKSIG'   )])
      else:
         txout.binScript = ''.join([  getOpCode('OP_DUP'        ), \
                                      getOpCode('OP_HASH160'    ), \
                                      '\x14',                      \
                                      dstAddr.getAddr160(),        \
                                      getOpCode('OP_EQUALVERIFY'), \
                                      getOpCode('OP_CHECKSIG'   )])
      
      newTx.outputs.append(txout)

                                      
   #############################
   # Create temp TxIns with blank scripts
   for i in range(numInputs):
      txin = PyTxIn()
      txin.outpoint = PyOutPoint()
      if(coinbaseTx):
         txin.outpoint.txHash = '\x00'*32
         txin.outpoint.txOutIndex     = binary_to_int('\xff'*4)
      else:
         txin.outpoint.txHash = hash256(srcTxOuts[i][1].serialize())
         txin.outpoint.txOutIndex     = srcTxOuts[i][2]
      txin.binScript = ''
      txin.intSeq = 2**32-1
      newTx.inputs.append(txin)                                      


   #############################
   # Now we apply the ultra-complicated signature procedure
   # We need a copy of the Tx with all the txin scripts blanked out
   txCopySerialized = newTx.serialize()
   for i in range(numInputs):
      if coinbaseTx:
         pass
      else:
         txCopy     = PyTx().unserialize(txCopySerialized)
         srcAddr    = srcTxOuts[i][0]
         txoutIdx   = srcTxOuts[i][2]
         prevTxOut  = srcTxOuts[i][1].outputs[txoutIdx]
         binToSign  = ''

         assert(srcAddr.hasPrivKey())

         # Only implemented one type of hashing:  SIGHASH_ALL
         hashType   = 1  # SIGHASH_ALL
         hashCode1  = int_to_binary(1, widthBytes=1)
         hashCode4  = int_to_binary(1, widthBytes=4)

         # Copy the script of the TxOut we're spending, into the txIn script
         txCopy.inputs[i].binScript = prevTxOut.binScript
         preHashMsg = txCopy.serialize() + hashCode4
         binToSign = hash256(preHashMsg)
         binToSign = binary_switchEndian(binToSign)
         signature = srcAddr.generateDERSignature(binToSign)

         
         # If we are spending a Coinbase-TxOut, only need sig, no pubkey
         # Don't forget to tack on the one-byte hashcode and consider it part of sig
         if len(prevTxOut.binScript) > 30:
            sigLenInBinary = int_to_binary(len(signature) + 1)
            newTx.inputs[i].binScript = sigLenInBinary + signature + hashCode1
         else:
            pubkey = srcAddr.pubKey_serialize()
            sigLenInBinary    = int_to_binary(len(signature) + 1)
            pubkeyLenInBinary = int_to_binary(len(pubkey)   )
            newTx.inputs[i].binScript = sigLenInBinary    + signature + hashCode1 + \
                                        pubkeyLenInBinary + pubkey
      
   #############################
   # Finally, our tx is complete!
   return newTx
   


################################################################################
################################################################################
#
# SelectCoins algorithms
#
#   The following methods define multiple ways that one could select coins 
#   for a given transaction.  However, the "best" solution is extremely 
#   dependent on the variety of unspent outputs, and also the preferences
#   of the user.  Things to take into account when selecting coins:
#
#     - Number of inputs:  If we have a lot of inputs in this transaction
#                          from different addresses, then all those addresses
#                          have now been linked together.  We want to use
#                          as few outputs as possible
#
#     - Tx Fess/Size:      The bigger the transaction, in bytes, the more
#                          fee we're going to have to pay to the miners
#
#     - Priority:          Low-priority transactions might require higher
#                          fees and/or take longer to make it into the
#                          blockchain.  Priority is the sum of TxOut
#                          priorities:  (NumConfirm * NumBTC / SizeKB)
#                          We especially want to avoid 0-confirmation txs
#
#     - Output values:     In almost every transaction, we must return
#                          change to ourselves.  This means there will
#                          be two outputs, one to the recipient, one to 
#                          us.  We prefer that both outputs be about the 
#                          same size, so that it's not clear which is the
#                          recipient, which is the change.  But we don't
#                          want to use too many inputs to do this.
#                          
#     - Sustainability:    We should pick a strategy that tends to leave our
#                          wallet containing a variety of TxOuts that are
#                          well-suited for future transactions to benefit.
#                          For instance, always favoring the single TxOut
#                          with a value close to the target, will result
#                          in a future wallet full of tiny TxOuts.  This 
#                          guarantees that in the future, we're going to 
#                          have to do 10+ inputs for a single Tx.
#           
#
#   The strategy is to execute a half dozen different types of SelectCoins
#   algorithms, each with a different goal in mind.  Then we examine each
#   of the results and evaluate a "select-score."  Use the one with the
#   best score.  In the future, we could make the scoring algorithm based
#   on user preferences.  We expect that depending on what the availble
#   list looks like, some of these algorithms could produce perfect results,
#   and in other instances *terrible* results.
#
################################################################################
################################################################################

################################################################################
# These would normally be defined by C++ and fed in, but I've recreated
# the C++ class here... it's really just a container, anyway
class UnspentTxOut(object):
   def __init__(self, addr='', val=-1, numConf=-1):
      self.addr = addr
      self.val  = long(val*1e8)
      self.conf = numConf
      self.binScript = '\x76\xa9\x14' + self.addr + '\x88\xac'
   def createFromCppUtxo(self, cppUtxo):
      self.addr = cppUtxo.getRecipientAddr()
      self.val  = cppUtxo.getValue()
      self.conf = cppUtxo.getNumConfirm()
      self.binScript = '\x76\xa9\x14' + self.addr + '\x88\xac'
      self.txHash     = cppUtxo.getTxHash()
      self.txOutIndex = cppUtxo.getTxOutIndex()
      return self
   def getValue(self):
      return self.val
   def getNumConfirm(self):
      return self.conf
   def getScript(self):
      return self.binScript
   def getRecipientAddr(self):
      return self.addr
   def prettyStr(self, indent=''):
      pstr = [indent]
      pstr.append(binary_to_hex(self.addr[:8]))
      pstr.append(coin2str(self.val))
      pstr.append(str(self.conf).rjust(8,' '))
      return '  '.join(pstr)
   def pprint(self, indent=''):
      print self.prettyStr(indent)


################################################################################
def sumTxOutList(txoutList):
   return sum([u.getValue() for u in txoutList])

################################################################################
# This is really just for viewing a TxOut list -- usually for debugging
def pprintUnspentTxOutList(utxoList, headerLine='Coin Selection: '):
   totalSum = sum([u.getValue() for u in utxoList])
   print headerLine, '(Total = %s BTC)' % coin2str(totalSum)
   print '   ','Owner Address'.ljust(34),
   print '   ','TxOutValue'.rjust(18),
   print '   ','NumConf'.rjust(8),
   print '   ','PriorityFactor'.rjust(16)
   for utxo in utxoList:
      print '   ',hash160_to_addrStr(utxo.getRecipientAddr()).ljust(34),
      print '   ',(coin2str(utxo.getValue()) + ' BTC').rjust(18),
      print '   ',str(utxo.getNumConfirm()).rjust(8),
      print '   ', ('%0.2f' % (utxo.getValue()*utxo.getNumConfirm()/(COIN*144.))).rjust(16)


################################################################################
# Sorting currently implemented in C++, but we implement a different kind, here
def PySortCoins(unspentTxOutInfo, sortMethod=1):
   """
   Here we define a few different ways to sort a list of unspent TxOut objects.
   Most of them are simple, some are more complex.  In particular, the last
   method (4) tries to be intelligent, by grouping together inputs from the 
   same address.

   The goal is not to do the heavy lifting for SelectCoins... we simply need
   a few different ways to sort coins so that the SelectCoins algorithms has
   a variety of different inputs to play with.  Each sorting method is useful
   for some types of unspent-TxOut lists, so as long as we have one good 
   sort, the PyEvalCoinSelect method will pick it out.

   As a precaution we send all the zero-confirmation UTXO's to the back
   of the list, so that they will only be used if absolutely necessary.  
   """
   zeroConfirm = []

   if sortMethod==0:
      priorityFn = lambda a: a.getValue() * a.getNumConfirm()
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==1:
      priorityFn = lambda a: (a.getValue() * a.getNumConfirm())**(1/3.)
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==2:
      priorityFn = lambda a: (math.log(a.getValue()*a.getNumConfirm()+1)+4)**4
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==3:
      priorityFn = lambda a: a.getValue() if a.getNumConfirm()>0 else 0
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==4:
      addrMap = {}
      zeroConfirm = []
      for utxo in unspentTxOutInfo:
         if utxo.getNumConfirm() == 0:
            zeroConfirm.append(utxo)
         else:
            addr = TxOutScriptExtractAddr160(utxo.getScript())
            if not addrMap.has_key(addr):
               addrMap[addr] = [utxo]
            else:
               addrMap[addr].append(utxo)

      priorityUTXO = (lambda a: (a.getNumConfirm()*a.getValue()**0.333))
      for addr,txoutList in addrMap.iteritems():
         txoutList.sort(key=priorityUTXO, reverse=True)
   
      priorityGrp = lambda a: max([priorityUTXO(utxo) for utxo in a])
      finalSortedList = []
      for utxo in sorted(addrMap.values(), key=priorityGrp, reverse=True):
         finalSortedList.extend(utxo)
   
      finalSortedList.extend(zeroConfirm)
      return finalSortedList
   if sortMethod in (5, 6, 7):
      utxoSorted = PySortCoins(unspentTxOutInfo, 1)
      # Rotate the top 1,2 or 3 elements to the bottom of the list
      for i in range(sortMethod-4):  
         utxoSorted.append(utxoSorted[0])
         del utxoSorted[0]
      return utxoSorted
   
   # TODO:  Add a semi-random sort method:  it will favor putting high-priority
   #        outputs at the front of the list, but will not be deterministic
   #        This should give us some high-fitness variation compared to sorting
   #        uniformly
   if sortMethod==8:
      utxosNoZC = filter(lambda a: a.getNumConfirm()!=0, unspentTxOutInfo)
      random.shuffle(utxosNoZC)
      utxosNoZC.extend(filter(lambda a: a.getNumConfirm()==0, unspentTxOutInfo))
      return utxosNoZC
   if sortMethod==9:
      utxoSorted = PySortCoins(unspentTxOutInfo, 1)
      sz = len(filter(lambda a: a.getNumConfirm()!=0, utxoSorted))
      # swap 1/3 of the values at random
      topsz = int(min(max(round(sz/3), 5), sz))
      for i in range(topsz):
         pick1 = int(random.uniform(0,topsz))
         pick2 = int(random.uniform(0,sz-topsz))
         utxoSorted[pick1], utxoSorted[pick2] = utxoSorted[pick2], utxoSorted[pick1]
      return utxoSorted




################################################################################
# Now we try half a dozen different selection algorithms
################################################################################



################################################################################
def PySelectCoins_SingleInput_SingleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   This method should usually be called with a small number added to target val
   so that a tx can be constructed that has room for user to add some extra fee
   if necessary.

   However, we must also try calling it with the exact value, in case the user
   is trying to spend exactly their remaining balance.
   """
   target = targetOutVal + minFee
   bestMatchVal  = 2**64
   bestMatchUtxo = None
   for utxo in unspentTxOutInfo:
      if target <= utxo.getValue() < bestMatchVal:
         bestMatchVal = utxo.getValue()
         bestMatchUtxo = utxo

   closeness = bestMatchVal - target
   if 0 < closeness <= CENT:
      # If we're going to have a change output, make sure it's above CENT
      # to avoid a mandatory fee
      try2Val  = 2**64
      try2Utxo = None
      for utxo in unspentTxOutInfo:
         if target+CENT < utxo.getValue() < try2Val:
            try2Val = utxo.getValue()
            try2Val = utxo
      if not try2Utxo==None:
         bestMatchUtxo = try2Utxo
      

   if bestMatchUtxo==None:
      return []
   else:
      return [bestMatchUtxo]

################################################################################
def PySelectCoins_MultiInput_SingleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   This method should usually be called with a small number added to target val
   so that a tx can be constructed that has room for user to add some extra fee
   if necessary.

   However, we must also try calling it with the exact value, in case the user
   is trying to spend exactly their remaining balance.
   """
   target = targetOutVal + minFee
   outList = []
   sumVal = 0
   for utxo in unspentTxOutInfo:
      sumVal += utxo.getValue()
      outList.append(utxo)
      if sumVal>=targetOutVal:
         break
         
   return outList
         


################################################################################
def PySelectCoins_SingleInput_DoubleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   We will look for a single input that is within 30% of the target
   In case the tx value is tiny rel to the fee: the minTarget calc
   may fail to exceed the actual tx size needed, so we add an extra 

   We restrain the search to 25%.  If there is no one output in this
   range, then we will return nothing, and the SingleInput_SingleValue
   method might return a usable result
   """
   idealTarget    = 2*targetOutVal + minFee

   # check to make sure we're accumulating enough
   minTarget   = long(0.75 * idealTarget)
   minTarget   = max(minTarget, targetOutVal+minFee)
   maxTarget   = long(1.25 * idealTarget)

   if sum([u.getValue() for u in unspentTxOutInfo]) < minTarget:
      return []

   bestMatch = 2**64-1
   bestUTXO   = None
   for txout in unspentTxOutInfo:
      if minTarget <= txout.getValue() <= maxTarget:
         if abs(txout.getValue()-idealTarget) < bestMatch:
            bestMatch = abs(txout.getValue()-idealTarget) 
            bestUTXO = txout

   if bestUTXO==None:
      return []
   else:
      return [bestUTXO]
         
################################################################################
def PySelectCoins_MultiInput_DoubleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):

   idealTarget = 2.0 * targetOutVal 
   minTarget   = long(0.80 * idealTarget)
   minTarget   = max(minTarget, targetOutVal+minFee)
   if sum([u.getValue() for u in unspentTxOutInfo]) < minTarget:
      return []

   outList   = []
   lastDiff  = 2**64-1
   sumVal    = 0
   for utxo in unspentTxOutInfo:
      sumVal += utxo.getValue()
      outList.append(utxo)
      currDiff = abs(sumVal - idealTarget)
      # should switch from decreasing to increasing when best match
      if sumVal>=minTarget and currDiff>lastDiff:
         del outList[-1]
         break
      lastDiff = currDiff

   return outList




################################################################################
def getSelectCoinsScores(utxoSelectList, targetOutVal, minFee):
   """
   Define a metric for scoring the output of SelectCoints.  The output of 
   this method is a tuple of scores which identify a few different factors
   of a txOut selection that users might care about in a selectCoins algorithm.

   This method only returns an absolute score, usually between 0 and 1 for 
   each factor.  It is up to the person calling this method to decide how
   much "weight" they want to give each one.  You could even use the scores
   as multiplicative factors if you wanted, though they were designed with
   the following equation in mind:   finalScore = sum(WEIGHT[i] * SCORE[i])

   TODO:  I need to recalibrate some of these factors, and modify them to 
          represent more directly what the user would be concerned about --
          such as PayFeeFactor, AnonymityFactor, etc.  The information is
          indirectly available with the current set of factors here
   """

   # Need to calculate how much the change will be returned to sender on this tx
   totalIn = sum([utxo.getValue() for utxo in utxoSelectList]) 
   totalChange = totalIn - (targetOutVal+minFee)

   # Abort if this is an empty list (negative score) or not enough coins
   if len(utxoSelectList)==0 or totalIn<targetOutVal+minFee:
      return -1

   
   ##################
   # -- Does this selection include any zero-confirmation tx?
   # -- How many addresses are linked together by this tx?
   addrSet = set([])
   noZeroConf = 1
   for utxo in utxoSelectList:
      addrSet.add(TxOutScriptExtractAddr160(utxo.getScript()))
      if utxo.getNumConfirm() == 0:
         noZeroConf = 0
   numAddr = len(addrSet)
   numAddrFactor = 4.0/(numAddr+1)**2  # values in the range (0, 1]
   
   

   ##################
   # Evaluate output anonanymity
   # One good measure of anonymity is look at trailiing zeros of the value.
   # If one output is like 50.0, and nother if 27.383291, then it's fairly
   # obvious which one is the change.  Can measure that by seeing that 50.0
   # in satoshis has 9 trailing zeros, where as 27.383291 only has 2
   #
   # If the diff is negative, the wrong answer starts to look like the 
   # correct one (about which output is recipient and which is change)
   # We should give "extra credit" for those cases
   def countTrailingZeros(btcVal):
      for i in range(1,20):
         if btcVal % 10**i != 0:
            return i-1
      return 0  # not sure how we'd get here, but let's be safe
   tgtTrailingZeros =  countTrailingZeros(targetOutVal)
   chgTrailingZeros =  countTrailingZeros(totalChange)
   zeroDiff = tgtTrailingZeros - chgTrailingZeros
   outAnonFactor = 0 
   if totalChange==0:
      outAnonFactor = 1
   else:
      if zeroDiff==2:
         outAnonFactor = 0.2
      elif zeroDiff==1:
         outAnonFactor = 0.7
      elif zeroDiff<1:
         outAnonFactor = abs(zeroDiff) + 1


   ##################
   # Equal inputs are anonymous-- but no point in doing this if the 
   # trailing zeros count is way different -- i.e. does it matter if
   # outputs a and b are close, if a=51.000, and b=47.283?  It's
   # still pretty obvious which one is the change. (so: only execute
   # the following block if outAnonFactor > 0)
   #
   # On the other hand, if we have 1.832 and 10.00, and the 10.000 is the 
   # change, we don't really care that they're not close, it's still 
   # damned good/deceptive output anonymity  (so: only execute
   # the following block if outAnonFactor <= 1)
   if 0 < outAnonFactor <= 1 and not totalChange==0:
      outValDiff = abs(totalChange - targetOutVal)
      diffPct = (outValDiff / max(totalChange, targetOutVal))
      if diffPct < 0.20:
         outAnonFactor *= 1
      elif diffPct < 0.50:
         outAnonFactor *= 0.7
      elif diffPct < 1.0:
         outAnonFactor *= 0.3
      else:
         outAnonFactor = 0
   

   ##################
   # Tx size:  we don't have signatures yet, but we assume that each txin is
   #           about 180 Bytes, TxOuts are 35, and 10 other bytes in the Tx
   numBytes  =  10
   numBytes += 180 * len(utxoSelectList)
   numBytes +=  35 * (1 if totalChange==0 else 2)
   txSizeFactor = 0
   numKb = int(numBytes / 1000)
   # Will compute size factor after we see this tx priority and AllowFree
   # results.  If the tx qualifies for free, we don't need to penalize 
   # a 3 kB transaction vs one that is 0.5 kB


   ##################
   # Priority:  If our priority is above the 1-btc-after-1-day threshold
   #            then we might be allowed a free tx.  But, if its priority
   #            isn't much above this thresh, it might take a couple blocks
   #            to be included
   dPriority = 0
   anyZeroConfirm = False
   for utxo in utxoSelectList:
      if utxo.getNumConfirm() == 0:
         anyZeroConfirm = True
      else:
         dPriority += utxo.getValue() * utxo.getNumConfirm()

   dPriority = dPriority / numBytes
   priorityThresh = COIN * 144 / 250
   if dPriority < priorityThresh:
      priorityFactor = 0
   elif dPriority < 10.0*priorityThresh:
      priorityFactor = 0.7
   elif dPriority < 100.0*priorityThresh:
      priorityFactor = 0.9
   else:
      priorityFactor = 1.0


   ##################
   # AllowFree:  If three conditions are met, then the tx can be sent safely
   #             without a tx fee.  Granted, it may not be included in the 
   #             current block if the free space is full, but definitely in 
   #             the next one
   isFreeAllowed = 0
   haveDustOutputs = (0<totalChange<CENT or targetOutVal<CENT) 
   if ((not haveDustOutputs) and \
       dPriority >= priorityThresh and \
       numBytes <= 3500):
      isFreeAllowed = 1
      
   
   ##################
   # Finish size-factor calculation -- if free is allowed, kB is irrelevant
   txSizeFactor = 0
   if isFreeAllowed or numKb<1:
      txSizeFactor = 1
   else:
      if numKb < 2:
         txSizeFactor=0.2
      elif numKb<3:
         txSizeFactor=0.1
      elif numKb<4:
         txSizeFactor=0
      else:
         txSizeFactor=-1  #if this is huge, actually subtract score
                       
   return (isFreeAllowed, noZeroConf, priorityFactor, numAddrFactor, txSizeFactor, outAnonFactor)


################################################################################
# We define default preferences for weightings.  Weightings are used to 
# determine the "priorities" for ranking various SelectCoins results
# By setting the weights to different orders of magnitude, you are essentially
# defining a sort-order:  order by FactorA, then sub-order by FactorB...
################################################################################
# TODO:  ADJUST WEIGHTING!
IDX_ALLOWFREE   = 0
IDX_NOZEROCONF  = 1
IDX_PRIORITY    = 2
IDX_NUMADDR     = 3
IDX_TXSIZE      = 4
IDX_OUTANONYM   = 5
WEIGHTS = [None]*6
WEIGHTS[IDX_ALLOWFREE]  =  100000
WEIGHTS[IDX_NOZEROCONF] = 1000000  # let's avoid zero-conf if possible
WEIGHTS[IDX_PRIORITY]   =      50
WEIGHTS[IDX_NUMADDR]    =  100000
WEIGHTS[IDX_TXSIZE]     =     100 
WEIGHTS[IDX_OUTANONYM]  =      30  

################################################################################
def PyEvalCoinSelect(utxoSelectList, targetOutVal, minFee, weights=WEIGHTS):
   """
   Use a specified set of weightings and sub-scores for a unspentTxOut list, 
   to assign an absolute "fitness" of this particular selection.  The goal of 
   getSelectCoinsScores() is to produce weighting-agnostic subscores -- then
   this method applies the weightings to these scores to get a final answer.
   
   If list A has a higher score than list B, then it's a better selection for
   that transaction.  If you the two scores don't look right to you, then you 
   probably just need to adjust the weightings to your liking.

   These weightings may become user-configurable in the future -- likely as an
   option of coin-selection profiles -- such as "max anonymity", "min fee",
   "balanced", etc).
   """
   SCORES = getSelectCoinsScores(utxoSelectList, targetOutVal, minFee)
   if SCORES==-1:
      return -1

   # Combine all the scores
   score  = 0
   score += WEIGHTS[IDX_NOZEROCONF] * SCORES[IDX_NOZEROCONF]
   score += WEIGHTS[IDX_PRIORITY]   * SCORES[IDX_PRIORITY]
   score += WEIGHTS[IDX_NUMADDR]    * SCORES[IDX_NUMADDR]
   score += WEIGHTS[IDX_TXSIZE]     * SCORES[IDX_TXSIZE]
   score += WEIGHTS[IDX_OUTANONYM]  * SCORES[IDX_OUTANONYM]
   
   # If we're already paying a fee, why bother including this weight?
   if minFee < 0.0005:
      score += WEIGHTS[IDX_ALLOWFREE]  * SCORES[IDX_ALLOWFREE]

   return score


################################################################################
def PySelectCoins(unspentTxOutInfo, targetOutVal, minFee=0, numRand=10, margin=0.01e8):
   """
   Intense algorithm for coin selection:  computes about 30 different ways to
   select coins based on the desired target output and the min tx fee.  Then 
   ranks the various solutions and picks the best one
   """
   if sum([u.getValue() for u in unspentTxOutInfo]) < targetOutVal:
      return []

   targExact  = targetOutVal
   targMargin = targetOutVal+margin

   selectLists = []

   # Start with the intelligent solutions with different sortings
   for sortMethod in range(8):
      diffSortList = PySortCoins(unspentTxOutInfo, sortMethod)
      selectLists.append(PySelectCoins_SingleInput_SingleValue( diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_MultiInput_SingleValue(  diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_SingleInput_SingleValue( diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_MultiInput_SingleValue(  diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_SingleInput_DoubleValue( diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_MultiInput_DoubleValue(  diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_SingleInput_DoubleValue( diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_MultiInput_DoubleValue(  diffSortList, targMargin, minFee ))

   # Throw in a couple random solutions, maybe we get lucky
   # But first, make a copy before in-place shuffling
   # NOTE:  using list[:] like below, really causes a swig::vector<type> to freak out!
   #utxos = unspentTxOutInfo[:]
   #utxos = list(unspentTxOutInfo)  
   for method in range(8,10):
      for i in range(numRand):
         utxos = PySortCoins(unspentTxOutInfo, method)
         selectLists.append(PySelectCoins_MultiInput_SingleValue(utxos, targExact,  minFee))
         selectLists.append(PySelectCoins_MultiInput_DoubleValue(utxos, targExact,  minFee))
         selectLists.append(PySelectCoins_MultiInput_SingleValue(utxos, targMargin, minFee))
         selectLists.append(PySelectCoins_MultiInput_DoubleValue(utxos, targMargin, minFee))

   # Now we define PyEvalCoinSelect as our sorting metric, and find the best solution
   scoreFunc = lambda ulist: PyEvalCoinSelect(ulist, targetOutVal, minFee)
   finalSelection = max(selectLists, key=scoreFunc)
   SCORES = getSelectCoinsScores(finalSelection, targetOutVal, minFee)
   if len(finalSelection)==0:
      return []

   # If we selected a list that has only one or two inputs, and we have
   # other, tiny, unspent outputs from the same addresses, we should 
   # throw one or two of them in to help clear them out.  However, we
   # only do so if a plethora of conditions exist:
   #
   # First, we only consider doing this if the tx has <5 inputs already.
   # Also, we skip this process if the current tx doesn't have excessive
   # priority already -- we don't want to risk de-prioritizing a tx for 
   # this purpose.
   #
   # Next we sort by LOWEST value, because we really benefit from this most
   # by clearing out tiny outputs.  Along those lines, we don't even do 
   # unless it has low priority -- don't want to take a high-priority utxo
   # and convert it to one that will be low-priority to start.
   # 
   # Finally, we shouldn't do this if a high score was assigned to output
   # anonymity: this extra output may cause a tx with good output anonymity 
   # to no longer possess this property
   IDEAL_NUM_INPUTS = 5
   if len(finalSelection)>=IDEAL_NUM_INPUTS or SCORES[IDX_PRIORITY]<0.5:
      return finalSelection
   else:
      for sel in finalSelection:
         addrAlreadyUsed = sel.getRecipientAddr()
         for other in sorted(unspentTxOutInfo, key=(lambda a: a.getValue())):
            # First 3 conditions make sure we're not picking txOut already selected
            if(  addrAlreadyUsed == other.getRecipientAddr() and \
                 sel.getValue() != other.getValue() and \
                 sel.getNumConfirm() != other.getNumConfirm() and \
                 other not in finalSelection and \
                 other.getValue()*other.getNumConfirm() < 10*COIN*144./250. and \
                 other.getNumConfirm() > 0 and \
                 SCORES[IDX_OUTANONYM] == 0):
               finalSelection.append(other)
               if len(finalSelection)>=IDEAL_NUM_INPUTS:
                  return finalSelection

   return finalSelection
               

def calcMinSuggestedFees(selectCoinsResult, targetOutVal, preSelectedFee):
   """
   Returns two fee options:  one for relay, one for include-in-block.
   In general, relay fees are required to get your block propagated
   (since most nodes are Satoshi clients), but there's no guarantee
   it will be included in a block -- though I'm sure there's plenty
   of miners out there will include your tx for sub-standard fee.
   However, it's virtually guaranteed that a miner will accept a fee
   equal to the second return value from this method.

   We have to supply the fee that was used in the selection algorithm,
   so that we can figure out how much change there will be.  Without 
   this information, we might accidentally declare a tx to be freeAllow
   when it actually is not.
   """

   if len(selectCoinsResult)==0:
      return [-1,-1]

   paid = targetOutVal + preSelectedFee
   change = sum([u.getValue() for u in selectCoinsResult]) - paid

   # Calc approx tx size
   numBytes  =  10
   numBytes += 180 * len(selectCoinsResult)
   numBytes +=  35 * (1 if change==0 else 2)
   numKb = int(numBytes / 1000)

   # Compute raw priority of tx
   prioritySum = 0
   for utxo in selectCoinsResult:
      prioritySum += utxo.getValue() * utxo.getNumConfirm()
   prioritySum = prioritySum / numBytes

   # Any tiny/dust outputs?
   haveDustOutputs = (0<change<CENT or targetOutVal<CENT) 

   if((not haveDustOutputs) and \
      prioritySum >= COIN * 144 / 250. and \
      numBytes <= 3600):
      return [0,0]
   
   # This cannot be a free transaction.  
   minFeeMultiplier = (1 + numKb)
   
   # At the moment this condition never triggers
   if minFeeMultiplier<1.0 and haveDustOutputs:
      minFeeMultiplier = 1.0


   return [minFeeMultiplier * MIN_RELAY_TX_FEE, \
           minFeeMultiplier * MIN_TX_FEE]
               


   
   
   
   
################################################################################
################################################################################
def PyBuildUnsignedTx(selectedTxOuts, dstAddrValPairs, force=False):
   pytx = PyTx()
   sumInputs  = sum([utxo.getValue()  for utxo in selectedTxOuts])
   sumOutputs = sum([dst[1]          for dst in dstAddrValPairs])
   txFee = sumInputs - sumOutputs

   if txFee < 0:
      print '***ERROR:  input amount is less than output amount'
      return PyTx()
   elif txFee > 1e8 and not force:
      print '***WARNING:  this transaction includes a rather large fee'
      print '             (%0.2f).  If this was intentional, please' % txFee/1e8
      print '             re-execute this function call with force=True'
      return PyTx()

   # We put the TxOut script we're spending in the TxIn binScript
   # In the OP_CHECKSIG procedure, we will eventually have to put
   # this script here anyway, and then the entity signing this tx
   # will not need any info about the blockchain if we do this
   for inp in selectedTxOuts:
      txin = PyTxIn()
      op = PyOutPoint()
      op.txHash   = inp.getTxHash()
      op.txOutIndex = inp.getTxOutIndex()
      txin.outpoint  = op

      txin.binScript = inp.getScript()  
      txin.intSeq    = 0xffffffff
      pytx.inputs.append(txin)
      
   # Creating the outputs is straightforward.  Always creating a
   # std txout, which includes a 25-byte script 
   #    (4 op-codes, 1 small var_int, 20-byte pubkey hash)
   # This would only be different if we were building a coinbase
   # tx, but that's for miners to do, not within the scope of
   # PyBtcEngine library
   for addr160,val in dstAddrValPairs:
      txout = PyTxOut()
      txout.value = val
      txout.binScript = ''.join([  getOpCode('OP_DUP'        ), \
                                   getOpCode('OP_HASH160'    ), \
                                   '\x14',                      \
                                   addr160,                     \
                                   getOpCode('OP_EQUALVERIFY'), \
                                   getOpCode('OP_CHECKSIG'   )])
      pytx.outputs.append(txout)

   pytx.lockTime = 0
   return pytx


