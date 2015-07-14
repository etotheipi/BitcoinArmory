###############################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
###############################################################################

from ArmoryUtils import *


################################################################################
class BitSet(object):
   """
   A very simplie implementation of a BitSet, intended for serialization and
   deserialization (thus the size of the BitSet must be a multiple of 8).
   It's not intended to be fast:  if you need to make thousands of bitsets
   holding millions of flags, this isn't the class to use.
   """
   ############################################################
   def __init__(self, numBits=0):
      if not numBits%8 == 0:
         LOGWARN('Number of bits must be a multiple of 8.  Rounding up...')

      self.bitList = [0] * roundUpMod(numBits, 8)

   ############################################################
   def __len__(self):
      return self.getNumBits()

   ############################################################
   def getNumBits(self):
      return len(self.bitList)

   ############################################################
   def reset(self, state=False):
      newVal = 1 if state else 0
      for i in range(len(self.bitList)):
         self.setBit(i, newVal)


   ############################################################
   def setBit(self, index, val):
      try:
         val = int(val)
      except:
         raise BadInputError('Invalid setBit call: "%s"' % str(val))

      if not val in [0,1]:
         raise BadInputError('Input value must be 0 or 1, got %d' % val)

      self.bitList[index] = val

   ############################################################
   def getBit(self, index):
      return self.bitList[index]

   ############################################################
   def getSlice(self, start, nbits):
      bs = BitSet(nbits)
      for i in range(nbits):
         bs.bitList[i] = self.bitList[i+start]
      return bs

   ############################################################
   def toBitString(self):
      return ''.join(['1' if b else '0' for b in self.bitList])

   ############################################################
   def toBinaryString(self, byteWidth=None):
      if self.getNumBits() == 0:
         return ''

      if byteWidth is None:
         byteWidth = self.getNumBits()/8

      if byteWidth < self.getNumBits()/8:
         raise BadInputError('Requested width does not match bitset')

      return int_to_binary(self.toInteger(),
                           widthBytes=byteWidth,
                           endOut=BIGENDIAN)

   ############################################################
   def toInteger(self):
      n = 0
      for i,bit in enumerate(self.bitList[::-1]):
         n += bit * (2**i)
      return n


   ############################################################
   def copy(self, newSize=None):
      if newSize is None:
         newSize = self.getNumBits()

      if newSize < self.getNumBits():
         LOGWARN('Truncating BitSet from %d bits to %d bits',
                                    self.getNumBits(), newSize)

      bs = BitSet(newSize)
      for i in range(newSize):
         bs.bitList[i] = 0 if i>=self.getNumBits() else self.bitList[i]

      return bs


   ############################################################
   @staticmethod
   def CreateFromBitString(bitstr):
      """
      A "bit string" is just a list of '1' and '0's in a string
      """
      bitstr = bitstr.replace(' ','')
      bs = BitSet(len(bitstr))
      for i in range(len(bitstr)):
         bs.setBit(i, int(bitstr[i]))
      return bs

   ############################################################
   @staticmethod
   def CreateFromBinaryString(binstr):
      """
      This is the most compact representation of a BitSet, raw binary out
      """
      nBytes = len(binstr)
      readInt = binary_to_int(binstr, BIGENDIAN)
      return BitSet.CreateFromInteger(readInt, nBytes*8)

   ############################################################
   @staticmethod
   def CreateFromInteger(ival, numBits=0):

      # Could use log(ival, 2) but no need for transcendental functions
      blist = []
      while ival>0:
         ival,r = divmod(ival,2)
         blist.append(r)

      if numBits == 0:
         numBits = len(blist)
      else:
         if len(blist) > numBits:
            raise BadInputError('Requested nBits cannot contain input integer')

         if not numBits%8 == 0:
            # Will be updated below
            LOGWARN('Number of bits must be a multiple of 8.  Rounding up...')

      numBits = roundUpMod(numBits, 8)

      while len(blist) < numBits:
         blist.append(0)

      bs = BitSet(len(blist))
      bs.bitList = blist[::-1]
      return bs
