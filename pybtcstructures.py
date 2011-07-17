from pybtcengine import *
import os
from os import path


BUF_SIZE = 16*1024**2


class BlockChain(object):
   """
   All information about each block is stored by its hash.  The entry in the
   header and data maps is created just by seeing a block hash.  Once the block
   information is acquired, it will be used to fill in the map.  This creates
   flexibility, but also may be annoying to have to always check whether 
   block data is filled in
   """

   def __init__(self, genesisBlock='000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'):
      self.genBlkHash = hex_to_binary(genesisBlock, BIGENDIAN)
      self.blockHeadersMap = {}  # indexed by header hash
      self.txHashListMap   = {}  # indexed by header hash
      self.txDataMap       = {}  # indexed by transaction hash

   def readBlockChainFile(self, bcfilename, justHeaders=False):
      # This ended up much more complicated than I had hoped, because I 
      # was trying to buffer the read so I don't ahve the full 500 MB of
      # blk0001.dat in memory at once...  
      assert(path.exists(bcfilename))
      bcFile = open(bcfilename, 'r')
      binUnpacker = BinaryUnpacker(bcFile.read(BUF_SIZE))
      fileSizeLeft = os.stat(bcfilename).st_size - BUF_SIZE
      headFile = open('blkHeadersOnly.dat', 'w')

      i = 0
      print 'File %s is %0.2f MB' % (bcfilename, fileSizeLeft/float(1024**2))
      print 'Reading blockdata',
      if justHeaders:
         print '(just headers)',
      print ''

      while fileSizeLeft > 0 or binUnpacker.getRemainingSize() > 1:
         if( i%10000 == 0):
            print '\tBlocks read:', i
         # Each block starts with 4 magic bytes
         magicBytes    = binary_to_hex(binUnpacker.get(BINARY_CHUNK, 4))
         nextBlockSize = binUnpacker.get(UINT32)
         
         buBytesLeft = binUnpacker.getRemainingSize()
         if buBytesLeft < nextBlockSize + 8:
            if(fileSizeLeft + buBytesLeft < nextBlockSize):
               return
            else:
               binUnpacker.append( bcFile.read(BUF_SIZE) )
               fileSizeLeft -= BUF_SIZE

         #if not (magicBytes=='f9beb4d9' or magicBytes=='fabfb5da'):
            #print 'File', bcfilename, 'is not a blockchain file!'
            #return False
         #print fileSizeLeft, binUnpacker.getRemainingSize(), nextBlockSize

         blockStartByte = bcFile.tell() - binUnpacker.getRemainingSize()
         thisHeader = BlockHeader().unserialize( binUnpacker )
         thisData   = []
         if justHeaders:
            afterHeaderPos = binUnpacker.getPosition()
            binUnpacker.advance( nextBlockSize - 80 )
         else:
            thisData = BlockData().unserialize( binUnpacker )
            
         #thisBlock.pprint()

         self.addBlockToMemoryPool(thisHeader, thisData, justHeaders)   
         blkFilePos = int_to_binary(blockStartByte, widthBytes=8)
         headFile.write( blkFilePos + thisHeader.serialize())
         i += 1

      headFile.close()
         


   def addBlockToMemoryPool(self, head, data, justHeaders=False):

      headHash = hash256(head.serialize())
      intDiff = binaryBits_to_intDifficulty( head.diffBits )
      print 'Adding block', binary_to_hex(headHash, endOut=BIGENDIAN), ' Diff = ', intDiff
      self.blockHeadersMap[headHash] = head
      if justHeaders:
         pass
      else:
         calcRoot = data.getMerkleRoot()
         assert(calcRoot == head.merkleRoot)
         self.txHashListMap[headHash] = data.getTxHashList()
         for i,tx in enumerate(theBlock.blockData.txList):
            self.txDataMap[data.merkleTree[i]] = tx

   def getBlockChainStats(self):
      return (len(self.blockHeadersMap), len(self.txDataMap))  
         

   def getBlockHeaderByHash(self, txHash):
      if(self.blockheadersMap.has_key(txHash)):
         return self.blockheadersMap[txHash]
      else:
         return None
      

   def getBlockDataByHash(self, txHash):
      if(self.blockDataList.has_key(txHash)):
         return self.blockDataList[txHash]
      else:
         return None

   def getBlockByHash(self, txHash):
      # TODO:  Since we aren't storing the whole block in memory, we need 
      #        to reconstruct the block on the fly from the header and the
      #        transaction list
      if(self.blockHeadersMap.has_key(txHash)):
         blk = Block()
         #blk.blockHeader = self.blockHeadersMap[txHash]
         #blk.blockData = self.blockHeadersMap[txHash]
         return blk
      else:
         return None




class KeyStore(object):
   class KeyData(object):
      def __init__(self, addrStr, addrInt, privateInt):
         self.secret = privateInt
      

   def __init__(self):
      self.addrMap = None


class SavingsAccount(object):
   def __init__(self, name, addrFile, keyFile=None):
      pass
      
