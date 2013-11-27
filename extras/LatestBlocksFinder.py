import sys
sys.argv.append('--nologging')

from utilities.BinaryUnpacker import BinaryUnpacker
from utilities.ArmoryUtils import binary_to_int, LITTLEENDIAN, binary_to_hex,\
   sha256, BIGENDIAN
from utilities.BinaryPacker import BINARY_CHUNK, UINT32, VAR_INT
from collections import namedtuple

import os
from armoryengine import BTC_HOME_DIR

n = 10
def getLastTwoFiles():
   i = 79
   blkFilePath = os.path.join(BTC_HOME_DIR, 'blocks', 'blk%05d.dat' % i)
   lastFile = None
   secondToLastFile = None
   while True:
      try:
         with open(blkFilePath, 'rb') as f:
            secondToLastFile = lastFile
            lastFile = [i,blkFilePath]
      except IOError:
         break
      i += 1
      blkFilePath = os.path.join(BTC_HOME_DIR, 'blocks', 'blk%05d.dat' % i)
   return lastFile, secondToLastFile

def getFileSize(f):
   pos = f.tell()
   # Go to the end to get the file length
   f.seek(0,2)
   result = f.tell()
   f.seek(pos)
   return result


BLOCK_SIZE_LENGTH = 4
MAGIC_NUMBER_LENGTH = 4
HEADER_LENGTH = 80

TX_OUT_HASH_LENGTH = 32
TX_OUT_INDEX_LENGTH = 4
SEQUENCE_LENGTH = 4
VERSION_LENGTH = 4
TxOut = namedtuple('TxOut', ['txOutIndex', 'value', 'script', 'txOutType'])
TxIn = namedtuple('TxIn', ['outpoint', 'script','sequence'])
Tx = namedtuple('Tx', ['txHash', 'version', 'txInList', 'txOutList'])
Block = namedtuple('Block', ['blkNum', 'blkSize', 'blkHdr', 'txCount', 'txBinary', 'txOffsetList', 'txList'])
BlockHeader = namedtuple('BlockHeader', ['version', 'prevHash', 'merkleHash',
                                       'time', 'bits', 'nonce' ])

def parseBlockHeader(blkHdrBinary):
   binunpack = BinaryUnpacker(blkHdrBinary)
   return BlockHeader(binunpack.get(UINT32),
                      binunpack.get(BINARY_CHUNK, 32),
                      binunpack.get(BINARY_CHUNK, 32),
                      binunpack.get(UINT32),
                      binunpack.get(UINT32),
                      binunpack.get(UINT32))

def getBlockHeight(txBinary):
   binunpack = BinaryUnpacker(txBinary)
   binunpack.advance(VERSION_LENGTH)
   txInCount = binunpack.get(VAR_INT)
   binunpack.advance(TX_OUT_HASH_LENGTH + TX_OUT_INDEX_LENGTH)
   sigScriptLength = binunpack.get(VAR_INT)
   binunpack.advance(1)
   height = binary_to_int(binunpack.get(BINARY_CHUNK, 3))
   return height

def getNextBlock(f):
   fileOffset = f.tell()
   f.seek(MAGIC_NUMBER_LENGTH, 1)
   blkSize = binary_to_int(f.read(BLOCK_SIZE_LENGTH), LITTLEENDIAN)
   result = None
   if blkSize > 0:
      binunpack = BinaryUnpacker(f.read(blkSize))
      blkHdrBinary = binunpack.get(BINARY_CHUNK, HEADER_LENGTH)
      txCount = binunpack.get(VAR_INT)
      txBinary = binunpack.get(BINARY_CHUNK, binunpack.getRemainingSize())
      blockHeight = getBlockHeight(txBinary)
      result = [sha256(sha256(blkHdrBinary)), blockHeight, fileOffset]
   else:
      f.seek(0,2)
   return result

# argument is an array that consists of a file descriptor with the file number
def getAllBlocks(blkFileWithNumber):
   blkInfoList = []
   with open(blkFileWithNumber[1], 'rb') as f:
      fSize = getFileSize(f)
      while f.tell() < fSize:
         blkInfo = getNextBlock(f)
         if blkInfo != None:
            blkInfoWithFileNum = [blkFileWithNumber[0]]
            blkInfoWithFileNum.extend(blkInfo)
            blkInfoList.append(blkInfoWithFileNum)
   return blkInfoList

# only goes back 2 files so anything over 800 could get cut off
# at 2 block files worth of data
def getLastNBlocks(n=10):
   lastFile, secondToLastFile = getLastTwoFiles()

   lastBlocks = getAllBlocks(lastFile)
   if len(lastBlocks) < n:
      secondToLastBlocks = getAllBlocks(secondToLastFile)
      secondToLastBlocks.extend(lastBlocks)
      lastBlocks = secondToLastBlocks
   return lastBlocks[-n:]

lastNBlocks = getLastNBlocks(3)
for blk in lastNBlocks:
   print blk[0], binary_to_hex(blk[1], BIGENDIAN), blk[2], blk[3]
