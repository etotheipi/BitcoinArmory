import sys
sys.argv.append('--nologging')
from armoryengine import BTC_HOME_DIR

from utilities.ArmoryUtils import binary_to_int, LITTLEENDIAN, sha256, \
   binary_to_hex, BIGENDIAN
import hashlib
import os



BLOCK_SIZE_LENGTH = 4
MAGIC_NUMBER_LENGTH = 4
HEADER_LENGTH = 80

def getLastBlockFile():
   # the current last block file number
   i = 80
   blkFilePath = os.path.join(BTC_HOME_DIR, 'blocks', 'blk%05d.dat' % i)
   lastFile = None
   while True:
      try:
         with open(blkFilePath, 'rb') as f:
            lastFile = blkFilePath
      except IOError:
         break
      i += 1
      blkFilePath = os.path.join(BTC_HOME_DIR, 'blocks', 'blk%05d.dat' % i)
   return lastFile

def getFileSize(f):
   pos = f.tell()
   # Go to the end to get the file length
   f.seek(0,2)
   result = f.tell()
   f.seek(pos)
   return result


def getNextBlockHash(f):
   fileOffset = f.tell()
   f.seek(MAGIC_NUMBER_LENGTH, 1)
   blkSize = binary_to_int(f.read(BLOCK_SIZE_LENGTH), LITTLEENDIAN)
   result = None
   if blkSize > 0:
      blkString = f.read(blkSize)
      blkHdrBinary = blkString[:HEADER_LENGTH]
      result = sha256(sha256(blkHdrBinary))
   else:
      f.seek(0,2)
   return result

def getLastBlockHash(blkFile):
   result = None
   with open(blkFile, 'rb') as f:
      fSize = getFileSize(f)
      while f.tell() < fSize:
         blockHash = getNextBlockHash(f)
         if blockHash != None:
            result = blockHash
   return result

print binary_to_hex(getLastBlockHash(getLastBlockFile()), BIGENDIAN)
