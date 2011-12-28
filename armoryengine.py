################################################################################
#
# Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory
# Author:     Alan Reiner
# Orig Date:  20 November, 2011
# Descr:      This file serves as an engine for python-based Bitcoin software.
#             I forked this from my own project -- PyBtcEngine -- because I
#             I needed to start including/rewriting code to use CppBlockUtils
#             but did not want to break the pure-python-ness of PyBtcEngine.
#             If you are interested in in a pure-python set of bitcoin utils
#             please go checkout the PyBtcEngine github project.
#
#             Of course, the biggest advatage here is that you have access to
#             the blockchain through BlockObj/BlockObjRef/BlockUtils, as found
#             in the CppForSWIG directory.  This is available in PyBtcEngine,
#             but I had to split out the modules, and I didn't have a good way
#             to maintain the pure-python module while also implementing all
#             the great SWIG-imported C++ utilities I built.
#
#             This module replaces the ECDSA operations, with faster ones
#             implemented in C++ from Crypto++.  This also enables the ability
#             to use SecureBinaryData objects for moving around private keys,
#             though I'm not entirely clear if python-based memory management
#             is going to properly clean up after itself, even with a page-
#             locked, destructable data container.
#
#             In the end, this will be a single, huge, python file that should
#             contain, LITERALLY, every computational Bitcoin operation needed
#             to build a client application in Python, EXCEPT for networking.
#
#             I will try to keep the README up-to-date with the latest features
#             that I have implemented and tested.
#
################################################################################

import copy
import hashlib
import random
import time
import os
import string
import sys
import shutil
import math
from struct import pack, unpack
from datetime import datetime


# These are overriden for testnet
USE_TESTNET = True

# Version Numbers -- numDigits [var, 2, 2, 3]
BTCARMORY_VERSION    = (0, 50, 0, 0)  # (Major, Minor, Minor++, even-more-minor)
PYBTCADDRESS_VERSION = (1, 00, 0, 0)  # (Major, Minor, Minor++, even-more-minor)
PYBTCWALLET_VERSION  = (1, 35, 0, 0)  # (Major, Minor, Minor++, even-more-minor)

ARMORY_DONATION_ADDR = '1Gffm7LKXcNFPrtxy6yF4JBoe5rVka4sn1'
if USE_TESTNET:
   ARMORY_DONATION_ADDR = 'mqQPaNevruP9nRDioszUBAuUqE7zKyHgNc'

def getVersionString(vquad, numPieces=4):
   vstr = '%d.%02d' % vquad[:2]
   if (vquad[2] > 0 or vquad[3] > 0) and numPieces>2:
      vstr += '.%02d' % vquad[2]
   if vquad[3] > 0 and numPieces>3:
      vstr += '.%03d' % vquad[3]
   return vstr

def getVersionInt(vquad, numPieces=4):
   vint  = int(vquad[0] * 1e7)
   vint += int(vquad[1] * 1e5)
   if numPieces>2:
      vint += int(vquad[2] * 1e3)
   if numPieces>3:
      vint += int(vquad[3])
   return vint

def readVersionString(verStr):
   verList = [int(piece) for piece in verStr.split('.')]
   while len(verList)<4:
      verList.append(0)
   return tuple(verList)

def readVersionInt(verInt):
   verStr = str(verInt).rjust(10,'0')
   verList = []
   verList.append( int(verStr[       -3:]) )
   verList.append( int(verStr[    -5:-3 ]) )
   verList.append( int(verStr[ -7:-5    ]) )
   verList.append( int(verStr[:-7       ]) )
   return tuple(verList[::-1])

print '********************************************************************************'
print 'Loading Armory Engine:'
print '   Armory Version:      ', getVersionString(BTCARMORY_VERSION)
print '   PyBtcAddress Version:', getVersionString(PYBTCADDRESS_VERSION)
print '   PyBtcWallet  Version:', getVersionString(PYBTCWALLET_VERSION)

# Get the host operating system
import platform
opsys = platform.system()
OS_WINDOWS = 'win' in opsys.lower()
OS_LINUX   = 'nix' in opsys.lower() or 'nux' in opsys.lower()
OS_MACOSX  = 'mac' in opsys.lower() or 'osx' in opsys.lower()

# Figure out the default directories for Satoshi client, and BicoinArmory
OS_NAME          = ''
USER_HOME_DIR    = ''
BTC_HOME_DIR     = ''
ARMORY_HOME_DIR  = ''
SUBDIR = 'testnet' if USE_TESTNET else ''
if OS_WINDOWS:
   OS_NAME         = 'Windows'
   USER_HOME_DIR   = os.getenv('APPDATA')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, 'Bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, 'Armory', SUBDIR)
elif OS_LINUX:
   OS_NAME         = 'Linux'
   USER_HOME_DIR   = os.getenv('HOME')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, '.bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, '.armory', SUBDIR)
elif OS_MACOSX:
   OS_NAME         = 'Mac/OSX'
   USER_HOME_DIR   = os.path.expanduser('~/Library/Application Support')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, 'Bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, 'Armory', SUBDIR)
else:
   print '***Unknown operating system!'
   print '***Cannot determine default directory locations'

BLK0001_PATH    = os.path.join(BTC_HOME_DIR, 'blk0001.dat')
SETTINGS_PATH   = os.path.join(BTC_HOME_DIR, 'ArmorySettings.txt')

print 'Detected Operating system:', OS_NAME
print '   User home-directory   :', USER_HOME_DIR
print '   Satoshi BTC directory :', BTC_HOME_DIR
print '   Satoshi blk0001.dat   :', BLK0001_PATH
print '   Armory home dir       :', ARMORY_HOME_DIR

if ARMORY_HOME_DIR and not os.path.exists(ARMORY_HOME_DIR):
   os.mkdir(ARMORY_HOME_DIR)



class UnserializeError(Exception): pass
class BadAddressError(Exception): pass
class VerifyScriptError(Exception): pass
class FileExistsError(Exception): pass
class ECDSA_Error(Exception): pass
class PackerError(Exception): pass
class UnpackerError(Exception): pass
class UnitializedBlockDataError(Exception): pass
class WalletLockError(Exception): pass
class SignatureError(Exception): pass
class KeyDataError(Exception): pass
class ChecksumError(Exception): pass
class WalletAddressError(Exception): pass
class PassphraseError(Exception): pass
class EncryptionError(Exception): pass
class InterruptTestError(Exception): pass
class NetworkIDError(Exception): pass
class WalletExistsError(Exception): pass
class ConnectionError(Exception): pass





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
NETWORKS['\x00'] = "Main Network"
NETWORKS['\x6f'] = "Test Network"
NETWORKS['\x34'] = "Namecoin Network"



def coin2str(nSatoshi, ndec=8, rJust=False, maxZeros=8):
   """
   Converts a raw value (1e-8 BTC) into a formatted string for display
   
   ndec, guarantees that we get get a least N decimal places in our result

   maxZeros means we will replace zeros with spaces up to M decimal places
   in order to declutter the amount field

   """

   nBtc = float(nSatoshi) / float(ONE_BTC)
   s = '0.0'
   if   ndec==8:  s = '%0.8f' % (nBtc,)
   elif ndec==7:  s = '%0.7f' % (nBtc,)
   elif ndec==6:  s = '%0.6f' % (nBtc,)
   elif ndec==5:  s = '%0.5f' % (nBtc,)
   elif ndec==4:  s = '%0.4f' % (nBtc,)
   elif ndec==3:  s = '%0.3f' % (nBtc,)
   elif ndec==2:  s = '%0.2f' % (nBtc,)
   elif ndec==1:  s = '%0.1f' % (nBtc,)
   elif ndec==0:  s = '%0.0f' % (nBtc,)

   s = s.rjust(18, ' ')


   if maxZeros < ndec:
      maxChop = ndec - maxZeros
      nChop = min(len(s) - len(str(s.strip('0'))), maxChop)
      if nChop>0:
         s  = s[:-nChop] + nChop*' '

   if not rJust:
      s.strip(' ')

   s = s.replace('. ','  ')

   return s
    

def coin2str_approx(nSatoshi, sigfig=3):
   posVal = nSatoshi
   isNeg = False
   if nSatoshi<0:
      isNeg = True
      posVal *= -1
      
   nDig = max(round(math.log(posVal+1, 10)-0.5), 0)
   nChop = max(nDig-2, 0 )
   approxVal = round((10**nChop) * round(posVal / (10**nChop)))
   return coin2str( (-1 if isNeg else 1)*approxVal,  maxZeros=0)


# This is a sweet trick for create enum-like dictionaries. 
# Either automatically numbers (*args), or name-val pairs (**kwargs)
#http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)



# Some useful constants to be used throughout everything
BASE58CHARS  = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
BASE16CHARS  = 'abcd eghj knrs uwxy'.replace(' ','')
LITTLEENDIAN  = '<';
BIGENDIAN     = '>';
NETWORKENDIAN = '!';
ONE_BTC       = long(1e8)
CENT          = long(1e8/100.)
UNINITIALIZED = None
UNKNOWN       = -2
MIN_TX_FEE    = 50000
MIN_RELAY_TX_FEE = 10000

UINT8_MAX  = 2**8-1
UINT16_MAX = 2**16-1
UINT32_MAX = 2**32-1
UINT64_MAX = 2**64-1

RightNow = time.time
SECOND   = 1
MINUTE   = 60
HOUR     = 3600
DAY      = 24*HOUR
WEEK     = 7*DAY
MONTH    = 30*DAY
YEAR     = 365*DAY



# Define all the hashing functions we're going to need.  We don't actually
# use any of the first three directly (sha1, sha256, ripemd160), we only
# use hash256 and hash160 which use the first three to create the ONLY hash
# operations we ever do in the bitcoin network
# UPDATE:  mini-private-key format requires vanilla sha256... 
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
#
#    The SWIG/C++ block utilities give us access to the blockchain, fast ECDSA
#    operations, and general encryption/secure-binary containers
################################################################################
try:
   import CppBlockUtils as Cpp
   from CppBlockUtils import KdfRomix, CryptoECDSA, CryptoAES, SecureBinaryData
except:
   print '***ERROR:  C++ block utilities not available.'
   print '           Make sure that you have the SWIG-compiled modules'
   print '           in the current directory (or added to the PATH)'
   print '           Specifically, you need:'
   print '                  CppBlockUtils.py     and'
   if OS_LINUX or OS_MACOSX:
      print '                  _CppBlockUtils.so'
   elif OS_WINDOWS:
      print '                  _CppBlockUtils.pyd'
   else:
      print '\n\n... UNKNOWN operating system'
      exit(0)



################################################################################
# Might as well create the BDM right here -- there will only ever be one, anyway
TheBDM = Cpp.BlockDataManager().getBDM()







################################################################################
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


################################################################################
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



def pprintDiff(str1, str2, indent=''):
   if not len(str1)==len(str2):
      print 'pprintDiff: Strings are different length!'
      return

   byteDiff = []
   for i in range(len(str1)):
      if str1[i]==str2[i]:
         byteDiff.append('-')
      else:
         byteDiff.append('X')

   pprintHex(''.join(byteDiff), indent=indent)




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

##### INT/BITS #####

def int_to_bitset(i, widthBytes=0):
   bitsOut = []
   while i>0:
      i,r = divmod(i,2)
      bitsOut.append(['0','1'][r])
   result = ''.join(bitsOut)
   if widthBytes != 0:
      result = result.ljust(widthBytes*8,'0')
   return result

def bitset_to_int(bitset):
   n = 0
   for i,bit in enumerate(bitset):
      n += (0 if bit=='0' else 1) * 2**i
   return n



EmptyHash = hex_to_binary('00'*32)


################################################################################
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
      b58 = BASE58CHARS[r] + b58
   return '1'*padding + b58


################################################################################
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
      n += BASE58CHARS.index(ch)

   binOut = ''
   while n>0:
      d,m = divmod(n,256)
      binOut = chr(m) + binOut
      n = d
   return '\x00'*padding + binOut


   




################################################################################
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
   return '%d.%08d' % divmod (n, ONE_BTC)
def floatStr_to_ubtc(s):
   return long(round(float(s) * ONE_BTC))
def float_to_btc (f):
   return long (round(f * ONE_BTC))


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




def fixChecksumError(binaryStr, chksum, hashFunc=hash256):
   """
   Will only try to correct one byte, as that would be the most
   common error case.  Correcting two bytes is feasible, but I'm
   not going to bother implementing it until I need it.  If it's
   not a one-byte error, it's most likely a different problem
   """
   for byte in range(len(binaryStr)):
      binaryArray = [binaryStr[i] for i in range(len(binaryStr))]
      for val in range(256):
         binaryArray[byte] = chr(val)
         if hashFunc(''.join(binaryArray)).startswith(chksum):
            return ''.join(binaryArray)

   return ''

def computeChecksum(binaryStr, nBytes=4, hashFunc=hash256):
   return hashFunc(binaryStr)[:nBytes]


def verifyChecksum(binaryStr, chksum, hashFunc=hash256, fixIfNecessary=True, \
                                                              beQuiet=False):
   """
   Any time we are given a value and its checksum, we can use
   this method to verify it is valid.  If it's not valid, we
   try to correct up to a one-byte error.  Beyond that, we assume
   that the error is caused by something other than RAM/HDD error.

   The return value is:
      -- No error      :  return input
      -- One byte error:  return input with fixed byte
      -- 2+ bytes error:  return ''

   This method will check the checksum itself for errors, but not correct them.
   However, for PyBtcWallet serialization, if I determine that it is a chksum
   error and simply return the original string, then PyBtcWallet will correct
   the checksum in the file, next time it reserializes the data. 
   """
   bin1 = str(binaryStr)
   bin2 = binary_switchEndian(binaryStr)


   if hashFunc(bin1).startswith(chksum):
      return bin1
   elif hashFunc(bin2).startswith(chksum):
      if not beQuiet: print '***Checksum valid for input with reversed endianness'
      if fixIfNecessary:
         return bin2
   elif fixIfNecessary:
      if not beQuiet: print '***Checksum error!  Attempting to fix...',
      fixStr = fixChecksumError(bin1, chksum, hashFunc)
      if len(fixStr)>0:
         if not beQuiet: print 'fixed!'
         return fixStr
      else:
         # ONE LAST CHECK SPECIFIC TO MY SERIALIZATION SCHEME:
         # If the string was originally all zeros, chksum is hash256('')
         # ...which is a known value, and frequently used in my files
         if chksum==hex_to_binary('5df6e0e2'):
            if not beQuiet: print 'fixed!'
            return ''


   # ID a checksum byte error...
   origHash = hashFunc(bin1)
   for i in range(len(chksum)):
      chkArray = [chksum[j] for j in range(len(chksum))]
      for ch in range(256):
         chkArray[i] = chr(ch)
         if origHash.startswith(''.join(chkArray)):
            print '***Checksum error!  Incorrect byte in checksum!'
            return bin1

   print 'Checksum fix failed'
   return ''


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
def BDM_LoadBlockchainFile(blkfile=None):
   """
   Looks for the blk0001.dat file in the default location for your operating
   system.  If it is found, it is loaded into RAM and the longest chain is
   computed.  Access to any information in the blockchain can be found via
   the bdm object.
   """
   if blkfile==None:
      if not USE_TESTNET:
         if 'win' in opsys.lower():
            blkfile = os.path.join(os.getenv('APPDATA'), 'Bitcoin', 'blk0001.dat')
         if 'nix' in opsys.lower() or 'nux' in opsys.lower():
            blkfile = os.path.join(os.getenv('HOME'), '.bitcoin', 'blk0001.dat')
         if 'mac' in opsys.lower() or 'osx' in opsys.lower():
            blkfile = os.path.expanduser('~/Library/Application Support/Bitcoin/blk0001.dat')
      else:
         if 'win' in opsys.lower():
            blkfile = os.path.join(os.getenv('APPDATA'), 'Bitcoin/testnet', 'blk0001.dat')
         if 'nix' in opsys.lower() or 'nux' in opsys.lower():
            blkfile = os.path.join(os.getenv('HOME'), '.bitcoin/testnet', 'blk0001.dat')
         if 'mac' in opsys.lower() or 'osx' in opsys.lower():
            blkfile = os.path.expanduser('~/Library/Application Support/Bitcoin/testnet/blk0001.dat')

   if not os.path.exists(blkfile):
      raise FileExistsError, ('File does not exist: %s' % blkfile)
   return TheBDM.readBlkFile_FromScratch(blkfile)


