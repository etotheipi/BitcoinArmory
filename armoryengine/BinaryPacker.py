################################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory
# Author:     Alan Reiner
# Website:    www.bitcoinarmory.com
# Orig Date:  20 November, 2011
#
################################################################################

from struct import pack, unpack

from ArmoryLog import *
from ArmoryUtils import int_to_binary, lenBytes, toUnicode, toBytes
from BitSet import BitSet

from Constants import *
from Exceptions import *


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


class BinaryPacker(object):

   """
   Class for helping load binary data into a stream.  Typical usage is
      >> bp = BinaryPacker()
      >> bp.put(UINT32, 12)
      >> bp.put(VAR_INT, 78)
      >> bp.put(BINARY_CHUNK, '\x9f'*10)
      >> ...etc...
      >> result = bp.getBinaryString()
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
      elif varType in [VAR_STR, VAR_UNICODE]:
         # VAR_UNICODE is unpacked differently for unicode, but same for pack
         self.binaryConcat += packVarInt(lenBytes(theData))[0]
         self.binaryConcat += toBytes(theData)
      elif varType == FLOAT:
         self.binaryConcat += pack(E+'f', theData)
      elif varType == BINARY_CHUNK:
         if width is None:
            self.binaryConcat += theData
         else:
            if len(theData)>width:
               raise PackerError('Too much data to fit into fixed width field')
            self.binaryConcat += theData.ljust(width, '\x00')
      elif varType == BITSET:
         if width < theData.getNumBits()/8:
            raise PackerError('Too much data to fit into fixed width field')
         self.put(BINARY_CHUNK, theData.toBinaryString(), width)
      else:
         raise PackerError("Var type not recognized!  VarType="+str(varType))


################################################################################
def makeBinaryUnpacker(toUnpack):
   if isinstance(toUnpack, BinaryUnpacker):
      return toUnpack
   else:
      return BinaryUnpacker(toUnpack)


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

   def getSize(self):
      return len(self.binaryStr)

   def getRemainingSize(self):
      return len(self.binaryStr) - self.pos

   def getBinaryString(self):
      return self.binaryStr

   def getRemainingString(self):
      return self.binaryStr[self.pos:]

   def append(self, binaryStr):
      self.binaryStr += binaryStr

   def advance(self, bytesToAdvance):
      self.pos += bytesToAdvance

   def rewind(self, bytesToRewind):
      self.pos -= bytesToRewind

   def resetPosition(self, toPos=0):
      self.pos = toPos

   def getPosition(self):
      return self.pos

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
      elif varType == VAR_UNICODE:
         sizeCheck(1)
         [value, nBytes] = unpackVarInt(self.binaryStr[pos:pos+9])
         binOut = toUnicode(self.binaryStr[pos+nBytes:pos+nBytes+value])
         self.advance(nBytes+value)
         return binOut
      elif varType == FLOAT:
         sizeCheck(4)
         value = unpack(E+'f', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == BINARY_CHUNK:
         sizeCheck(sz)
         binOut = self.binaryStr[pos:pos+sz]
         self.advance(sz)
         return binOut
      elif varType == BITSET:
         binString = self.get(BINARY_CHUNK, sz)
         return BitSet.CreateFromBinaryString(binString)

      LOGERROR('Var Type not recognized!  VarType = %d', varType)
      raise UnpackerError("Var type not recognized!  VarType=%s" % varType)
