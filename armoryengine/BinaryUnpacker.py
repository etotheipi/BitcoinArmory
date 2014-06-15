################################################################################
#
# Copyright (C) 2011-2014, Armory Technologies, Inc.                         
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




################################################################################
################################################################################
#  Classes for reading and writing large binary objects
################################################################################
################################################################################
from struct import pack, unpack
from BinaryPacker import UINT8, UINT16, UINT32, UINT64, INT8, INT16, INT32, INT64, VAR_INT, VAR_STR, FLOAT, BINARY_CHUNK
from armoryengine.ArmoryUtils import LITTLEENDIAN, unpackVarInt, LOGERROR

class UnpackerError(Exception): pass

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
         value = unpack(E+'f', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == BINARY_CHUNK:
         sizeCheck(sz)
         binOut = self.binaryStr[pos:pos+sz]
         self.advance(sz)
         return binOut

      LOGERROR('Var Type not recognized!  VarType = %d', varType)
      raise UnpackerError, "Var type not recognized!  VarType="+str(varType)

################################################################################