################################################################################
################################################################################
#  Classes for reading and writing large binary objects
################################################################################
################################################################################
UINT8, UINT16, UINT32, UINT64, INT8, INT16, INT32, INT64, VAR_INT, VAR_STR, FLOAT, BINARY_CHUNK = range(12)

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
   def getRemainingString(self): return self.binaryStr[self.pos:]
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
      def sizeCheck(sz):
         if self.getRemainingSize()<sz:
            raise UnpackerError

      E = endianness
      pos = self.pos
      if varType == UINT32:
         sizeCheck(4)
         value = unpack(E+'I', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == UINT64:
         sizeCheck(8)
         value = unpack(E+'Q', self.binaryStr[pos:pos+8])[0]
         self.advance(8)
         return value
      elif varType == UINT8:
         sizeCheck(1)
         value = unpack(E+'B', self.binaryStr[pos:pos+1])[0]
         self.advance(1)
         return value
      elif varType == UINT16:
         sizeCheck(2)
         value = unpack(E+'H', self.binaryStr[pos:pos+2])[0]
         self.advance(2)
         return value
      elif varType == INT32:
         sizeCheck(4)
         value = unpack(E+'i', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == INT64:
         sizeCheck(8)
         value = unpack(E+'q', self.binaryStr[pos:pos+8])[0]
         self.advance(8)
         return value
      elif varType == INT8:
         sizeCheck(1)
         value = unpack(E+'b', self.binaryStr[pos:pos+1])[0]
         self.advance(1)
         return value
      elif varType == INT16:
         sizeCheck(2)
         value = unpack(E+'h', self.binaryStr[pos:pos+2])[0]
         self.advance(2)
         return value
      elif varType == VAR_INT:
         sizeCheck(1)
         [value, nBytes] = unpackVarInt(self.binaryStr[pos:pos+9])
         self.advance(nBytes)
         return value
      elif varType == VAR_STR:
         sizeCheck(1)
         [value, nBytes] = unpackVarInt(self.binaryStr[pos:pos+9])
         binOut = self.binaryStr[pos+nBytes:pos+nBytes+value]
         self.advance(nBytes+value)
         return binOut
      elif varType == FLOAT:
         sizeCheck(4)
         value = unpack(E+'f', self.binaryStr[pos:pos+4])
         self.advance(4)
         return value
      elif varType == BINARY_CHUNK:
         sizeCheck(sz)
         binOut = self.binaryStr[pos:pos+sz]
         self.advance(sz)
         return binOut

      print 'Var Type not recognized!  VarType =', varType
      raise UnpackerError, "Var type not recognized!  VarType="+str(varType)



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


   def put(self, varType, theData, width=None, endianness=LITTLEENDIAN):
      """
      Need to supply the argument type you are put'ing into the stream.
      Values of BINARY_CHUNK will automatically detect the size as necessary

      Use width=X to include padding of BINARY_CHUNKs w/ 0x00 bytes
      """
      E = endianness
      if   varType == UINT8:
         self.binaryConcat += int_to_binary(theData, 1, endianness)
      elif varType == UINT16:
         self.binaryConcat += int_to_binary(theData, 2, endianness)
      elif varType == UINT32:
         self.binaryConcat += int_to_binary(theData, 4, endianness)
      elif varType == UINT64:
         self.binaryConcat += int_to_binary(theData, 8, endianness)
      elif varType == INT8:
         self.binaryConcat += pack(E+'b', theData)
      elif varType == INT16:
         self.binaryConcat += pack(E+'h', theData)
      elif varType == INT32:
         self.binaryConcat += pack(E+'i', theData)
      elif varType == INT64:
         self.binaryConcat += pack(E+'q', theData)
      elif varType == VAR_INT:
         self.binaryConcat += packVarInt(theData)[0]
      elif varType == VAR_STR:
         self.binaryConcat += packVarInt(len(theData))[0]
         self.binaryConcat += theData
      elif varType == FLOAT:
         self.binaryConcat += pack(E+'f', theData)
      elif varType == BINARY_CHUNK:
         if width==None:
            self.binaryConcat += theData
         else:
            if len(theData)>width:
               raise PackerError, 'Too much data to fit into fixed width field'
            self.binaryConcat += theData.ljust(width, '\x00')
      else:
         raise PackerError, "Var type not recognized!  VarType="+str(varType)

################################################################################

# The following params are common to ALL bitcoin elliptic curves (secp256k1)
#_p  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
#_r  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
#_b  = 0x0000000000000000000000000000000000000000000000000000000000000007L
#_a  = 0x0000000000000000000000000000000000000000000000000000000000000000L
#_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
#_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L


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


def convertKeyDataToAddress(privKey=None, pubKey=None):
   if not privKey and not pubKey:
      raise BadAddressError, 'No key data supplied for conversion'
   elif privKey:
      if isinstance(privKey, str):
         privKey = SecureBinaryData(privKey)

      if not privKey.getSize()==32:
         raise BadAddressError, 'Invalid private key format!'
      else:
         pubKey = CryptoECDSA().ComputePublicKey(privKey)

   if isinstance(pubKey,str):
      pubKey = SecureBinaryData(pubKey)
   return pubKey.getHash160()



def decodeMiniPrivateKey(keyStr):
   """
   Converts a 22, 26 or 30-character Base58 mini private key into a 
   32-byte binary private key.  
   """
   if not len(keyStr) in (22,26,30):
      return ''

   keyQ = keyStr + '?'
   theHash = sha256(keyQ)
   
   if binary_to_hex(theHash[0]) == '01':
      raise KeyDataError, 'PBKDF2-based mini private keys not supported!'
   elif binary_to_hex(theHash[0]) != '00':
      raise KeyDataError, 'Invalid mini private key... double check the entry'
   
   return sha256(keyStr)
   


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
      # in the blockchain
      #               [unixTime, blkNum]
      self.timeRange = [0,0]
      self.blkRange  = [0,0]

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
   def touch(self, unixTime=None, blkNum=None):
      """
      Just like "touching" a file, this makes sure that the firstSeen and
      lastSeen fields for this address are updated to include "now"

      If we include only a block number, we will fill in the timestamp with
      the unix-time for that block (if the BlockDataManager is availabled)
      """
      if not blkNum==None:
         self.blkRange[0]  = min(self.blkRange[0], blkNum)
         self.blkRange[1]  = max(self.blkRange[1], blkNum)
         if unixTime==None and TheBDM.isInitialized():
            unixTime = TheBDM.getHeaderByHeight(blkNum).getTimestamp()

      if unixTime==None:
         unixTime = RightNow()

      self.timeRange[0] = min(self.timeRange[0], unixTime)
      self.timeRange[1] = max(self.timeRange[1], unixTime)



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
   def isAddressUsed(self):
      isUntouch = self.timeRange[0]==UINT32_MAX and self.blkRange[0]==UINT32_MAX
      return not isUntouch

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
         print 'No encryption key supplied to verifyEncryption!'
         return False


      decryptedKey = CryptoAES().Decrypt( self.binPrivKey32_Encr, \
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
            self.binPublicKey65 = computedPubKey
            verified = (computedPubKey.getHash160()==self.addrStr20)

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
            print '***WARNING:  Address already locked with different IV.'
            print '             Changing IV may cause loss of keydata.'
         else:
            print '***WARNING:  Address already contains an initialization'
            print '             vector.  If you change IV without updating'
            print '             the encrypted storage, you may permanently'
            print '             lose the encrypted data'

         if force:
            pass
         else:
            print '             If you really want to do this, re-execute'
            print '             this call with force=True'
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
         else:
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
               self.binPrivKey32_Encr = CryptoAES().Encrypt( \
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
         self.binPrivKey32_Plain = CryptoAES().Decrypt( \
                                     self.createPrivKeyNextUnlock_IVandKey[1], \
                                     SecureBinaryData(secureKdfOutput), \
                                     self.createPrivKeyNextUnlock_IVandKey[0])

         for i in range(self.createPrivKeyNextUnlock_ChainDepth):
            self.binPrivKey32_Plain = CryptoECDSA().ComputeChainedPrivateKey( \
                                         self.binPrivKey32_Plain, \
                                         self.chaincode)


         # IV should have already been randomly generated, before
         self.isLocked = False
         self.createPrivKeyNextUnlock            = False
         self.createPrivKeyNextUnlock_IVandKey   = []
         self.createPrivKeyNextUnlock_ChainDepth = 0

         # Lock/Unlock to make sure encrypted private key is filled
         self.lock(secureKdfOutput)
         self.unlock(secureKdfOutput)

      else:

         if not self.binPrivKey32_Encr.getSize()==32:
            raise WalletLockError, 'No encrypted private key to decrypt!'

         if not self.binInitVect16.getSize()==16:
            raise WalletLockError, 'Initialization Vect (IV) is missing!'

         self.binPrivKey32_Plain = CryptoAES().Decrypt( \
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
         # We add an extra 0 byte to the beginning of each value to guarantee
         # that they are interpretted as unsigned integers.  Not always necessary
         # but it doesn't hurt to always do it.
         rBin   = '\x00' + sigstr[:32 ]
         sBin   = '\x00' + sigstr[ 32:]
         rSize  = int_to_binary(len(rBin))
         sSize  = int_to_binary(len(sBin))
         rsSize = int_to_binary(len(rBin) + len(sBin) + 4)
         sigScr = '\x30' + rsSize + \
                  '\x02' + rSize + rBin + \
                  '\x02' + sSize + sBin
         return sigScr
      except:
         print 'Failed signature generation'
      finally:
         # Always re-lock/cleanup after unlocking, even after an exception.
         # If locking triggers an error too, we will just skip it.
         try:
            if secureKdfOutput!=None:
               self.lock(secureKdfOutput)
         except:
            pass




   #############################################################################
   def verifyDERSignature(self, binMsgVerify, derSig):
      if not self.hasPubKey():
         raise KeyDataError, 'No public key available for this address!'

      if not isinstance(derSig, str):
         # In case this is a SecureBinaryData object...
         derSig = derSig.toBinStr()

      codeByte = derSig[0]
      nBytes   = binary_to_int(derSig[1])
      rsStr    = derSig[2:2+nBytes]
      assert(codeByte == '\x30')
      assert(nBytes == len(rsStr))
      # Read r
      codeByte  = rsStr[0]
      rBytes    = binary_to_int(rsStr[1])
      r         = rsStr[2:2+rBytes]
      assert(codeByte == '\x02')
      sStr      = rsStr[2+rBytes:]
      # Read s
      codeByte  = sStr[0]
      sBytes    = binary_to_int(sStr[1])
      s         = sStr[2:2+sBytes]
      assert(codeByte == '\x02')
      # Now we have the (r,s) values of the

      secMsg    = SecureBinaryData(binMsgVerify)
      secSig    = SecureBinaryData(r[-32:] + s[-32:])
      secPubKey = SecureBinaryData(self.binPublicKey65)
      return CryptoECDSA().VerifyData(secMsg, secSig, secPubKey)



   #############################################################################
   def createNewRandomAddress(self, secureKdfOutput=None, IV16=None):
      """
      This generates a new private key directly into a secure binary container
      and then encrypts it immediately if encryption is enabled and the AES key
      (from KDF) is available to do so.  This behaves like a static method,
      returning a copy/ref to itself.

      TODO:  There is no way for this method to know whether you wanted the
             key to be encrypted forgot to provide a key
      """
      self.__init__()
      self.binPrivKey32_Plain = CryptoECDSA().GenerateNewPrivateKey()
      self.binPublicKey65 = CryptoECDSA().ComputePublicKey(self.binPrivKey32_Plain)
      self.addrStr20 = self.binPublicKey65.getHash160()
      self.isInitialized = True

      if secureKdfOutput!=None:
         self.binInitVect16 = IV16
         if IV16==None or IV16.getSize()!=16:
            self.binInitVect16 = SecureBinaryData().GenerateRandom(16)
         self.lock(secureKdfOutput)
         self.isLocked      = True
         self.useEncryption = True
      else:
         self.isLocked      = False
         self.useEncryption = False
      return self


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
            newPriv = CryptoECDSA().ComputeChainedPrivateKey( \
                                    self.binPrivKey32_Plain, \
                                    self.chaincode, \
                                    self.binPublicKey65)
         else:
            newPriv = CryptoECDSA().ComputeChainedPrivateKey( \
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
         newAddr.binPublicKey65 = CryptoECDSA().ComputeChainedPublicKey( \
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
         print ''
         print '***WARNING: you have chosen to serialize a key you hope to be'
         print '            encrypted, but have not yet chosen a passphrase for'
         print '            it.  The only way to serialize this address is with '
         print '            the plaintext keys.  Please lock this address at'
         print '            least once in order to enable encrypted output.'
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
      binOut.put(UINT32,         getVersionInt(PYBTCADDRESS_VERSION))
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



################################################################################
# Identify all the codes/strings that are needed for dealing with scripts
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


TXIN_SCRIPT_STANDARD = 0
TXIN_SCRIPT_COINBASE = 1
TXIN_SCRIPT_SPENDCB  = 2
TXIN_SCRIPT_UNKNOWN  = 3

TXOUT_SCRIPT_STANDARD = 0
TXOUT_SCRIPT_COINBASE = 1
TXOUT_SCRIPT_MULTISIG = 2
TXOUT_SCRIPT_OP_EVAL  = 3
TXOUT_SCRIPT_UNKNOWN  = 4

MULTISIG_1of1     = (1,1)
MULTISIG_1of2     = (1,2)
MULTISIG_2oF2     = (2,2)
MULTISIG_1oF3     = (1,3)
MULTISIG_2oF3     = (2,3)
MULTISIG_3oF3     = (3,3)
MULTISIG_UNKNOWN  = (0,0)


################################################################################
def getTxOutMultiSigInfo(binScript):
   """
   Gets the Multi-Sig tx type, as well as all the address-160 strings of
   the keys that are needed to satisfy this transaction.  This currently
   only identifies M-of-N transaction types, returning unknown otherwise.

   However, the address list it returns should be valid regardless of
   whether the type was unknown:  we assume all 20-byte chunks of data
   are public key hashes, and 65-byte chunks are public keys.

   NOTE:  Because the address list is always valid, there is no reason
          not to use this method to extract addresses from ANY scripts,
          not just multi-sig...
   """
   addr160List = []
   pub65List   = []
   bup = BinaryUnpacker(binScript)
   opcodes = []
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
         opcodes.append(nextByte)
         

      if len(binChunk) == 20:
         addr160List.append(binChunk)
         pub65List.append('')
         opcodes.append('<Addr20>')
      elif len(binChunk) == 65:
         addr160List.append(convertKeyDataToAddress(pubKey=binChunk))
         pub65List.append(binChunk)
         opcodes.append('<PubKey65>')


   mstype = MULTISIG_UNKNOWN
   #print 'Transaction:',
   #for op in opcodes:
      #print op,

   # First assume that this is an M-of-N script
   try:
      isCMS = opcodes[-1]==getOpCode('OP_CHECKMULTISIG')
      M = int(opcodes[ 0])
      N = int(opcodes[-2])
      keys  = opcodes[1:-2]
      nPub = sum([(1 if p=='PubKey65' else 0) for p in keys])
      if 0<M<3 and 0<N<=3 and N==nPub:
         # We have a legit M-of-N script, figure out which one
         if M==1 and N==1: return MULTISIG_1of1, addr160List, pub65List
         if M==1 and N==2: return MULTISIG_1of2, addr160List, pub65List
         if M==2 and N==2: return MULTISIG_2oF2, addr160List, pub65List
         if M==1 and N==3: return MULTISIG_1oF3, addr160List, pub65List
         if M==2 and N==3: return MULTISIG_2oF3, addr160List, pub65List
         if M==3 and N==3: return MULTISIG_3oF3, addr160List, pub65List
   except:
      pass

      
   # Next try A-or-(B-and-C) transaction (not implemented yet
   # I'm not sure how these transactions will look
   try:
      pass
   except:
      pass

   return MULTISIG_UNKNOWN, addr160List, pub65List


################################################################################
def getTxOutScriptType(binScript):
   if binScript[:2] == hex_to_binary('4104'):
      is65B = len(binScript) == 67
      lastByteMatch = binScript[-1] == getOpCode('OP_CHECKSIG')
      if (is65B and lastByteMatch):
         return TXOUT_SCRIPT_COINBASE
   else:
      is1 = binScript[ 0] == getOpCode('OP_DUP')
      is2 = binScript[ 1] == getOpCode('OP_HASH160')
      is3 = binScript[-2] == getOpCode('OP_EQUALVERIFY')
      is4 = binScript[-1] == getOpCode('OP_CHECKSIG')
      if (is1 and is2 and is3 and is4):
         return TXOUT_SCRIPT_STANDARD

   # If we got here, let's check if it's a standard Multi-sig type
   mstype = getTxOutMultiSigInfo(binScript)[0]
   if mstype!=MULTISIG_UNKNOWN:
      return TXOUT_SCRIPT_MULTISIG

   return TXOUT_SCRIPT_UNKNOWN

################################################################################
def TxOutScriptExtractAddrStr(binScript):
   return hash160_to_addrStr(TxOutScriptExtractAddr160(binScript))

################################################################################
def TxOutScriptExtractAddr160(binScript):
   txoutType = getTxOutScriptType(binScript)
   if txoutType == TXOUT_SCRIPT_UNKNOWN:
      return '<Non-standard TxOut script>'

   if txoutType == TXOUT_SCRIPT_COINBASE:
      return convertKeyDataToAddress(pubKey=binScript[1:66])
   elif txoutType == TXOUT_SCRIPT_STANDARD:
      return binScript[3:23]
   elif txoutType == TXOUT_SCRIPT_MULTISIG:
      # Returns a list of addresses
      return getTxOutMultiSigInfo(binScript)[1]


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
   if not (b1=='\x30' and b3=='\x02'):
      return TXIN_SCRIPT_UNKNOWN

   SigSize = binary_to_int(b2) + 3
   PubkeySize = 66  # 0x4104[Pubx][Puby]

   if len(binScript)==SigSize:
      return TXIN_SCRIPT_SPENDCB
   elif len(binScript)==(SigSize + PubkeySize + 1):
      return TXIN_SCRIPT_STANDARD

   return TXIN_SCRIPT_UNKNOWN


################################################################################
def TxInScriptExtractKeyAddr(txinObj):
   scrType = getTxInScriptType(txinObj)
   if scrType == TXIN_SCRIPT_STANDARD:
      pubKeyBin = txinObj.binScript[-65:]
      newAddr = PyBtcAddress().createFromPublicKey(pubKeyBin)
      return (newAddr.calculateAddrStr(), newAddr.binPublicKey65.toBinStr()) # LITTLE_ENDIAN
   elif scrType == TXIN_SCRIPT_COINBASE:
      return ('[COINBASE-NO-ADDR: %s]'%binary_to_hex(txinObj.binScript), '[COINBASE-NO-PUBKEY]')
      #return ('[COINBASE-NO-ADDR]', '[COINBASE-NO-PUBKEY]')
   elif scrType == TXIN_SCRIPT_SPENDCB:
      return ('[SPENDCOINBASE]', '[SPENDCOINBASE]')
   else:
      return ('[UNKNOWN-TXIN]', '[UNKNOWN-TXIN]')



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
      self.txOutIndex = opData.get(UINT32)
      return self

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.txHash)
      binOut.put(UINT32, self.txOutIndex)
      return binOut.getBinaryString()


   def copy(self):
      return PyOutPoint().unserialize(self.serialize())


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

   def copy(self):
      return PyTxIn().unserialize(self.serialize())


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
                  '('+binary_to_hex(self.binScript)[:64]+')'
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

   def getValue(self):
      return self.value

   def getScript(self):
      return self.binScript

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT64, self.value)
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      return binOut.getBinaryString()

   def copy(self):
      return PyTxOut().unserialize(self.serialize())

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'TxOut:'
      print indstr + indent + 'Value:   ', self.value, '(', float(self.value) / ONE_BTC, ')'
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

   def copy(self):
      return PyTx().unserialize(self.serialize())

   def getHash(self):
      if self.thisHash == UNINITIALIZED:
         self.thisHash = hash256(self.serialize())
      return self.thisHash

   def getHashHex(self, endianness=LITTLEENDIAN):
      return binary_to_hex(self.getHash(), endOut=endianness)


   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'Transaction:'
      print indstr + indent + 'TxHash:   ', self.getHashHex(endian), \
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



   #def pprintShort(self, nIndent=0, endian=BIGENDIAN):
      #print '\nTransaction: %s' % self.getHashHex()


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

   def copy(self):
      return PyBlockHeader().unserialize(self.serialize())

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
      print indstr + indent + 'Version:   ', self.version
      print indstr + indent + 'ThisHash:  ', binary_to_hex( self.theHash, endOut=endian), \
                                                      '(BE)' if endian==BIGENDIAN else '(LE)'
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
      if txOldData and txNew and not txInIndex==None:
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
      self.script1 = str(txNew.inputs[txInIndex].binScript) # copy
      self.txInIndex  = txInIndex
      self.txOutIndex = txNew.inputs[txInIndex].outpoint.txOutIndex
      self.txHash  = txNew.inputs[txInIndex].outpoint.txHash

      if isinstance(txOldData, PyTx):
         if not self.txHash == hash256(txOldData.serialize()):
            print '*** Supplied incorrect pair of transactions!'
         self.script2 = str(txOldData.outputs[self.txOutIndex].binScript)
      elif isinstance(txOldData, PyTxOut):
         self.script2 = str(txOldData.binScript)
      elif isinstance(txOldData, str):
         self.script2 = str(txOldData)



   def verifyTransactionValid(self, txOldData=None, txNew=None, txInIndex=-1):
      if txOldData and txNew and txInIndex != -1:
         self.setTxObjects(txOldData, txNew, txInIndex)
      else:
         txOldData = self.script2
         txNew = self.txNew
         txInIndex = self.txInIndex

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

      # Hashes are computed as part of CppBlockUtils::CryptoECDSA methods
      ##hashToVerify = hash256(toHash)
      ##hashToVerify = binary_switchEndian(hashToVerify)

      # 10. Apply ECDSA signature verification
      if senderAddr.verifyDERSignature(toHash, justSig):
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
         return OP_DISABLED
      elif opcode == OP_DIV:
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
                                      dstAddr.binPublicKey65.toBinStr(),  \
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

         # CppBlockUtils::CryptoECDSA modules do the hashing for us
         ##binToSign = hash256(preHashMsg)
         ##binToSign = binary_switchEndian(binToSign)

         signature = srcAddr.generateDERSignature(preHashMsg)


         # If we are spending a Coinbase-TxOut, only need sig, no pubkey
         # Don't forget to tack on the one-byte hashcode and consider it part of sig
         if len(prevTxOut.binScript) > 30:
            sigLenInBinary = int_to_binary(len(signature) + 1)
            newTx.inputs[i].binScript = sigLenInBinary + signature + hashCode1
         else:
            pubkey = srcAddr.binPublicKey65.toBinStr()
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
class PyUnspentTxOut(object):
   def __init__(self, addr='', val=-1, numConf=-1):
      self.addr = addr
      self.val  = long(val*ONE_BTC)
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
      print '   ', ('%0.2f' % (utxo.getValue()*utxo.getNumConfirm()/(ONE_BTC*144.))).rjust(16)


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
   priorityThresh = ONE_BTC * 144 / 250
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
def PySelectCoins(unspentTxOutInfo, targetOutVal, minFee=0, numRand=10, margin=CENT):
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
                 other.getValue()*other.getNumConfirm() < 10*ONE_BTC*144./250. and \
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
      prioritySum >= ONE_BTC * 144 / 250. and \
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
# This class can be used for both multi-signature tx collection, as well as
# offline wallet signing (you are collecting signatures for a 1-of-1 tx only
# involving yourself).
class PyTxDistProposal(object):
   """
   PyTxDistProposal is created from a PyTx object, and represents
   an unsigned transaction, that may require the signatures of
   multiple parties before being accepted by the network.

   We assume that the PyTx object has been prepared already by
   replacing all the TxIn scripts with the scripts of the TxOuts
   they are spending.

   In other words, in order to prepare a PyTxDistProposal, you
   will need access to the blockchain to find the txouts you are
   spending (and thus they have to be acquired with external
   code, such as my CppBlockUtils SWIG module).  But once the
   TxDP is created, the system signing it only needs the ECDSA
   private keys and nothing else.   This enables the device
   providing the signatures to be extremely lightweight.

   For a given TxDP, we will be storing the following structure
   in memory.  Use a 3-input tx as an example, with the first 
   being a 2-of-3 multi-sig transaction (unsigned)
      
      self.scriptTypes    = [TXOUT_SCRIPT_MULTISIG, 
                             TXOUT_SCRIPT_STANDARD,   
                             TXOUT_SCRIPT_STANDARD]

      self.inputValues    = [ 2313000000, 
                              400000000, 
                              1000000000]

      self.signatures     = [ ['', '', ''],
                              [''],
                              [''],         ]

      self.inAddr20Lists  = [ [addr1, addr2, addr3],
                              [addr4]
                              [addr5]         ]

      # Usually only have public keys on multi-sig TxOuts
      self.inPubKeyLists  = [ [pubKey1, pubKey2, pubKey3],
                              ['']
                              ['']         ]   

      self.numSigsNeeded  = [ 2
                              1
                              1 ]
      
   """
   #############################################################################
   def __init__(self, pytx=None):
      self.pytxObj       = UNINITIALIZED
      self.uniqueB58     = ''
      self.scriptTypes   = []
      self.signatures    = []
      self.txOutScripts  = []
      self.inAddr20Lists = []
      self.inPubKeyLists = []
      self.inputValues   = []
      self.numSigsNeeded = []
      if pytx:
         self.createFromPreparedPyTx(pytx)

   #############################################################################
   def createFromPreparedPyTx(self, pytx):
      sz = len(pytx.inputs)
      self.pytxObj = pytx
      self.signatures     = [[]]*sz
      self.scriptTypes    = [None]*sz
      self.inAddr20Lists  = [[]]*sz
      self.inPubKeyLists  = [[]]*sz
      self.inputValues    = [-1]*sz
      self.numSigsNeeded  = [0]*sz
      for i in range(sz):
         script = str(pytx.inputs[i].binScript)
         self.txOutScripts.append(str(script)) # copy it
         scrType = getTxOutScriptType(pytx.inputs[i].binScript)
         self.scriptTypes[i] = scrType
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            self.inAddr20Lists[i].append(TxOutScriptExtractAddr160(script))
            self.inPubKeyLists[i].append('')
            self.signatures[i]    = ['']
            self.numSigsNeeded[i] = 1
         elif scrType==TXOUT_SCRIPT_MULTISIG:
            mstype, addrs, pubs = getTxOutMultiSigInfo(script)
            self.inAddr20Lists[i] = addrs
            self.inPubKeyLists[i] = pubs
            self.signatures[i]    = ['']*len(addrs)
            self.numSigsNeeded[i] = mstype[0]  # mstype for M-of-N tx is (M,N)
         elif scrType in (TXOUT_SCRIPT_OP_EVAL, TXOUT_SCRIPT_UNKNOWN):
            pass

      txser = self.pytxObj.serialize()
      self.uniqueB58 = binary_to_base58(hash256(txser))[:8]
      return self

   #############################################################################
   def createFromTxOutSelection(self, utxoSelection, recip160ValPairs):
      """
      This creates a TxDP for a standard transaction from a list of inputs and 
      a list of recipient-value-pairs.  

      NOTE:  I have modified this so that if the "recip" is not a 20-byte binary
             string, it is instead interpretted as a SCRIPT -- which could be
             anything, including a multi-signature transaction
      """
      pprintUnspentTxOutList(utxoSelection)
      print sumTxOutList(utxoSelection)
      print sum([a[1] for a in recip160ValPairs])
      assert(sumTxOutList(utxoSelection) >= sum([a[1] for a in recip160ValPairs]))
      self.pytxObj = PyTx()
      self.pytxObj.version = 1
      self.pytxObj.lockTime = 0
      self.pytxObj.inputs = []
      self.pytxObj.outputs = []

      for iin,utxo in enumerate(utxoSelection):
         txin = PyTxIn()
         txin.outpoint = PyOutPoint()
         txin.outpoint.txHash = utxo.getTxHash()
         txin.outpoint.txOutIndex = utxo.getTxOutIndex()
         txin.binScript = utxo.getScript() # this is the TxOut script
         self.txOutScripts.append(str(txin.binScript)) # copy it
         txin.intSeq = 2**32-1
         self.pytxObj.inputs.append(txin)
         self.inputValues.append(utxo.getValue())

         stype = getTxOutScriptType(utxo.getScript())
         self.scriptTypes.append(stype)
         if stype in (TXOUT_SCRIPT_COINBASE, TXOUT_SCRIPT_STANDARD):
            # Only one addr/str per input
            self.inAddr20Lists.append( [utxo.getRecipientAddr()] )
            self.inPubKeyLists.append( [''] )
            self.signatures.append( [''] )
            self.numSigsNeeded.append(1)
         elif stype in (TXOUT_SCRIPT_MULTISIG,):
            # May be multiple addr/str per input
            msType, addrlist, publist = getTxOutMultiSigInfo(utxo.getScript())
            self.inAddr20Lists.append(addrlist)
            self.inPubKeyLists.append(publist)
            self.numSigsNeeded[i] = msType[0]  # mstype for M-of-N tx is (M,N)
            self.signatures.append( ['']*msType[1])
            

      for recipObj,value in recip160ValPairs:
         txout = PyTxOut()
         txout.value = long(value)

         # Assume recipObj is either a PBA or a string
         if isinstance(recipObj, PyBtcAddress):
            recipObj = recipObj.getAddr160()

         # Now recipObj is def a string
         if len(recipObj)!=20:
            # If not an address, it's a full script
            txout.binScript = recipObj
         else:
            # Construct a std TxOut from addr160 str
            txout.binScript = ''.join([  getOpCode('OP_DUP'        ), \
                                         getOpCode('OP_HASH160'    ), \
                                         '\x14',                      \
                                         recipObj,
                                         getOpCode('OP_EQUALVERIFY'), \
                                         getOpCode('OP_CHECKSIG'   )])

         self.pytxObj.outputs.append(txout)

      # Finally, we have the fully-constructed PyTx object with txin scripts
      # replaced by the TxOut scripts they are spending
      txser = self.pytxObj.serialize()
      self.uniqueB58 = binary_to_base58(hash256(txser))[:8]
      return self


   #############################################################################
   def appendSignature(self, binSig, txinIndex=None):
      """
      Use this to add a signature to the TxDP object in memory.
      """
      idx, pos, addr = self.processSignature(binSig, txinIndex, checkAllInputs=True)
      if addr:
         self.signatures[validIdx].append(binSig)
         return True
   
      return False


   #############################################################################
   def processSignature(self, sigStr, txinIdx, checkAllInputs=False):
      """
      For standard transaction types, the signature field is actually the raw
      script to be plugged into the final transaction that allows it to eval
      to true -- except for multi-sig transactions.  We have to mangle the 
      data a little bit if we want to use the script-processor to verify the
      signature.  Instead, we will use the crypto ops directly.

      The return value is everything we need to know about this signature:
      -- TxIn-index:    if checkAllInputs=True, we need to know which one worked
      -- Addr-position: for multi-sig tx, we need to know which addr it matches
      -- Addr160:       address to which this signature corresponds
      """

      if txinIdx==None or txinIdx<0 or txinIdx>=len(self.pytxObj.inputs):
         pass
      else:
         scriptType = self.scriptTypes[txinIdx]
         txCopy = PyTx().unserialize(self.pytxObj.serialize())
         if scriptType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            # For standard Tx types, sig is the script itself (copy it)
            prevOutScript = str(txCopy.inputs[txinIdx].binScript)
            txCopy.inputs[txinIdx].binScript = str(sigStr)
            psp = PyScriptProcessor(prevOutScript, txCopy, txinIdx)
            if psp.verifyTransactionValid():
               return txinIdx, 0, TxOutScriptExtractAddr160(prevOutScript)
         elif scriptType == TXOUT_SCRIPT_MULTISIG:
            # We have to verify the signature manually...
            for i in range(len(txCopy.inputs)):
               if not i==idx:
                  txCopy.inputs[i].binScript = ''
   
            hashCode   = binary_to_int(sigStr[-1])
            hashCode4  = int_to_binary(hashcode, widthBytes=4)
            preHashMsg = txCopy.serialize() + hashCode4
            if not hashCode==1:
               raise NotImplementedError, 'Non-standard hashcodes not supported!'
   
            # Now check all public keys in the multi-sig TxOut script
            for i,pubkey in enumerate(self.inPubKeyLists):
               tempAddr = PyBtcAddress().createFromPublicKeyData(pubkey)
               if tempAddr.verifyDERSignature(preHashMsg, sigStr):
                  return txInIdx, i, hash160(pubkey)
         

      if checkAllInputs:
         for i in range(len(self.pytxObj.inputs)):
            idx, pos, addr160 = self.processSignature(sigStr, i)
            if idx>0:
               return idx, pos, addr160
         
      return -1,-1,''
      

   #############################################################################
   def checkTxHasEnoughSignatures(self, alsoVerify=False):
      """
      This method only counts signatures, unless verify==True
      """
      for i in range(len(self.pytxObj.inputs)):
         numSigsHave = sum( [(1 if sig else 0) for sig in self.signatures[i]] )
         if numSigsHave<self.numSigsNeeded[i]:
            return False

      if not alsoVerify:
         return True

      if not self.getBroadcastTxIfReady():
         return False

      return True
      
      
      
            

   #############################################################################
   def getBroadcastTxIfReady(self):
      try:
         return self.prepareFinalTx()
      except SignatureError, msg:
         return None
      # Let all other exceptions go on up the chain
   

   #############################################################################
   def prepareFinalTx(self):
      """
      This converts the TxDP back into a regular PyTx object, verifying
      signatures as it goes.  Throw an error if the TxDP does not have
      the complete set of valid signatures needed to be accepted by the 
      network.
      """
      # We must make/modify a copy of the TxDP, because serialization relies
      # on having the original TxDP intact.
      finalTx = PyTx().unserialize(self.pytxObj.serialize())

      # Put the txIn scripts together (non-trivial for multi-sig cases)
      # then run them through the script evaluator to make sure they
      # are valid. 
      psp = PyScriptProcessor()
      for i,txin in enumerate(finalTx.inputs):
         if self.scriptTypes[i] in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            finalTx.inputs[i].binScript = self.signatures[i][0]
         elif self.scriptTypes[i]==TXOUT_SCRIPT_MULTISIG:
            sortedSigs = ['']*len(self.inAddr20Lists[i])
            for sig in self.signatures[i]:
               idx, pos, addr = self.processSignature(sig, i)
               if not addr:
                  raise SignatureError, 'Sig is not valid for input', i
               else:
                  sortedSigs[pos] = sig
            finalTx.inputs[i].binScript = getOpCode('OP_0') + ''.join(sortedSigs)

         psp.setTxObjects(self.txOutScripts[i], finalTx, i)
         totalScriptValid = psp.verifyTransactionValid()
         if not totalScriptValid:
            print 'Invalid script for input %d:'
            pprintScript(finalTx.inputs[i].binScript, 2)
            print 'Spending txout script:'
            pprintScript(self.txOutScripts[i], 2)
            raise SignatureError, 'Invalid script for input %d' % i
         else:
            if len(self.inAddr20Lists)==1: print 'Signature', i, 'is valid!'
            else: print 'Signatures for input', i, 'are valid!'
      return finalTx


   #############################################################################
   def serializeAscii(self):
      txdpLines = []
      headline = ('-----BEGIN-TRANSACTION-' + self.uniqueB58 + '-----').ljust(80,'-')
      txdpLines.append( headline )
      dpsz = len(self.pytxObj.serialize())
      pieces = ['', 'TXDIST', binary_to_hex(MAGIC_BYTES), self.uniqueB58, \
                      int_to_hex(dpsz, widthBytes=2, endOut=BIGENDIAN)]
      txdpLines.append('_'.join(pieces))
      
      txHex = binary_to_hex(self.pytxObj.serialize())
      for byte in range(0,len(txHex),80):
         txdpLines.append( txHex[byte:byte+80] )


      for iin,txin in enumerate(self.pytxObj.inputs):
         # TODO: come up with a better way than "0" to specify no-value-avail
         if self.inputValues[iin]:
            formattedVal = coin2str(self.inputValues[iin], ndec=8)
         else:
            formattedVal = '0'

         txdpLines.append('_TXINPUT_%02d_%s' % (iin, formattedVal.strip()))
         for s,sig in enumerate(self.signatures[iin]):
            if len(sig)==0:
               continue
            addrB58 = hash160_to_addrStr(self.inAddr20Lists[iin][s])
            sigsz = int_to_hex(len(sig), widthBytes=2, endOut=BIGENDIAN)
            txdpLines.append('_SIG_%s_%02d_%s' % (addrB58, iin, sigsz))
            sigHex = binary_to_hex(sig)
            for byte in range(0,len(sigHex),80):
               txdpLines.append( sigHex[byte:byte+80] )

      endline = ('-------END-TRANSACTION-' + self.uniqueB58 + '-----').ljust(80,'-')
      txdpLines.append( endline )
      return '\n'.join(txdpLines)
      

   #############################################################################
   def unserializeAscii(self, asciiStr):
      txdpTxt = [line.strip() for line in asciiStr.split('\n')]


      # Why can't I figure out the best way to do this?  I thought this is what
      # generators are for, but I was clearly mistaken...
      # I know there's a bettery [python-]way to do this...
      L = [0]
      def nextLine(i):
         s = txdpTxt[i[0]]
         i[0] += 1
         return s

      line = nextLine(L)
      while not ('BEGIN-TRANSACTION' in line):
         line = nextLine(L)

      #try:
      # Get the network, dp ID and number of bytes
      line = nextLine(L)
      magicBytesHex, dpIdB58, dpsz = line.split('_')[2:]
      magic = hex_to_binary(magicBytesHex)

      dpser = ''
      line = nextLine(L)
      while not 'TXINPUT' in line:
         dpser += line
         line = nextLine(L)

      dpserBin = hex_to_binary(dpser) 
      newTx = PyTx().unserialize(dpserBin)
      self.createFromPreparedPyTx( newTx )
      numIn = len(self.pytxObj.inputs)

      # Do some sanity checks
      if not self.uniqueB58 == dpIdB58:
         raise UnserializeError, 'TxDP: Actual DPID does not match listed ID'
      if not MAGIC_BYTES==magic:
         raise NetworkIDError, 'TxDP is for diff blockchain! (%s)' % \
                                                         BLOCKCHAINS[magic]

      # We stopped before when we had the first TXINPUT line
      while not 'END-TRANSACTION' in line: 
         [iin, val] = line.split('_')[2:]
         iin = int(iin)
         self.inputValues[iin] = float(val)*ONE_BTC
         
         line = nextLine(L)
         while '_SIG_' in line:
            addrB58, sz, sigszHex = line.split('_')[2:]
            sz = int(sz) 
            sigsz = hex_to_int(sigszHex, endIn=BIGENDIAN)
            hexSig = ''
            line = nextLine(L)
            while (not '_SIG_' in line)   and \
                  (not 'TXINPUT' in line) and \
                  (not 'END-TRANSACTION' in line):
               hexSig += line
               line = nextLine(L)
            binSig = hex_to_binary(hexSig)
            idx, sigOrder, addr160 = self.processSignature(binSig, iin)
            if idx == -1:
               raise SignatureError, 'Invalid sig: Input %d, addr=%s' % \
                                                             (iin, addrB58)
            if not hash160_to_addrStr(addr160)== addrB58:
               raise BadAddressError, 'Listed addr does not match computed addr'
            # If we got here, the signature is valid!
            self.signatures[iin][sigOrder] = binSig

      #except:
         #raise UnserializeError, 'Could not read TxDP!'

      return self
      

   def serializeBinary(self):
      pass

   def serializeHex(self):
      return binary_to_hex(self.serializeBinary())

   #def serializeBase58(self):
      #return binary_to_hex(self.serializeBinary())


   #############################################################################
   def pprint(self, indent=''):
      tx = self.pytxObj
      propID = hash256(tx.serialize())
      print indent+'Distribution Proposal : ', binary_to_base58(propID)[:8]
      print indent+'Transaction Version   : ', tx.version
      print indent+'Transaction Lock Time : ', tx.lockTime
      print indent+'Num Inputs            : ', len(tx.inputs)
      for i,txin in enumerate(tx.inputs):
         prevHash = txin.outpoint.txHash
         prevIndex = txin.outpoint.txOutIndex
         #print '   PrevOut: (%s, index=%d)' % (binary_to_hex(prevHash[:8]),prevIndex),
         print indent*2 + 'Value: %s' % self.inputValues[i]
         print indent*2 + 'SrcScript:   %s' % binary_to_hex(self.txOutScripts[i])
         for ns, sig in enumerate(self.signatures[i]):
            print indent*2 + 'Sig%d = "%s"'%(ns, binary_to_hex(sig))
      print indent+'Num Outputs           : ', len(tx.outputs)
      for i,txout in enumerate(tx.outputs):
         print '   Recipient: %s BTC' % coin2str(txout.value),
         scrType = getTxOutScriptType(txout.binScript)
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            print hash160_to_addrStr(TxOutScriptExtractAddr160(txout.binScript))
         elif scrType in (TXOUT_SCRIPT_MULTISIG,):
            mstype, addrs, pubs = getTxOutMultiSigInfo(txout.binScript)
            print 'MULTI-SIG-SCRIPT:%d-of-%d' % mstype
            for addr in addrs:
               print indent*2, hash160_to_addrStr(addr)
            
         

# Random method for creating
def touchFile(fname):
   try:
      os.utime(fname, None)
   except:
      open(fname, 'a').close()

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



################################################################################
################################################################################
class PyBtcWallet(object):
   """
   This class encapsulates all the concepts and variables in a "wallet",
   and maintains the passphrase protection, key stretching, encryption,
   etc, required to maintain the wallet.  This class also includes the
   file I/O methods for storing and loading wallets.

   ***NOTE:  I have ONLY implemented deterministic wallets, using ECDSA
             Diffie-Hellman shared-secret crypto operations.  This allows
             on to actually determine the next PUBLIC KEY in the address
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
   binUniqueID -- (4)   first 4 bytes of first address in wallet
                        (rootAddr25Bytes[:4][::-1]
                        This is not intended to look like the root addr str
                        and is reversed to avoid leading '1' which makes
                        different IDs look too similar
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
   the walletUpdateFailed file.  THEN we let the user know that their data
   has been successfully written (or that there's a new address for them to
   use, if that's what they were requesting).

   If there is a power failure during file modification, the update_unsuccess
   file will be present and detected, and PyBtcWallet will know to use the
   original copy.  It is critical is to guarantee that atomic operations
   completes before telling the user they can use this data.

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
      self.addrPoolSize = 100

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

   #############################################################################
   def getWalletVersion(self):
      return (getVersionInt(self.version), getVersionString(self.version))

   #############################################################################
   def getWalletVersion(self):
      return (getVersionInt(self.version), getVersionString(self.version))


   #############################################################################
   def getWalletPath(self):
      return self.walletPath

   #############################################################################
   def getTimeRangeForAddress(self, addr160):
      if not self.addrMap.has_key(addr160):
         return None
      else:
          return self.addrMap[addr160].getTimeRange()

   #############################################################################
   def getBlockRangeForAddress(self, addr20):
      if not self.addrMap.has_key(addr160):
         return None
      else:
          return self.addrMap[addr160].getBlockRange()

   #############################################################################
   def setBlockchainSyncFlag(self, syncYes=True):
      self.doBlockchainSync = syncYes

   #############################################################################
   def syncWithBlockchain(self):
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         assert(TheBDM.isInitialized())
         TheBDM.scanBlockchainForTx(self.cppWallet, self.lastSyncBlockNum)
         self.lastSyncBlockNum = TheBDM.getTopBlockHeader().getBlockHeight()
      else:
         print '***WARNING: Blockchain-sync requested, but current wallet'
         print '            is set to BLOCKCHAIN_DONOTUSE'

   #############################################################################
   def getBalance(self):
      return sumTxOutList(self.getUnspentTxOutList())

   #############################################################################
   def getTxLedger(self, addr160=None):
      """ 
      Gets the complete ledger for a specific address, or the wallet as a whole.
      """
      if addr160==None:
         return self.cppWallet.getTxLedger()
      else:
         if not self.hasAddr(addr160):
            return []
         else:
            return self.cppWallet.getAddrByHash160(addr160).getTxLedger()

   #############################################################################
   def getUnspentTxOutList(self):
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         assert(TheBDM.isInitialized())
         self.syncWithBlockchain()
         return TheBDM.getUnspentTxOutsForWallet(self.cppWallet)
      else:
         print '***Blockchain is not available for accessing wallet-tx data'
         return []


   #############################################################################
   def getAddrByHash160(self, addr160):
      return (None if not self.hasAddr(addr160) else self.addrMap[addr160])

   #############################################################################
   def hasAddr(self, addrData):
      if isinstance(addrData, str):
         if len(addrData) == 20:
            return self.addrMap.has_key(addrData)
         else:
            return self.addrMap.has_key(addrStr_to_hash160(addrData))
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
         self.kdfKey.destroy()
         self.kdfKey = None
         self.isLocked = True



   #############################################################################
   def lockTxOutsOnNewTx(self, pytxObj):
      for txin in pytxObj.inputs:
         self.cppWallet.lockTxOutSwig(txin.outpoint.txHash, txin.outpoint.txOutIndex)
         
   

   #############################################################################
   def setDefaultKeyLifetime(self, lifetimeInSec):
      """
      This is used to set (in memory only) the default time to keep the encrypt
      key in memory after the encryption passphrase has been entered.  This is
      NOT enforced by PyBtcWallet, but the unlock method will use it to calc a
      unix timestamp when the wallet SHOULD be locked, and the external program
      can use that to decide when to call the lock method.
      """
      self.defaultKeyLifetime = lifetimeInSec

   #############################################################################
   def createNewWallet(self, newWalletFilePath=None, \
                             plainRootKey=None, chaincode=None, \
                             withEncrypt=True, IV=None, securePassphrase=None, \
                             kdfTargSec=DEFAULT_COMPUTE_TIME_TARGET, \
                             kdfMaxMem=DEFAULT_MAXMEM_LIMIT, \
                             shortLabel='', longLabel=''):
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
      """

      if securePassphrase:
         securePassphrase = SecureBinaryData(securePassphrase)
      if plainRootKey:
         plainRootKey = SecureBinaryData(plainRootKey)
      if chaincode:
         chaincode = SecureBinaryData(chaincode)

      if withEncrypt and not securePassphrase:
         raise EncryptionError, 'Cannot create encrypted wallet without passphrase'

      print '***Creating new deterministic wallet'

      # Set up the KDF
      if not withEncrypt:
         self.kdfKey = None
      else:
         print '(with encryption)',
         self.kdf = KdfRomix()
         print kdfTargSec, kdfMaxMem
         (mem,niter,salt) = self.computeSystemSpecificKdfParams( \
                                                kdfTargSec, kdfMaxMem)
         self.kdf.usePrecomputedKdfParams(mem, niter, salt)
         self.kdfKey = self.kdf.DeriveKey(securePassphrase)

      if not plainRootKey:
         # TODO: We should find a source for injecting extra entropy
         #       At least, Crypto++ grabs from a few different sources, itself
         plainRootKey = SecureBinaryData().GenerateRandom(32)

      if not chaincode:
         chaincode = SecureBinaryData().GenerateRandom(32)

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
      self.labelName  = shortLabel[:32]
      self.labelDescr  = longLabel[:256]
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
         newName = 'armory_%s_.wallet' % self.uniqueIDB58
         self.walletPath = os.path.join(ARMORY_HOME_DIR, newName)

      print '   New wallet will be written to:', self.walletPath
      newfile = open(self.walletPath, 'w')
      fileData = BinaryPacker()

      # packHeader method writes KDF params and root address
      headerBytes = self.packHeader(fileData)

      # We make sure we have byte locations of the two addresses, to start
      self.addrMap[first160].walletByteLoc = headerBytes + 21

      fileData.put(BINARY_CHUNK, '\x00' + first160 + firstAddr.serialize())

      firstBlk = 0
      if TheBDM.isInitialized():
         firstBlk = TheBDM.getTopBlockHeader().getBlockHeight()

      # Don't forget to sync the C++ wallet object
      self.cppWallet = Cpp.BtcWallet()

      # Temporarily disabling first/last-seen times
      self.cppWallet.addAddress_5_(rootAddr.getAddr160(), 0,0,0,0)
                                             #self.wltCreateDate, firstBlk, \
                                             #self.wltCreateDate, firstBlk)
      self.cppWallet.addAddress_5_(first160, 0,0,0,0)
                                             #self.wltCreateDate, firstBlk, \
                                             #self.wltCreateDate, firstBlk)


      newfile.write(fileData.getBinaryString())
      newfile.close()

      walletFileBackup = self.getWalletPath('backup')
      shutil.copy(self.walletPath, walletFileBackup)

      # Let's fill the address pool while we have the KDF key in memory.
      # It will get a lot more expensive if we do it 
      self.fillAddressPool(self.addrPoolSize)

      return self

   #############################################################################
   def advanceHighestIndex(self, ct=1):
      topIndex = self.highestUsedChainIndex + ct
      topIndex = min(topIndex, self.lastComputedChainIndex)
      topIndex = max(topIndex, 0)

      self.highestUsedChainIndex = topIndex
      self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, self.offsetTopUsed, \
                    int_to_binary(self.highestUsedChainIndex, widthBytes=8)]])
      
   #############################################################################
   def rewindHighestIndex(self, ct=1):
      self.advanceHighestIndex(-ct)


   #############################################################################
   def getNextUnusedAddress(self):
      if self.lastComputedChainIndex - self.highestUsedChainIndex < \
                                              max(self.addrPoolSize-1,1):
         self.fillAddressPool(self.addrPoolSize)

      self.advanceHighestIndex(1)
      new160 = self.getAddress160ByChainIndex(self.highestUsedChainIndex)
      return self.addrMap[new160]

      """
      if len(self.lastComputedChainAddr160) == 20:
         mostRecentAddr = self.addrMap[self.lastComputedChainAddr160]
         newAddr = mostRecentAddr.extendAddressChain(self.kdfKey)
         new160 = newAddr.getAddr160()
         self.linearAddr160List.append(new160)

         newDataLoc = self.walletFileSafeUpdate( \
            [[WLT_UPDATE_ADD, WLT_DATATYPE_KEYDATA, new160, newAddr]])
         self.addrMap[new160] = newAddr
         self.addrMap[new160].walletByteLoc = newDataLoc[0] + 21

         self.lastComputedChainAddr160 = new160
         self.lastComputedChainIndex = newAddr.chainIndex
         # In the future we will enable first/last seen, but not yet
         self.cppWallet.addAddress_5_(new160, 0, 0, 0, 0)
         return self.addrMap[new160]
      else:
         raise WalletAddressError, 'Deterministic wallet not initialized yet'
      """

   #############################################################################
   #def getNewUnusedAddress(self):
      


   #############################################################################
   def computeNextAddress(self, addr160=None):
      """
      Use this to extend the chain beyond the last-computed address.

      We will usually be computing the next address from the tip of the 
      chain, but I suppose someone messing with the file format may
      leave gaps in the chain requiring some to be generated in the middle
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

      # In the future we will enable first/last seen, but not yet
      self.cppWallet.addAddress_5_(new160, 0, 0, 0, 0)
      return new160
      



   #############################################################################
   def fillAddressPool(self, numPool=None):
      if not numPool:
         numPool = self.addrPoolSize

      gap = self.lastComputedChainIndex - self.highestUsedChainIndex
      numToCreate = max(numPool - gap, 0)
      for i in range(numToCreate):
         self.computeNextAddress()
      return self.lastComputedChainIndex
         
   #############################################################################
   def detectHighestUsedIndex(self, writeResultToWallet=False):
      """
      This method is used to find the highestUsedChainIndex value of the 
      wallet WITHIN its address pool.  It will NOT extend its address pool
      in this search, because it is assumed that the wallet couldn't have
      used any addresses it had not calculated yet.

      If you have a wallet IMPORT, though, of a wallet that has been used
      before but does not have this information stored with it, then you
      should be using the next method:

            self.freshImportFindHighestIndex()

      which will actually extend the address pool as necessary to find the
      highest address used.      
      """
      if not TheBDM.isInitialized():
         print 'Cannot detect any usage information without the blockchain'
         return -1

      oldSync = self.doBlockchainSync
      self.doBlockchainSync = BLOCKCHAIN_READONLY
      self.syncWithBlockchain()
      self.doBlockchainSync = oldSync

      highestIndex = 0
      for addr in self.getLinearAddrList(withAddrPool=True):
         a160 = addr.getAddr160()
         if len(self.getTxLedger(a160)) > 0:
            highestIndex = max(highestIndex, addr.chainIndex)

      if writeResultToWallet:
         self.highestUsedChainIndex = highestIndex
         self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, self.offsetTopUsed, \
                                      int_to_binary(highestIndex, widthBytes=8)]])


      return highestIndex


   #############################################################################
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
         topCompute = self.fillAddressPool(stepSize)
         topUsed = self.detectHighestUsedIndex(True)
         nWhile += 1
         if nWhile>10000:
            raise WalletAddressError, 'Escaping inf loop in freshImport...'
            

      self.addrPoolSize = oldPoolSize
      return topUsed


   #############################################################################
   def writeFreshWalletFile(self, path, newName='', newDescr=''):
      newFile = open(path, 'w')
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

      for addr160,opevalData in self.opevalMap.iteritems():
         pass

      newFile.close()
   

   #############################################################################
   def forkOnlineWallet(self, newWalletFile, shortLabel='', longLabel=''):
      """
      Make a copy of this wallet that contains no private key data
      """
      if not self.addrMap['ROOT'].hasPrivKey():
         print 'This wallet is already void of any private key data!'

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
      return (RightNow()-start)

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
         raise UnserializeError, 'Corrupted KDF params, could not fix'
      elif not fixedKdfData==allKdfData:
         self.walletFileSafeUpdate( \
               [[WLT_UPDATE_MODIFY, self.offsetKdfParams, fixedKdfData]])
         allKdfData = fixedKdfData
         print '***WARNING: KDF params in wallet were corrupted, but fixed'

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
            print ''
            print '***ERROR:  You have requested changing the key-derivation'
            print '           parameters on an already-encrypted wallet, which'
            print '           requires modifying the encryption on this wallet.'
            print '           Please unlock your wallet before attempting to'
            print '           change the KDF parameters.'
            raise WalletLockError, 'Cannot change KDF without unlocking wallet'
         elif not self.verifyPassphrase(securePassphrase):
            raise PassphraseError, 'Incorrect passphrase to unlock wallet'

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
                                    kdfObj=None):
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
            raise WalletLockError, 'Must unlock wallet to change passphrase'
         else:
            oldKdfKey = self.kdfKey.copy()


      if newUsesEncryption and not self.kdf:
         raise EncryptionError, 'KDF must be setup before encrypting wallet'

      # Prep the file-update list with extras passed in as argument
      walletUpdateInfo = list(extraFileUpdates)

      # Derive the new KDF key if a passphrase was supplied
      newKdfKey = secureKdfOutput
      if securePassphrase:
         newKdfKey = self.kdf.DeriveKey(securePassphrase)

      if oldUsedEncryption and newUsesEncryption and self.verifyEncryptionKey(newKdfKey):
         print 'Attempting to change encryption to same passphrase!'
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
         for addr160,addr in self.addrMap.iteritems():
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
            self.unlock(newKdfKey)
      finally:
         # Make sure we always destroy the temporary passphrase results
         if newKdfKey: newKdfKey.destroy()
         if oldKdfKey: oldKdfKey.destroy()



   #############################################################################
   def getWalletPath(self, nameSuffix=None):
      fpath = self.walletPath

      if self.walletPath=='':
         fpath = os.path.join(ARMORY_HOME_DIR, 'armory_%s_.wallet' % self.uniqueIDB58)

      if not nameSuffix==None:
         pieces = os.path.splitext(fpath)
         if not pieces[0].endswith('_'):
            fpath = pieces[0] + '_' + nameSuffix + pieces[1]
         else:
            fpath = pieces[0] + nameSuffix + pieces[1]
      return fpath

   #############################################################################
   def upgradeWalletVersion(self ):
      """
      This function will be called on any wallet that has a version older than
      the current PYBTCWALLET_VERSION.  It will incrementally apply version
      upgrade logic, starting at the current version.  Every time the version
      in increased, I will add another conditional to the end to further 
      the upgrade process
      """
      if self.version==PYBTCWALLET_VERSION:
         return

      if getVersionInt(self.version) < getVersionInt( (1, 35, 0, 0) ):
         print '   Upgrading from version', self.version, '...'
         firstAddr = self.addrMap['ROOT'].extendAddressChain()
         self.uniqueIDBin =  (ADDRBYTE + firstAddr.getAddr160()[:5])[::-1]
         self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)
         self.version = (1, 35, 0, 0)

      #if getVersionInt(self.version) < getVersionInt( (1, 50, 0, 0) ):
      # ...

      self.version = PYBTCWALLET_VERSION

      # Shuffle wallet files:  save new one to temp, delete old, rename new
      print self.walletPath
      oldBackupOrig = self.getWalletPath('backup')
      oldBackupSave = self.getWalletPath('oldversion_backup')

      shutil.move(self.walletPath, oldBackupSave) 
      os.remove(oldBackupOrig)

      # With the old version copied, we can overwrite the current wallet.
      # When the new 
      self.writeFreshWalletFile(self.walletPath)
      self.readWalletFile(self.walletPath)

      print '   Upgraded wallet to version', PYBTCWALLET_VERSION


   #############################################################################
   def getCommentForAddress(self, addr160):
      if self.commentsMap.has_key(addr160):
         return self.commentsMap[addr160]
      else:
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
         print binary_to_hex(hashVal)
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
   def setWalletLabels(self, lshort, llong=''):
      toWriteS = lshort.ljust( 32, '\x00')
      toWriteL = llong.ljust(256, '\x00')

      updList = []
      updList.append([WLT_UPDATE_MODIFY, self.offsetLabelName,  toWriteS])
      updList.append([WLT_UPDATE_MODIFY, self.offsetLabelDescr, toWriteL])
      self.walletFileSafeUpdate(updList)
      self.labelName = toWriteS
      self.labelDescr = toWriteL


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


   #############################################################################
   def packHeader(self, binPacker):
      if not self.addrMap['ROOT']:
         raise WalletAddressError, 'Cannot serialize uninitialzed wallet!'

      startByte = binPacker.getSize()

      binPacker.put(BINARY_CHUNK, self.fileTypeStr, width=8)
      binPacker.put(UINT32, getVersionInt(self.version))
      binPacker.put(BINARY_CHUNK, self.magicBytes,  width=4)

      # Wallet info flags
      self.offsetWltFlags = binPacker.getSize() - startByte
      self.packWalletFlags(binPacker)

      # Binary Unique ID (firstAddr25bytes[:6][::-1])
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
      if getVersionInt(self.version) >= getVersionInt((1, 10, 0, 0)):
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
         print '***ERROR:  Requested wallet is for a different blockchain!'
         print '           Wallet is for:   ', BLOCKCHAINS[self.magicBytes]
         print '           ArmoryEngine:    ', BLOCKCHAINS[MAGIC_BYTES]
         return
      if not self.uniqueIDBin[-1] == ADDRBYTE:
         print '***ERROR:  Requested wallet is for a different network!'
         print '           Wallet is for:   ', NETWORKS[netByte]
         print '           ArmoryEngine:    ', NETWORKS[ADDRBYTE]
         return

      # User-supplied description/name for wallet
      self.offsetLabelName = binUnpacker.getPosition()
      self.labelName  = binUnpacker.get(BINARY_CHUNK, 32).strip('\x00')

      # Longer user-supplied description/name for wallet
      self.offsetLabelDescr  = binUnpacker.getPosition()
      self.labelDescr  = binUnpacker.get(BINARY_CHUNK, 256).strip('\x00')

      # Highest used address: 
      print self.version
      if getVersionInt(self.version) >= getVersionInt((1, 10, 0, 0)):
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
         raise NotImplementedError, 'OP_EVAL not support in wallet yet'
      elif dtype==WLT_DATATYPE_DELETED:
         deletedLen = binUnpacker.get(UINT16)
         binUnpacker.advance(deletedLen)
         

      return (dtype, hashVal, binData)

   #############################################################################
   def readWalletFile(self, wltpath, verifyIntegrity=True, skipBlockChainScan=False):

      if not os.path.exists(wltpath):
         raise FileExistsError, "No wallet file:"+wltpath

      self.__init__()
      self.walletPath = wltpath

      if verifyIntegrity:
         try:
            nError = self.doWalletFileConsistencyCheck()
         except KeyDataError, errmsg:
            print '***ERROR:  Wallet file had unfixable errors.'
            print '***ERROR:', errmsg
            raise KeyDataError, errmsg

      print 'Reading wallet file:', self.walletPath

      wltfile = open(wltpath, 'r')
      wltdata = BinaryUnpacker(wltfile.read())
      wltfile.close()

      self.cppWallet = Cpp.BtcWallet()

      print self.walletPath
      self.unpackHeader(wltdata)

      self.lastComputedChainIndex = -UINT32_MAX
      self.lastComputedChainAddr160  = None
      while wltdata.getRemainingSize()>0:
         byteLocation = wltdata.getPosition()
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
            self.linearAddr160List.append(newAddr.getAddr160())
            self.chainIndexMap[newAddr.chainIndex] = newAddr.getAddr160()

            # Update the parallel C++ object that scans the blockchain for us
            timeRng = newAddr.getTimeRange()
            blkRng  = newAddr.getBlockRange()
            self.cppWallet.addAddress_5_(hashVal, timeRng[0], blkRng[0], \
                                                  timeRng[1], blkRng[1])
         if dtype in (WLT_DATATYPE_ADDRCOMMENT, WLT_DATATYPE_TXCOMMENT):
            self.commentsMap[hashVal] = rawData # actually ASCII data, here
            self.commentLocs[hashVal] = byteLocation
         if dtype==WLT_DATATYPE_OPEVAL:
            raise NotImplementedError, 'OP_EVAL not support in wallet yet'
         if dtype==WLT_DATATYPE_DELETED:
            pass


      if (skipBlockChainScan or \
          not TheBDM.isInitialized() or \
          self.doBlockchainSync==BLOCKCHAIN_DONOTUSE):
         pass
      else:
         self.syncWithBlockchain()


      ### Update the wallet version if necessary ###
      if getVersionInt(self.version) < getVersionInt(PYBTCWALLET_VERSION):
         if verifyIntegrity:
            print '*** UPGRADING WALLET VERSION '
            self.upgradeWalletVersion()
            print '*** UPGRADE COMPLETE!'

      return self



   #############################################################################
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
         raise FileExistsError, 'No wallet file exists to be updated!'

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
                     raise Exception, 'Data type does not match update type'
                  toAppend.put(UINT8, WLT_DATATYPE_KEYDATA)
                  toAppend.put(BINARY_CHUNK, updateInfo[1])
                  toAppend.put(BINARY_CHUNK, updateInfo[2].serialize())

               elif dtype in (WLT_DATATYPE_ADDRCOMMENT, WLT_DATATYPE_TXCOMMENT):
                  if not isinstance(updateInfo[2], str):
                     raise Exception, 'Data type does not match update type'
                  toAppend.put(UINT8, dtype)
                  toAppend.put(BINARY_CHUNK, updateInfo[1])
                  toAppend.put(UINT16, len(updateInfo[2]))
                  toAppend.put(BINARY_CHUNK, updateInfo[2])

               elif dtype==WLT_DATATYPE_OPEVAL:
                  raise Exception, 'OP_EVAL not support in wallet yet'

            elif(modType==WLT_UPDATE_MODIFY):
               updateLocations.append(updateInfo[0])
               dataToChange.append( updateInfo )
            else:
               print '***ERROR:  Unknown wallet-update type!'
               raise Exception, 'Unknown wallet-update type!'
      except Exception:
         print '***ERROR: '
         print '***ERROR:  Bad input to walletFileSafeUpdate'
         return []

      binaryToAppend = toAppend.getBinaryString()


      # We need to safely modify both the main wallet file and backup
      # Start with main wallet
      touchFile(mainUpdateFlag)

      try:
         wltfile = open(self.walletPath, 'ab')
         wltfile.write(binaryToAppend)
         wltfile.close()

         # This is for unit-testing the atomic-wallet-file-update robustness
         if self.interruptTest1: raise InterruptTestError

         wltfile = open(self.walletPath, 'r+b')
         for loc,replStr in dataToChange:
            wltfile.seek(loc)
            wltfile.write(replStr)
         wltfile.close()

      except IOError:
         print '***ERROR: could not write data to wallet.  Permissions?'
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
         backupfile.close()

         backupfile = open(walletFileBackup, 'r+b')
         for loc,replStr in dataToChange:
            backupfile.seek(loc)
            backupfile.write(replStr)
         backupfile.close()

      except IOError:
         print '***WARNING: could not write backup wallet.  Permissions?'
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
         raise FileExistsError, 'No wallet file exists to be checked!'

      walletFileBackup = self.getWalletPath('backup')
      mainUpdateFlag   = self.getWalletPath('update_unsuccessful')
      backupUpdateFlag = self.getWalletPath('backup_unsuccessful')

      if not os.path.exists(walletFileBackup):
         # We haven't even created a backup file, yet
         print 'Creating backup file', walletFileBackup
         touchFile(backupUpdateFlag)
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(backupUpdateFlag)

      if os.path.exists(backupUpdateFlag) and os.path.exists(mainUpdateFlag):
         # Here we actually have a good main file, but backup never succeeded
         print '***WARNING: error in backup file... how did that happen?'
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(mainUpdateFlag)
         os.remove(backupUpdateFlag)
      elif os.path.exists(mainUpdateFlag):
         print '***WARNING: last file operation failed!  Restoring wallet from backup'
         # main wallet file might be corrupt, copy from backup
         shutil.copy(walletFileBackup, self.walletPath)
         os.remove(mainUpdateFlag)
      elif os.path.exists(backupUpdateFlag):
         print '***WARNING: creation of backup was interrupted -- fixing'
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(backupUpdateFlag)

      if onlySyncBackup:
         return 0



      """ I have absolutely no idea if any of this works, but I do think
          it is unecessary, as I'm already handling header byte-fixes,
          in-place when reading the header.  Just need to update all the
          other addresses to self correct, too.
      # If we got here, we want to do a thorough check for byte-errors
      errorsFound = 0
      updateList = []

      wltfile = open(self.walletPath, 'r')
      wltdata = wltfile.read()
      wltfile.close()

      buRaw = BinaryUnpacker(wltdata)
      buUnpack = BinaryUnpacker(wltdata)

      # The following line sets all the offsets for us to pull original
      # data from buOrig.  Then we can compare that data to the what was
      # unserialized -- and corrected -- to check whether there was byte
      # errors (the unserializing automatically corrects byte errors,
      # but only in memory).
      self.unpackHeader(buUnpack)
      buRaw.advance(self.offsetKdfParams)
      kdfRaw = buRaw.get(BINARY_CHUNK, 256)
      kdfFixed = self.serializeKdfParams()
   

      # Check the header data for consistency of private-key-generator
      offset = self.offsetRootAddr
      self.unpackHeader(wltdata)
      binChainRoot = self.addrMap['ROOT'].serialize()
      binChainRootFixed = PyBtcAddress().unserialize(binChainRoot).serialize()

      if len(binChainRootFixed)==0:
         raise KeyDataError, 'Deterministic key generator has unfixable error!'
      elif not binChainRoot==binChainRootFixed:
         errorsFound += 1
         updateList.append([WLT_UPDATE_MODIFY, offset, binChainRootFixed])

      while wltdata.getRemainingSize() > 0:
         dtype, addr, fileAddr = self.unpackNextEntry(wltdata)
         if dtype==WLT_DATATYPE_KEYDATA:
            fixedAddr = PyBtcAddress().unserialize(fileAddr).serialize()
            if len(fixedAddr)==0:
               raise KeyDataError, 'Unfixable error in wallet for addr:' \
                                                + hash160_to_addrStr(addr)
            elif not fixedAddr==fileAddr:
               errorsFound += 1
               updateList.append( \
                     [WLT_UPDATE_MODIFY, wltdata.getPosition(), fixedAddr])

      self.walletFileSafeUpdate(updateList)
      return errorsFound
      """




   #############################################################################
   #def getAddrByIndex(self, i):
      #return self.addrMap.values()[i]

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
         raise WalletAddressError, 'You can only delete imported addresses!'

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
      self.readWalletFile(wltPath)
      

   #############################################################################
   def importExternalAddressData(self, privKey=None, privChk=None, \
                                       pubKey=None,  pubChk=None, \
                                       addr20=None,  addrChk=None, \
                                       firstTime=0,  firstBlk=0, \
                                       lastTime=0,   lastBlk=0):
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
      """

      if not privKey and not self.watchingOnly:
         print ''
         print '***ERROR:  This wallet is strictly for addresses that you'
         print '           own.  You cannot import addresses without the'
         print '           the associated private key.  Instead, use a'
         print '           watching-only wallet to import this address.'
         raise WalletAddressError, 'Cannot import non-private-key addresses'



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
         print 'This address is already in your wallet!'
         return

      if pubKey and not computedPubkey==pubKey:
         raise ECDSA_Error, 'Private and public keys to be imported do not match!'
      if addr20 and not computedAddr20==addr20:
         raise ECDSA_Error, 'Supplied address hash does not match key data!'

      addr20 = computedAddr20
      
      if self.addrMap.has_key(addr20):
         return None

      # If a private key is supplied and this wallet is encrypted&locked, then 
      # we have no way to secure the private key without unlocking the wallet.
      if self.useEncryption and self.isLocked and privKey:
         raise WalletLockError, 'Cannot import private key when wallet is locked!'


      if privKey:
         # For priv key, lots of extra encryption and verification options
         newAddr = PyBtcAddress().createFromPlainKeyData( addr160=addr20, \
                                  plainPrivKey=privKey, publicKey65=pubKey,  \
                                  willBeEncr=self.useEncryption, \
                                  generateIVIfNecessary=self.useEncryption, \
                                  skipCheck=True, skipPubCompute=True)
      elif pubKey:
         newAddr = PyBtcAddress().createFromPublicKeyData(securePubKey)
      else:
         newAddr = PyBtcAddress().createFromPublicKeyHash160(addr20)


      newAddr.chaincode  = SecureBinaryData('\xff'*32)
      newAddr.chainIndex = -2
      newAddr.timeRange = [firstTime, lastTime]
      newAddr.blkRange  = [firstBlk,  lastBlk ]
      newAddr.binInitVect16  = SecureBinaryData().GenerateRandom(16)
      newAddr160 = newAddr.getAddr160()

      newDataLoc = self.walletFileSafeUpdate( \
         [[WLT_UPDATE_ADD, WLT_DATATYPE_KEYDATA, newAddr160, newAddr]])
      self.addrMap[newAddr160] = newAddr.copy()
      self.addrMap[newAddr160].walletByteLoc = newDataLoc[0] + 21
      self.linearAddr160List.append(newAddr160)
      if self.useEncryption and self.kdfKey:
         self.addrMap[newAddr160].lock(self.kdfKey)
         if not self.isLocked:
            self.addrMap[newAddr160].unlock(self.kdfKey)

      self.cppWallet.addAddress_5_(newAddr160, \
                                       firstTime, firstBlk, lastTime, lastBlk)

      return newAddr160


   #############################################################################
   def importAddressesFromFile(self, filename, sepList=":;'[]()=-_*&^%$#@!,./?"):
      """
      Attempts to import plaintext key data stored in a file.  This method
      expects all data to be in hex or Base58:

         20 bytes / 40  hex chars -- public key hashes
         25 bytes / 50  hex chars -- full binary addresses
         65 bytes / 130 hex chars -- public key
         32 bytes / 64  hex chars -- private key

         33 or 34 Base58 chars    -- address strings
         50 to 52 Base58 chars    -- base58-encoded private key

      Since this is python, I don't have to require any particular format:
      I can pretty easily break apart the entire file into individual strings,
      search for addresses and public keys, then, search for private keys that
      correspond to that data.  Obviously, simpler is better, but as long as
      the data is encoded as in the above list and separated by whitespace or
      punctuation, this method should succeed.

      We must throw an error if this is NOT a watching-only address and we
      find an address without a private key.  We will need to create a
      separate watching-only wallet in order to import these keys.

      TODO: will finish this later
      """
      """
      self.__init__()
      self.watchingOnly = True

      newfile = open(filename,'r')
      newdata = newfile.read()
      newfile.close()

      # Change all punctuation to the same char so split() works easier
      for ch in sepList:
         newdata.replace(ch, ' ')

      allPieces = newdata.split()
      for piece in allPieces:
         if len(piece)==64:
            potentialKey = SecureBinaryData('\x04' + piece)
            isValid = CryptoECDSA().VerifyPublicKeyValid(potentialKey)

      return self
      """






   #############################################################################
   def signTxDistProposal(self, txdp, hashcode=1):
      if not hashcode==1:
         print '***ERROR: hashcode!=1 is not supported at this time!'
         return

      # If the wallet is locked, we better bail now
      if self.isLocked:
         raise WalletLockError, "Cannot sign Tx when wallet is locked!"

      numInputs = len(txdp.pytxObj.inputs)
      wltAddr = []
      #amtToSign = 0  # I can't get this without asking blockchain for txout vals
      for index,txin in enumerate(txdp.pytxObj.inputs):
         scriptType = getTxOutScriptType(txin.binScript)
         
         if scriptType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            addr160 = TxOutScriptExtractAddr160(txin.getScript())
            if self.hasAddr(addr160) and self.addrMap[addr160].hasPrivKey():
               wltAddr.append( (self.addrMap[addr160], index, 0))
         elif scriptType==TXOUT_SCRIPT_MULTISIG:
            # Basically the same check but multiple addresses to consider
            addrList = getTxOutMultiSigInfo(txin.getScript())[1]
            for addrIdx, addr in enumerate(addrList):
               if self.hasAddr(addr) and self.addrMap[addr].hasPrivKey():
                  wltAddr.append( (self.addrMap[addr], index, addrIdx) )
                  break
                  

      # WltAddr now contains a list of every input we can sign for, and the
      # PyBtcAddress object that can be used to sign it.  Let's do it.
      numMyAddr = len(wltAddr)
      print 'Total number of inputs in transaction:  ', numInputs
      print 'Number of inputs that you can sign for: ', numMyAddr


      # The TxOut script is already in the TxIn script location, correctly
      # But we still need to blank out all other scripts when signing
      for addrObj,idx, sigIdx in wltAddr:
         if addrObj.isLocked:
            if self.kdfKey:
               addrObj.unlock(self.kdfKey)
            else:
               raise WalletLockError, 'Cannot sign tx without unlocking wallet'

         if not addrObj.hasPubKey():
            # Make sure the public key is available for this address
            addrObj.binPublicKey65 = CryptoECDSA().ComputePublicKey(addrObj.binPrivKey32_Plain)

         # Copy the script, blank out out all other scripts (assume hashcode==1)
         txCopy = PyTx().unserialize(txdp.pytxObj.serialize())
         for i in range(len(txCopy.inputs)):
            if not i==idx:
               txCopy.inputs[i].binScript = ''

         hashCode1  = int_to_binary(hashcode, widthBytes=1)
         hashCode4  = int_to_binary(hashcode, widthBytes=4)
         preHashMsg = txCopy.serialize() + hashCode4
         signature  = addrObj.generateDERSignature(preHashMsg) + hashCode1

         # Now we attach a binary signature or full script, depending on the type
         if txdp.scriptTypes[idx]==TXOUT_SCRIPT_COINBASE:
            # Only need the signature to complete coinbase TxOut
            sigLenInBinary = int_to_binary(len(signature))
            txdp.signatures[idx][0] = sigLenInBinary + signature
         elif txdp.scriptTypes[idx]==TXOUT_SCRIPT_STANDARD:
            # Gotta include the public key, too, for standard TxOuts
            pubkey = addrObj.binPublicKey65.toBinStr()
            sigLenInBinary    = int_to_binary(len(signature))
            pubkeyLenInBinary = int_to_binary(len(pubkey)   )
            txdp.signatures[idx][0] = sigLenInBinary    + signature + \
                                      pubkeyLenInBinary + pubkey
         elif txdp.scriptTypes[idx]==TXOUT_SCRIPT_MULTISIG:
            # We attach just the sig for multi-sig transactions
            sigLenInBinary = int_to_binary(len(signature))
            txdp.signatures[idx][sigIdx] = (sigLenInBinary + signature)
         else:
            print '***WARNING: unknown txOut script type'

      return txdp



   #############################################################################
   def unlock(self, secureKdfOutput=None, \
                    securePassphrase=None, \
                    tempKeyLifetime=0):
      """
      We must assume that the kdfResultKey is a SecureBinaryData object
      containing the result of the KDF-passphrase.  The wallet unlocked-
      lifetime will be set to X seconds from time.time() [now] and next
      time the checkWalletLockTimeout function is called it will be re-
      locked.
      """
      
      if not secureKdfOutput and not securePassphrase:
         raise PassphraseError, "No passphrase/key provided to unlock wallet!"
         
      if not secureKdfOutput:
         if not self.kdf:
            raise EncryptionError, 'How do we have a locked wallet w/o KDF???'
         secureKdfOutput = self.kdf.DeriveKey(securePassphrase)


      if not self.verifyEncryptionKey(secureKdfOutput):
         raise PassphraseError, "Incorrect passphrase for wallet"

      # For now, I assume that all keys have the same passphrase and all
      # unlocked successfully at the same time.
      # It's an awful lot of work to design a wallet to consider partially-
      # successful unlockings.
      self.kdfKey = secureKdfOutput
      if tempKeyLifetime==0:
         self.lockWalletAtTime = RightNow() + self.defaultKeyLifetime
      else:
         self.lockWalletAtTime = RightNow() + tempKeyLifetime

      for addrObj in self.addrMap.values():
         addrObj.unlock(self.kdfKey)

      self.isLocked = False


   #############################################################################
   def lock(self):
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
      try:
         for addr160,addrObj in self.addrMap.iteritems():
            self.addrMap[addr160].lock(self.kdfKey)

         if self.kdfKey:
            self.kdfKey.destroy()
            self.kdfKey = None
         self.isLocked = True
      except WalletLockError:
         print '***ERROR: Locking wallet requires encryption key.  This error'
         print '          Usually occurs on newly-encrypted wallets that have'
         print '          never been encrypted before.'
         raise WalletLockError, 'Unlock with passphrase before locking again'

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
         raise WalletAddressError, 'Chain index is out of range'
         

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
            extend160 = computeNextAddress(extend160)
            if desiredIdx==self.addrMap[extend160].chainIndex:
               return self.chainIndexMap[desiredIdx]


   #############################################################################
   def pprint(self, indent='', allAddrInfo=True):
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




"""
class PyLedgerEntry(object):
   def __init__(self):
      self.addr20       = UNINITIALIZED
      self.value        = UNINITIALIZED
      self.blockNum     = UNINITIALIZED
      self.txHash       = UNINITIALIZED
      self.index        = UNINITIALIZED
      self.isValid      = UNINITIALIZED
      self.isSentToSelf = UNINITIALIZED
      self.isChangeBack = UNINITIALIZED

   def createForWalletFromTx(self, wlt, tx):
      numIn  = len(tx.inputs)
      numOut = len(tx.outputs)

      

   //    addr20_    -  useless - originally had a purpose, but lost it
   //    value_     -  total debit/credit on WALLET balance, in Satoshis (1e-8 BTC)
   //    blockNum_  -  block height of the block in which this tx was included
   //    txHash_    -  hash of this tx 
   //    index_     -  index of the tx in the block
   //    isValid_   -  default to true -- invalidated due to reorg/double-spend
   //    isSentToSelf_ - if we supplied inputs and rx ALL outputs
   //    isChangeBack_ - if we supplied inputs and rx ANY outputs
"""




###############################################################################
###############################################################################
# 
#  Networking Objects
# 
###############################################################################
###############################################################################

def quad_to_str( addrQuad):
   return '.'.join([str(a) for a in addrQuad])

def quad_to_binary( addrQuad):
   return ''.join([chr(a) for a in addrQuad])

def binary_to_quad(addrBin):
   return [ord(a) for a in addrBin]

def str_to_quad(addrBin):
   return [int(a) for a in addrBin.split('.')]

def str_to_binary(addrBin):
   """ I should come up with a better name for this -- it's net-addr only """
   return ''.join([chr(int(a)) for a in addrBin.split('.')])

def parseNetAddress(addrObj):
   if isinstance(addrObj, str):
      if len(addrObj)==4:
         return binary_to_quad(addrObj)
      else:
         return str_to_quad(addrObj)
   # Probably already in the right form
   return addrObj



MSG_INV_ERROR = 0
MSG_INV_TX    = 1
MSG_INV_BLOCK = 2


################################################################################
class PyMessage(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """
   def __init__(self, cmd='', payload=None):
      """
      Can create a message by the command name, or the payload (or neither)
      """
      self.magic   = MAGIC_BYTES
      self.cmd     = cmd
      self.payload = payload

      if payload:
         self.cmd = payload.command
      elif cmd:
         self.payload = PayloadMap[self.cmd]()



   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.magic,                    width= 4)
      bp.put(BINARY_CHUNK, self.cmd.ljust(12, '\x00'),    width=12)
      payloadBin = self.payload.serialize()
      bp.put(UINT32, len(payloadBin))
      if not self.cmd=='version' and not self.cmd=='verack':
         bp.put(BINARY_CHUNK, hash256(payloadBin)[:4],     width= 4)
      bp.put(BINARY_CHUNK, payloadBin)
      return bp.getBinaryString()
    
   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         msgData = toUnpack
      else:
         msgData = BinaryUnpacker( toUnpack )


      self.magic = msgData.get(BINARY_CHUNK, 4)
      self.cmd   = msgData.get(BINARY_CHUNK, 12).strip('\x00')
      length     = msgData.get(UINT32)
      if not self.cmd=='version' and not self.cmd=='verack':
         chksum  = msgData.get(BINARY_CHUNK, 4)
      payload    = msgData.get(BINARY_CHUNK, length)
      if not self.cmd=='version' and not self.cmd=='verack':
         payload    = verifyChecksum(payload, chksum)

      self.payload = PayloadMap[self.cmd]().unserialize(payload)

      if self.magic != MAGIC_BYTES:
         raise NetworkIDError, 'Message has wrong network bytes!'
      return self


   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Bitcoin-Network-Message -- ' + self.cmd.upper()
      print indstr + indent + 'Magic:   ' + binary_to_hex(self.magic)
      print indstr + indent + 'Command: ' + self.cmd
      print indstr + indent + 'Payload: ' + str(len(self.payload.serialize())) + ' bytes'
      self.payload.pprint(nIndent+1)


################################################################################
class PyNetAddress(object):

   def __init__(self, time=-1, svcs='0'*16, netaddrObj=[], port=-1):
      """
      For our client we will ALWAYS use svcs=0 (NODE_NETWORK=0)

      time     is stored as a unix timestamp
      services is stored as a bitset -- a string of 16 '0's or '1's
      addrObj  is stored as a list/tuple of four UINT8s
      port     is a regular old port number...
      """
      self.time     = time
      self.services = svcs
      self.addrQuad = parseNetAddress(netaddrObj)
      self.port     = port

   def unserialize(self, toUnpack, hasTimeField=True):
      if isinstance(toUnpack, BinaryUnpacker):
         addrData = toUnpack
      else:
         addrData = BinaryUnpacker( toUnpack )

      if hasTimeField:
         self.time     = addrData.get(UINT32)

      self.services = addrData.get(UINT64)
      self.addrQuad = addrData.get(BINARY_CHUNK,16)[-4:]
      self.port     = addrData.get(UINT16, endianness=NETWORKENDIAN)

      self.services = int_to_bitset(self.services)
      self.addrQuad = binary_to_quad(self.addrQuad)
      return self

   def serialize(self, withTimeField=True):
      bp = BinaryPacker()
      if withTimeField:
         bp.put(UINT32,       self.time)
      bp.put(UINT64,       bitset_to_int(self.services))
      bp.put(BINARY_CHUNK, quad_to_binary(self.addrQuad).rjust(16,'\x00'))
      bp.put(UINT16,       self.port, endianness=NETWORKENDIAN)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Network-Address:',
      print indstr + indent + 'Time:  ' + unixTimeToFormatStr(self.time)
      print indstr + indent + 'Svcs:  ' + self.services
      print indstr + indent + 'IPv4:  ' + quad_to_str(self.addrQuad)
      print indstr + indent + 'Port:  ' + self.port

   def pprintShort(self):
      print quad_to_str(self.addrQuad) + ':' + str(self.port)

################################################################################
################################################################################
class PayloadAddr(object):

   command = 'addr'
   
   def __init__(self, addrList=[]):
      self.addrList   = addrList  # PyNetAddress objs

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         addrData = toUnpack
      else:
         addrData = BinaryUnpacker( toUnpack )

      self.addrList = []
      naddr = addrData.get(VAR_INT)
      for i in range(naddr):
         self.addrList.append( PyNetAddress().unserialize(addrData) )
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, len(self.addrList))
      for netaddr in self.addrList:
         bp.put(BINARY_CHUNK, netaddr.serialize(), width=30)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(addr):',
      for a in self.addrList:
         a.pprintShort()

   def pprintShort(self):
      for a in self.addrList:
         print '[' + quad_to_str(a.pprintShort()) + '], '

################################################################################
################################################################################
class PayloadPing(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """
   command = 'ping'

   def __init__(self):
      pass

   def unserialize(self, toUnpack):
      return self

   def serialize(self):
      return ''

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(ping)'

      

################################################################################
################################################################################
class PayloadVersion(object):

   command = 'version'

   def __init__(self, version=0, svcs='0'*16, tstamp=-1, addrRcv=PyNetAddress(), \
                      addrFrm=PyNetAddress(), nonce=-1, sub=-1, height=-1):
      self.version  = version
      self.services = svcs
      self.time     = tstamp
      self.addrRecv = addrRcv
      self.addrFrom = addrFrm
      self.nonce    = nonce
      self.subver   = sub
      self.height0  = height

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         verData = toUnpack
      else:
         verData = BinaryUnpacker( toUnpack )

      self.version  = verData.get(INT32)
      self.services = int_to_bitset(verData.get(UINT64), widthBytes=8)
      self.time     = verData.get(INT64)
      self.addrRecv = PyNetAddress().unserialize(verData, hasTimeField=False)
      self.addrFrom = PyNetAddress().unserialize(verData, hasTimeField=False)
      self.nonce    = verData.get(UINT64)
      self.subver   = verData.get(VAR_STR)
      self.height0  = verData.get(INT32)
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(INT32,   self.version )
      bp.put(UINT64,  bitset_to_int(self.services))
      bp.put(INT64,   self.time    )  # todo, should this really be int64?
      bp.put(BINARY_CHUNK, self.addrRecv.serialize(withTimeField=False))
      bp.put(BINARY_CHUNK, self.addrFrom.serialize(withTimeField=False))
      bp.put(UINT64,  self.nonce   )
      bp.put(VAR_STR, self.subver  )
      bp.put(INT32,   self.height0 )
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(version):'
      print indstr + indent + 'Version:  ' + str(self.version)
      print indstr + indent + 'Services: ' + self.services
      print indstr + indent + 'Time:     ' + unixTimeToFormatStr(self.time)
      print indstr + indent + 'AddrTo:  ',;  self.addrRecv.pprintShort()
      print indstr + indent + 'AddrFrom:',;  self.addrFrom.pprintShort()
      print indstr + indent + 'Nonce:    ' + str(self.nonce)
      print indstr + indent + 'SubVer:  ',   self.subver
      print indstr + indent + 'StartHgt: ' + str(self.height0)

################################################################################
class PayloadVerack(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """

   command = 'verack'

   def __init__(self):
      pass

   def unserialize(self, toUnpack):
      return self

   def serialize(self):
      return ''

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(verack)'


################################################################################
################################################################################
class PayloadInv(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """

   command = 'inv'

   def __init__(self):
      self.invList = []  # list of (type, hash) pairs

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         invData = toUnpack
      else:
         invData = BinaryUnpacker( toUnpack )

      numInv = invData.get(VAR_INT)
      for i in range(numInv):
         invType = invData.get(UINT32)
         invHash = invData.get(BINARY_CHUNK, 32)
         self.invList.append( [invType, invHash] )
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, len(self.invList))
      for inv in self.invList:
         bp.put(UINT32, inv[0])
         bp.put(BINARY_CHUNK, inv[1], width=32)
      return bp.getBinaryString()
      

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(inv):'
      for inv in self.invList:
         print indstr + indent + ('BLOCK: ' if inv[0]==2 else 'TX   : ') + \
                                 binary_to_hex(inv[1])



################################################################################
################################################################################
class PayloadGetData(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """

   command = 'getdata'

   def __init__(self, invList=[]):
      if invList:
         self.invList = invList
      else:
         self.invList = []
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         invData = toUnpack
      else:
         invData = BinaryUnpacker( toUnpack )

      numInv = invData.get(VAR_INT)
      for i in range(numInv):
         invType = invData.get(UINT32)
         invHash = invData.get(BINARY_CHUNK, 32)
         self.invList.append( [invType, invHash] )
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, len(self.invList))
      for inv in self.invList:
         bp.put(UINT32, inv[0])
         bp.put(BINARY_CHUNK, inv[1], width=32)
      return bp.getBinaryString()
      

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getdata):'
      for inv in self.invList:
         print indstr + indent + ('BLOCK: ' if inv[0]==2 else 'TX   : ') + \
                                 binary_to_hex(inv[1])
      

################################################################################
################################################################################
class PayloadGetHeaders(object):
   command = 'getheaders'

   def __init__(self, startCt=-1, hashStartList=[], hashStop=''):
      self.startCount = startCt
      self.hashStart  = hashStartList
      self.hashStop   = hashStop
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         ghData = toUnpack
      else:
         ghData = BinaryUnpacker( toUnpack )

      self.startCount = ghData.get(VAR_INT)
      for i in range(self.startCount):
         self.hashStart.append(ghData.get(BINARY_CHUNK, 32))
      self.hashStop = ghData.get(BINARY_CHUNK, 32)
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, self.startCount)
      for i in range(self.startCount):
         bp.put(BINARY_CHUNK, self.hashStart[i], width=32)
      bp.put(BINARY_CHUNK, self.hashStop, width=32)
      return bp.getBinaryString()
   
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getheaders):'
      print indstr + indent + 'HashStart(s) :' + binary_to_hex(self.hashStart[0])
      for i in range(1,len(self.hashStart)):
         print indstr + indent + '             :' + binary_to_hex(self.hashStart[i])
      print indstr + indent + 'HashStop     :' + binary_to_hex(self.hashStop)
         


################################################################################
################################################################################
class PayloadGetBlocks(object):
   command = 'getblocks'

   def __init__(self, version=1, startCt=-1, hashStartList=[], hashStop=''):
      self.version    = 1
      self.startCount = startCt
      self.hashStart  = hashStartList
      self.hashStop   = hashStop
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         gbData = toUnpack
      else:
         gbData = BinaryUnpacker( toUnpack )

      self.version = gbData.get(UINT32)
      self.startCount = gbData.get(VAR_INT)
      for i in range(self.startCount):
         self.hashStart.append(gbData.get(BINARY_CHUNK, 32))
      self.hashStop = gbData.get(BINARY_CHUNK, 32)
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(UINT32, self.version)
      bp.put(VAR_INT, self.startCount)
      for i in range(self.startCount):
         bp.put(BINARY_CHUNK,  self.hashStart[i], width=32)
      bp.put(BINARY_CHUNK, self.hashStart, width=32)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getheaders):'
      print indstr + indent + 'Version      :' + str(self.version)
      print indstr + indent + 'HashStart(s) :' + binary_to_hex(self.hashStart[0])
      for i in range(1,len(self.hashStart)):
         print indstr + indent + '             :' + binary_to_hex(self.hashStart[i])
      print indstr + indent + 'HashStop     :' + binary_to_hex(self.hashStop)


################################################################################
################################################################################
class PayloadTx(object):
   command = 'tx'

   def __init__(self, tx=PyTx()):
      self.tx = tx

   def unserialize(self, toUnpack):
      self.tx.unserialize(toUnpack)
      return self

   def serialize(self):
      return self.tx.serialize()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(tx):'
      self.tx.pprint(nIndent+1)



################################################################################
################################################################################
class PayloadBlock(object):
   command = 'block'

   def __init__(self, header=PyBlockHeader(), txlist=[]):
      self.header = header
      self.txList = txlist
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack
      else:
         blkData = BinaryUnpacker( toUnpack )

      self.txList = []
      self.header.unserialize(blkData)
      numTx = blkData.get(VAR_INT)
      for i in range(numTx):
         self.txList.append(PyTx().unserialize(blkData))
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.header.serialize())
      bp.put(VAR_INT, len(self.txList))
      for tx in self.txList:
         bp.put(BINARY_CHUNK, tx.serialize())
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(block):'
      self.header.pprint(nIndent+1)
      for tx in self.txList:
         print indstr + indent + 'Tx:', tx.getHashHex()


################################################################################
class PayloadAlert(object):
   command = 'alert'

   def __init__(self):
      self.version = 1
      self.relayUntil = 0
      self.expiration = 0
      self.uniqueID   = 0
      self.cancelVal  = 0
      self.cancelSet  = []
      self.minVersion = 0
      self.maxVersion = 0
      self.subVerSet  = []
      self.comment    = ''
      self.statusBar  = ''
      self.reserved   = ''
      self.signature   = ''
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack
      else:
         blkData = BinaryUnpacker( toUnpack )

      return self

   def serialize(self):
      bp = BinaryPacker()
      return bp.getBinaryString()


################################################################################
# Use this map to figure out which object to serialize/unserialize from a cmd
PayloadMap = {
   'ping':        PayloadPing,
   'tx':          PayloadTx,
   'inv':         PayloadInv,
   'version':     PayloadVersion,
   'verack':      PayloadVerack,
   'addr':        PayloadAddr,
   'getdata':     PayloadGetData,
   'getheaders':  PayloadGetHeaders,
   'getblocks':   PayloadGetBlocks,
   'block':       PayloadBlock,
   'alert':       PayloadAlert }





try:
   from twisted.internet.protocol import Protocol, ClientFactory
   from twisted.internet.defer import Deferred
except ImportError:
   print '***Python-Twisted is not installed -- cannot enable'
   print '   networking-related methods for ArmoryEngine' 


################################################################################
def forceDeferred(callbk):
   if callbk:
      if isinstance(callbk, Deferred):
         return callbk
      else:
         d = Deferred()
         d.addCallback(callbk)


################################################################################
#
# Armory Networking:
# 
#    This is where I will define all the network operations needed for 
#    Armory to operate, using python-twisted.  There are "better"
#    ways to do this with "reusable" code structures (i.e. using huge
#    deferred callback chains), but this is not the central "creative" 
#    part of the Bitcoin protocol.  I need just enough to broadcast tx
#    and receive new tx that aren't in the blockchain yet.  Beyond that,
#    I'll just be ignoring everything else.
#
################################################################################
class ArmoryClient(Protocol):
   """
   This is where all the Bitcoin-specific networking stuff goes.
   In the Twisted way, you need to inject your own chains of 
   callbacks through the factory in order to get this class to do
   the right thing on the various events.
   """

   ############################################################
   def __init__(self):
      self.recvData = ''
      self.handshakeFinished = False
      self.peer = []

   ############################################################
   def connectionMade(self):
      """
      Construct the initial version message and send it right away.
      Everything else will be handled by dataReceived.
      """
      addrTo   = str_to_quad(self.transport.getPeer().host)
      portTo   =             self.transport.getPeer().port
      addrFrom = str_to_quad(self.transport.getHost().host)
      portFrom =             self.transport.getHost().port

      self.peer = [addrTo, portTo]

      services = '0'*16
      msgVersion = PayloadVersion()
      msgVersion.version  = 40000   # TODO: this is what my Satoshi client says
      msgVersion.services = services
      msgVersion.time     = long(RightNow())
      msgVersion.addrRecv = PyNetAddress(0, services, addrTo,   portTo  )
      msgVersion.addrFrom = PyNetAddress(0, services, addrFrom, portFrom)
      msgVersion.nonce    = random.randint(2**60, 2**64-1)
      msgVersion.subver   = ''
      msgVersion.height0  = -1
      self.sendMessage( msgVersion )
      
   ############################################################
   def dataReceived(self, data):
      """
      Called by the reactor when data is received over the connection. 
      This method will do nothing if we don't receive a full message.
      """

      #print '\n\nData Received:',
      # Put the current buffer into an unpacker, process until empty
      self.recvData += data
      buf = BinaryUnpacker(self.recvData)

      messages = []
      while True:
         try:
            # recvData is only modified if the unserialize succeeds
            messages.append( PyMessage().unserialize(buf) )
            self.recvData = buf.getRemainingString()
            #print '\n  Message', len(messages), 'read: ',
            #print messages[-1].cmd.upper(),
         except NetworkIDError:
            print 'Message for a different network!' 
            if BLOCKCHAINS.has_key(self.recvData[:4]):
               print '(for network:', BLOCKCHAINS[self.recvData[:4]], ')'
            # Before raising the error, we should've finished reading the msg
            # So pop it off the front of the buffer
            self.recvData = buf.getRemainingString()
            return
         except UnpackerError:
            # Expect this error when buffer isn't full enough for a whole msg
            break

      # We might've gotten here without anything to process -- if so, bail
      if len(messages)==0:
         return

      # Finally, we have some message to process, let's do it
      for msg in messages:
         cmd = msg.cmd
         print '\nBuffer: '
         pprintHex(binary_to_hex(data), indent=' '*6)

         # We process version and verackk regardless of handshakeFinished
         if cmd=='version' and not self.handshakeFinished:
            if msg.payload.version >= 209:
               self.sendMessage( PayloadVerack() )
         elif cmd=='verack':
            self.handshakeFinished = True
            self.factory.handshakeFinished(self)

         ####################################################################
         # Don't process any other messages unless the handshake is finished
         if self.handshakeFinished:
            self.processMessage(msg)


   ############################################################
   def connectionLost(self, reason):
      """
      Try to reopen connection (not impl yet)
      """
      self.factory.connectionFailed(self, reason)


   ############################################################
   def processMessage(self, msg):
      # TODO:  when I start expanding this class to be more versatile,
      #        I'll consider chaining/setting callbacks from the calling
      #        application.  For now, it's pretty static.
      msg.payload.pprint(nIndent=2)
      if msg.cmd=='inv':
         #print 'Received inv message'
         invobj = msg.payload
         getdataMsg = PyMessage('getdata')
         for inv in invobj.invList:
            if inv[0]==MSG_INV_BLOCK:
               # We'll hear about the new block via blk0001.dat... and when
               # we do (within 5s), we should purge the zero-conf tx list
               from twisted.internet import reactor
               reactor.callLater(2, self.factory.purgeMemoryPool)
            if inv[0]==MSG_INV_TX    and not TheBDM.getTxByHash(inv[1]):
               #print 'Requesting new tx data'
               getdataMsg.payload.invList.append(inv)
         self.sendMessage(getdataMsg)
      if msg.cmd=='tx':
         #print 'Received tx message'
         pytx = msg.payload.tx
         newAlert = self.factory.checkForDoubleBroadcast(pytx)
         if newAlert:
            print '***!!!*** DOUBLE-BROADCAST DETECTED!'
            print '***!!!*** The person who just send you money may be'
            print '***!!!*** Attempting to defraud you.  It is especially'
            print '***!!!*** important that you wait for 6+ confirmations'
            print '***!!!*** before considering this transaction valid!'
         else:
            self.factory.addTxToMemoryPool(pytx)
            self.factory.saveMemoryPool()
            self.factory.func_newTx(pytx)
      if msg.cmd=='block':
         # We don't care much about blocks right now --  We will find
         # out about them when the Satoshi client updates blk0001.dat
         #print 'Received block message (ignoring)'
         from twisted.internet import reactor
         reactor.callLater(2, self.factory.purgeMemoryPool)
                  

   ############################################################
   def sendMessage(self, msg):
      """
      Must pass in a PyMessage, or one of the Payload<X> types, which
      will be converted to a PyMessage -- and then sent to the peer.
      If you have a fully-serialized message (with header) already,
      easy enough to user PyMessage().unserialize(binMsg)
      """
      if isinstance(msg, PyMessage):
         #print '\n\nSending Message:', msg.payload.command.upper()
         #pprintHex(binary_to_hex(msg.serialize()), indent='   ')
         self.transport.write(msg.serialize())
      else:
         msg = PyMessage(payload=msg)
         #print '\n\nSending Message:', msg.payload.command.upper()
         #pprintHex(binary_to_hex(msg.serialize()), indent='   ')
         self.transport.write(msg.serialize())


   ############################################################
   def sendTx(self, txObj):
      """
      This is a convenience method for the special case of sending
      a locally-constructed transaction.  Pass in either a PyTx 
      object, or a binary serialized tx.  It will be converted to
      a PyMessage and forwarded to our peer(s)
      """
      if   isinstance(txObj, PyMessage):
         self.sendMessage( txObj )
      elif isinstance(txObj, PyTx):
         self.sendMessage( PayloadTx(txObj))
      elif isinstance(txObj, str):
         self.sendMessage( PayloadTx(PyTx().unserialize(txObj)) )
         




   


################################################################################
################################################################################
class ArmoryClientFactory(ClientFactory):
   """
   Spawns Protocol objects used for communicating over the socket.  All such
   objects (ArmoryClients) can share information through this factory.
   However, at the moment, this class is designed to only create a single 
   connection -- to localhost.

   Note that I am implementing a special security feature:  besides collecting
   tx's not in the blockchain yet, I also monitor for double-broadcast events
   which are due to two transactions being sent at the same time with different
   recipients but the same inputs.  
   """
   protocol = ArmoryClient
   zeroConfTx = {}
   zeroConfTxTime = {}
   zeroConfTxOutMap = {}       #   map[OutPoint] = txHash
   doubleBroadcastAlerts = {}  #   map[Addr160]  = txHash
   lastAlert = 0

   #############################################################################
   def __init__(self, \
                def_handshake=None, \
                func_loseConnect=None, \
                func_newTx=None, \
                func_doubleSpendAlert=None):
      """
      Initialize the ClientFactory with a deferred for when the handshake 
      finishes:  there should be only one handshake, and thus one firing 
      of the handshake-finished callback
      """
      self.zeroConfTx = {}
      self.zeroConfTxOutMap = {}
      self.doubleBroadcastAlerts = {}
      self.lastAlert = 0
      self.deferred_handshake   = forceDeferred(def_handshake)
      self.fileMemPool = os.path.join(ARMORY_HOME_DIR, 'mempool.bin')

      # All other methods will be regular callbacks:  we plan to have a very
      # static set of behaviors for each message type
      # (NOTE:  The logic for what I need right now is so simple, that
      #         I finished implementing it in a few lines of code.  When I
      #         need to expand the versatility of this class, I'll start 
      #         doing more OOP/deferreds/etc
      self.func_loseConnect = func_loseConnect
      self.func_doubleSpendAlert = func_doubleSpendAlert
      self.func_newTx = func_newTx

      self.proto = None

   
   #############################################################################
   def saveMemoryPool(self, fname=None):
      if fname==None:
         fname = self.fileMemPool
      outfile = open(fname,'w')
      for hsh,tx in self.zeroConfTx.iteritems():
         outfile.write(int_to_binary(int(self.zeroConfTxTime[hsh]), widthBytes=8))
         outfile.write(tx.serialize())
      outfile.close()
   


   #############################################################################
   def loadMemoryPool(self, fname=None):
      if fname==None:
         fname = self.fileMemPool
      if not os.path.exists(fname):
         print '***WARNING: No memory pool file... assuming empty' 
         return

      outfile = open(fname,'r')
      binunpack = BinaryUnpacker(outfile.read())
      outfile.close()
      
      try:
         while binunpack.getRemainingSize() > 0:
            txtime = binunpack.get(UINT64)
            tx = PyTx().unserialize(binunpack)
            self.zeroConfTxTime[tx.getHash()] = txtime
            self.zeroConfTx[tx.getHash()] = tx 
      except:
         print '***WARNING: error reading memory pool... remaining will be skipped'
         pass
      

   #############################################################################
   def addTxToMemoryPool(self, pytx):
      self.zeroConfTx[pytx.getHash()] = pytx.copy()
      self.zeroConfTxTime[pytx.getHash()] = RightNow()
      


   #############################################################################
   def handshakeFinished(self, protoObj):
      print 'Handshake finished, connection open!'
      self.proto = protoObj
      if self.deferred_handshake:
         d, self.deferred_handshake = self.deferred_handshake, None
         d.callback(protoObj)


   #############################################################################
   def purgeMemoryPool(self):
      #print 'Purging the memory pool'
      if not TheBDM.isInitialized():
         return

      #print 'Memory pool to be cleaned  :', len(self.zeroConfTx), 'tx left:'
      # Check for tx that used to be zero-conf, but are now in blockchain
      txHashToRm = []
      txHashToRmDBD = []
      for hsh,tx in self.zeroConfTx.iteritems():
         if TheBDM.getTxByHash(hsh):
            txHashToRm.append(hsh)
            # We also need to clean up the double-broadcast detector
            for key,val in self.zeroConfTxOutMap.iteritems():
               if hsh==val:
                  txHashToRmDBD.append(key)

      for hsh in txHashToRm:
         del self.zeroConfTx[hsh]
         del self.zeroConfTxTime[hsh]

      for key in txHashToRmDBD:
         del self.zeroConfTxOutMap[key]

      if RightNow() > self.lastAlert + 2*HOUR:
         # Clear out alerts after 2 hours
         self.doubleBroadcastAlerts = {} 
      
      #print 'Memory pool should be clean:', len(self.zeroConfTx), 'tx left:'
      #for hsh,tx in self.zeroConfTx.iteritems():
         #print '   Tx:', tx.getHashHex()

      self.saveMemoryPool()


   #############################################################################
   def checkForDoubleBroadcast(self, pytxObj):
      newAlerts = False
      for txin in pytxObj.inputs:
         op = (txin.outpoint.txHash, txin.outpoint.txOutIndex)
         if self.zeroConfTxOutMap.has_key(op):
            # !!! Someone tried to spend the same inputs twice !!!
            newAlerts = True
            self.lastAlert = RightNow()
            prevHash = self.zeroConfTxOutMap[op]
            prevTx = zeroConfTx[prevHash]
            for tx in (pytxObj, prevTx):
               # Add all recipients from both transactions
               for txout in tx.outputs:
                  # Search all the TxOuts for recipients
                  addr = TxOutScriptExtractAddr160(txout.binScript)
                  if isinstance(addrs, list):
                     for addr in addrs:
                        self.doubleBroadcastAlerts[addr] = tx.getHash()
                  else:
                     self.doubleBroadcastAlerts[addrs] = tx.getHash()

      if self.func_doubleSpendAlert:
         self.func_doubleSpendAlert()


   #############################################################################
   def connectionFailed(self, protoObj, reason):
      """
      This method needs some serious work... I don't quite know yet how
      to reopen the connection... and I'll need to copy the Deferred so
      that it is ready for the next connection failure
      """
      print 'Connection failed!'
      time.sleep(5)
      if self.func_loseConnect:
         self.func_loseConnect(protoObj, reason)
      #d, self.deferred_loseConnect = self.deferred_loseConnect, None
      #d.errback(reason)


   #############################################################################
   def sendTx(self, pytxObj):
      if self.proto:
         self.proto.sendTx(pytxObj)
      else:
         raise ConnectionError, 'Connection to localhost DNE.'



################################################################################
################################################################################
class SettingsFile(object):
   """
   This class could be replaced by the built-in QSettings in PyQt, except
   that older versions of PyQt do not support the QSettings (or at least
   I never figured it out).  Easy enough to do it here

   All settings must populated with a simple datatype -- non-simple 
   datatypes should be broken down into pieces that are simple:  numbers 
   and strings, or lists/tuples of them.

   Will write all the settings to file.  Each line will look like:
         SingleValueSetting1 # 3824.8 
         SingleValueSetting2 # this is a string
         Tuple Or List Obj 1 # 12 | 43 | 13 | 33
         Tuple Or List Obj 2 # str1 | another str
   """

   #############################################################################
   def __init__(self, path=None):
      self.settingsPath = path
      self.settingsMap = {}
      self.restoreDefaults()
      if not path:
         self.settingsPath = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt') 

      print 'Using settings file:', self.settingsPath
      if os.path.exists(self.settingsPath):
         self.loadSettingsFile(path)
      else:
         self.restoreDefaults()



   #############################################################################
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'Settings:'
      for k,v in self.settingsMap.iteritems():
         print indstr + indent + k.ljust(15), v

   #############################################################################
   def restoreDefaults(self):
      """ 
      Put all default settings here.  DNAA means "Do Not Ask Again"
      """
      self.settingsMap['New_Settings_File']   = True
      self.settingsMap['Load_Count']          = 0
      self.settingsMap['User_Mode']           = 'Standard'  # 'Advanced'
      self.settingsMap['Other_Wallets']       = ''
      self.settingsMap['First_Load']          = True
      self.settingsMap['UnlockTimeout']       = 10
      self.settingsMap['DNAA_UnlockTimeout']  = False

   #############################################################################
   def hasSetting(self, name):
      return self.settingsMap.has_key(name)
   
   #############################################################################
   def set(self, name, value):
      if isinstance(value, tuple):
         self.settingsMap[name] = list(value)
      else:
         self.settingsMap[name] = value
      self.writeSettingsFile()

   #############################################################################
   def extend(self, name, value):
      """ Adds/converts setting to list, appends value to the end of it """
      if not self.settingsMap.has_key(name):
         if isinstance(value, list):
            self.set(name, value)
         else:
            self.set(name, [value])
      else:
         origVal = self.get(name, expectList=True)
         if isinstance(value, list):
            origVal.extend(value)
         else:
            origVal.append(value)
         self.settingsMap[name] = origVal
      self.writeSettingsFile()

   #############################################################################
   def get(self, name, expectList=False):
      if not self.hasSetting(name) or self.settingsMap[name]=='':
         return ([] if expectList else '')
      else:
         val = self.settingsMap[name]
         if expectList:
            if isinstance(val, list):
               return val
            else:
               return [val]
         else:
            return val

   #############################################################################
   def getAllSettings(self):
      return self.settingsMap

   #############################################################################
   def getSettingOrSetDefault(self, name, defaultVal, expectList=False):
      output = defaultVal
      if self.hasSetting(name):
         output = self.get(name)
      else:
         self.set(name, defaultVal)

      return output

 



   #############################################################################
   def delete(self, name):
      if self.hasSetting(name):
         del self.settingsMap[name]
      self.writeSettingsFile()

   #############################################################################
   def writeSettingsFile(self, path=None):
      if not path:
         path = self.settingsPath
      f = open(path, 'w')
      for key,val in self.settingsMap.iteritems():
         try:
            # Skip anything that throws an exception
            valStr = '' 
            if isinstance(val, str) or \
               isinstance(val, unicode) or \
               isinstance(val, int) or \
               isinstance(val, float) or \
               isinstance(val, long):
               valStr = str(val)
            elif isinstance(val, list) or \
                 isinstance(val, tuple):
               valStr = ' $  '.join([str(v) for v in val])
            f.write(key.ljust(36) + ' | ' + valStr + '\n')
         except:
            print 'Invalid entry in SettingsFile... skipping'
      f.close()
      

   #############################################################################
   def loadSettingsFile(self, path=None):
      if not path:
         path = self.settingsPath

      if not os.path.exists(path):
         raise FileExistsError, 'Settings file DNE:', path

      f = open(path, 'r')
      sdata = f.read()
      f.close()

      # Automatically convert settings to numeric if possible
      def castVal(v):
         v = v.strip()
         a,b = v.isdigit(), v.replace('.','').isdigit()
         if a:   
            return int(v)
         elif b: 
            return float(v)
         else:   
            if v.lower()=='true':
               return True
            elif v.lower()=='false':
               return False
            else:
               return v
         

      sdata = [line.strip() for line in sdata.split('\n')]
      for line in sdata:
         if len(line.strip())==0:
            continue

         try:
            key,vals = line.split('|')
            valList = [castVal(v) for v in vals.split('$')]
            if len(valList)==1:
               self.settingsMap[key.strip()] = valList[0]
            else:
               self.settingsMap[key.strip()] = valList
         except:
            print 'Invalid setting in', path, ' (skipping...)'









