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
from ArmoryUtils import *

import CppBlockUtils as Cpp


################################################################################
def createRSECCode(data, ecBytes=ERRCORR_BYTES,
                         perDataBytes=ERRCORR_PER_DATA):
   """
   Returns default of 16 bytes of parity per 1024 bytes of input.
   If the input is, say 2500 bytes, then we will have 48 bytes of
   parity, 16 for the first 1024, 16 for the next 1024, and 16 for
   the last 452.
   """

   LOGERROR('TODO: TEMPORARILY DISABLED RS ERROR CORRECTION.  FIXME')

   parity = []
   nChunk = (len(data)-1)/perDataBytes + 1
   for i in range(nChunk):
      byte0, byte1 = i*perDataBytes, (i+1)*perDataBytes
      #parity.append(Cpp.GetParityBytes(data[byte0:byte1], ecBytes))
      parity.append('\x00'*ERRCORR_BYTES)
   return ''.join(parity)


################################################################################
def verifyRSECCode(data, parity, ecBytes=ERRCORR_BYTES,
                                perDataBytes=ERRCORR_PER_DATA):
   """
   Returns:
      data:  input after error correction
      bool:  data failed correction, invalid
      bool:  data was modified

   If parity is all zero bytes, then we ignore it and return the data as-is.
   """

   LOGERROR('TODO: TEMPORARILY DISABLED RS ERROR CORRECTION.  FIXME')

   if len(parity)==parity.count('\x00'):
      # Parity is NULL, ignore it and return the input
      return data, False, False
   else:
      # Parity bytes are non-zero, check for (and correct) errors, if possible
      correctData = Cpp.CheckRSErrorCorrect(data, parity, ecBytes, perDataBytes)
      if len(correctData) == 0:
         return '', True, False
      elif correctData==data:
         return correctData, False, False
      else:
         return correctData, False, True


################################################################################
def createChecksumBytes(data, ecBytes=ERRCORR_BYTES,
                              perDataBytes=ERRCORR_PER_DATA):
   nBlks = ((len(data) - 1) / int(perDataBytes)) + 1
   chksum = ''
   for i in range(nBlks):
      b0 = i*perDataBytes
      b1 = (i+1)*perDataBytes
      chksum += computeChecksum(data[b0:b1], ecBytes)

   return chksum


################################################################################
def verifyChecksumBytes(data, chksum, ecBytes=ERRCORR_BYTES,
                                      perDataBytes=ERRCORR_PER_DATA):
   """
   Returns:
      data:  input after error correction
      bool:  data failed correction, invalid
      bool:  data was modified
   """
   output = ''
   nBlks = ((len(data) - 1) / int(perDataBytes)) + 1
   if not len(chksum)==nBlks*ecBytes:
      LOGERROR('Invalid checksum data: len(data)==%d, len(chk)==%d' % \
                  (len(data), len(chksum)))

   for i in range(nBlks):
      blk = data[i*perDataBytes:(i+1)*perDataBytes]
      chk = chksum[i*ecBytes:(i+1)*ecBytes]
      blkFixed = verifyChecksum(blk, chk)
      if len(blkFixed)==0:
         return '', True, False
      output += blkFixed

   # We were able to correct errors
   if output==data:
      errInChk = createChecksumBytes(data, ecBytes, perDataBytes) != chksum
      return output, False, errInChk
   else:
      return output, False, True
