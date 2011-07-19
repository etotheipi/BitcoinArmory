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

   def __init__(self, genesisBlockHash=GENESIS_BLOCK_HASH):
      self.genBlkHash = genesisBlockHash
      self.networkMagicBytes = ''
      self.blockHeadersMap   = {}               # indexed by header hash
      self.txHashListMap     = {}               # indexed by header hash
      self.txDataMap         = {}               # indexed by transaction hash
      self.topBlockHash      = self.genBlkHash  # tip of the longest chain (hash)
      self.topBlockHeight    = 0                # the height at the top
      self.topBlockSumDiff   = 0                # Cumulative difficulty at top
      #self.lastChainCalc   = UNINITIALIZED  # will contain the last time we calculated the chain

   def readBlockChainFile(self, bcfilename, justHeaders=False):
      # This ended up much more complicated than I had hoped, because I 
      # was trying to buffer the read so I don't have the full 500 MB of
      # blk0001.dat in memory at once...  
      assert(path.exists(bcfilename))
      bcFile = open(bcfilename, 'r')
      binUnpacker = BinaryUnpacker(bcFile.read(BUF_SIZE))
      fileSizeLeft = os.stat(bcfilename).st_size - BUF_SIZE

      print 'File %s is %0.2f MB' % (bcfilename, (fileSizeLeft+BUF_SIZE)/float(1024**2))
      print 'Reading blockdata',
      if justHeaders:
         print '(just headers)',
      print ''

      i = 0
      while fileSizeLeft > 0 or binUnpacker.getRemainingSize() > 1:
         if( i%10000 == 0):
            print '\tBlocks read:', i
         # Each block starts with 4 magic bytes
         magicBytes = binary_to_hex(binUnpacker.get(BINARY_CHUNK, 4))
         nextBlockSize = binUnpacker.get(UINT32)
         
         buBytesLeft = binUnpacker.getRemainingSize()
         if buBytesLeft < nextBlockSize + 8:
            if(fileSizeLeft + buBytesLeft < nextBlockSize):
               return
            else:
               readSz = min(fileSizeLeft, BUF_SIZE)
               binUnpacker.append( bcFile.read(readSz) )
               fileSizeLeft -= readSz


         blockStartByte = bcFile.tell() - binUnpacker.getRemainingSize()
         thisHeader = BlockHeader().unserialize( binUnpacker )
         thisData   = []
         if justHeaders:
            afterHeaderPos = binUnpacker.getPosition()
            binUnpacker.advance( nextBlockSize - 80 )
         else:
            thisData = BlockData().unserialize( binUnpacker )
            
         self.addBlockToMemoryPool(thisHeader, thisData, justHeaders)   
         blkFilePos = int_to_binary(blockStartByte, widthBytes=8)
         if i==0: 
            if not (magicBytes=='f9beb4d9' or magicBytes=='fabfb5da'):
               print 'File', bcfilename, 'is not a blockchain file!'
               return False
            self.networkMagicBytes = magicBytes
         i += 1

         

   def readHeadersFile(self, headfilename):
      assert(path.exists(headfilename))
      print 'Reading Headers file:', headfilename, '...'
      headFile = open(headfilename, 'r')
      binData = BinaryUnpacker(headFile.read())
      headFile.close()

      # 4 magic bytes at beginning, 80 bytes-per-header
      sizeHeaderFile = os.stat(headfilename).st_size
      self.networkMagicBytes = binary_to_hex( binData.get(BINARY_CHUNK, 4) )
      numBlocks = binary_to_int( binData.get(BINARY_CHUNK, 4) )
      bytesPerHeader = (sizeHeaderFile-8)/numBlocks

      for i in range(numBlocks):
         header = BlockHeader().unserializeWithExtra(binData)
         self.addBlockToMemoryPool(header, justHeaders=True)
         
      print 'Done reading headers file'
      print 'Headers file size is:    ', float(sizeHeaderFile) / float(1024**2), 'MB'
      print 'Number of headers:       ', numBlocks
      print 'Bytes for each header:   ', bytesPerHeader, '(80 official bytes,', bytesPerHeader-80,' extra bytes)'
      print 'Headers are for network: ', ' '.join([self.networkMagicBytes[i:i+2] for i in range(0,8,2)])

      return self
         
   def writeHeadersFile(self, headfilename):
      print 'Writing Headers file:', headfilename, '...'
      bp = BinaryPacker()
      
      nHeaders = len(self.blockHeadersMap)
      print 'nHeaders:',nHeaders
      print 'magic:', self.networkMagicBytes
      bp.put(BINARY_CHUNK, hex_to_binary(self.networkMagicBytes))
      bp.put(UINT32, nHeaders)
      print binary_to_hex(bp.getBinaryString())
      for headhash, head in self.blockHeadersMap.iteritems():
         bp.put(BINARY_CHUNK, head.serializeWithExtra() )
       
      headFile = open(headfilename, 'w')
      headFile.write(bp.getBinaryString())
      
      
      
   # From the given block, walk backwards to the highest block that has a 
   # definite height and sumDifficulty.  Then walk back up the chain and
   # fill in all the heights and sumDifficulty values.  If the startHash
   # is already "solved", then we just exit.  Only the first couple calls
   # to this method will do a lot of computation
   def solveChainFromTop(self, startNodeHash):
      headers = self.blockHeadersMap  # gonna be accessing this alot, make ref
      startBlk = headers[startNodeHash] 

      if not startBlk.blkHeight == UNINITIALIZED:
         return (startBlk.blkHeight, startBlk.sumDifficult)

      # The only block that doesn't have a prevBlkHash is the genesis block,
      # but we've made sure it is "solved" already... right?
      hashlistBackwards   = [startNodeHash]
      thisBlk = headers[startBlk.prevBlkHash ]
      while thisBlk.blkHeight == UNINITIALIZED:
         hashlistBackwards.append(thisBlk.theHash)
         thisBlk = headers[ thisBlk.prevBlkHash ]
         
      # Now we should have a long list of hashes starting from the top node
      # to the highest-so-far solved block (will be the genesis block
      # on the first call).  Now walk back up, setting the block heights
      # and cumulative difficulties
      for theHash in hashlistBackwards[::-1]:
         thisBlk = headers[theHash]
         prevBlk = headers[thisBlk.prevBlkHash]
         thisBlk.sumDifficult = prevBlk.sumDifficult + thisBlk.getDifficulty()
         thisBlk.blkHeight    = prevBlk.blkHeight + 1
         prevBlk.isOrphan = False
          
      thisBlk = headers[startNodeHash]
      return (thisBlk.blkHeight, thisBlk.sumDifficult)
      
      

   def calcLongestChain(self, recalcAll=False):
      # To calculate the longest chain, we start from every block and 
      # work our way down to the highest point we've "answered" already
      # (found absolute block-height and cumulative difficulty).  Then we
      # walk back up filling in the heights and cumulative difficulties 
      # for the nodes we just passed.  Once a few high nodes have been
      # calculated, most of the blocks will already be done.  
      
      headers = self.blockHeadersMap  # gonna be accessing this alot, make ref

      prevTopHash   = self.topBlockHash
      prevTopHeight = self.topBlockHeight

      if recalcAll:
         prevTopHash   = GENESIS_BLOCK_HASH
         prevTopHeight = 0

      # Seed the base of the chain with a solved genesis block
      genBlk = headers[GENESIS_BLOCK_HASH]
      genBlk.blkHeight = 0
      genBlk.sumDifficult = 1.0
      genBlk.isOrphan = False

      # Now follow the chain back from every block in the memory pool
      for blkhash in headers.iterkeys():
         height, sumDiff = self.solveChainFromTop(blkhash)
         if sumDiff > self.topBlockSumDiff:
            self.topBlockHeight  = height
            self.topBlockSumDiff = sumDiff
            self.topBlockHash    = blkhash
         
         
      # Finally, we trace the chain back down one more time, from the best
      # block.  This time we update all the nextBlkHash values to point to 
      # the "correct" nextNode (the one on the main blockChain)
      thisBlk = headers[self.topBlockHash]
      thisBlk.nextBlkHash = NOHASH
      nextHash = self.topBlockHash
      while not thisBlk.blkHeight==prevTopHeight:
         thisBlk = headers[thisBlk.prevBlkHash]
         thisBlk.nextBlkHash = nextHash   
         thisBlk.isOrphan = False   
         nextHash = thisBlk.theHash
         
      return self.topBlockHash

               
      
         
   #############################################################################
   #############################################################################
      
      


   def addBlockToMemoryPool(self, head, data=[], justHeaders=False):

      headHash = hash256(head.serialize())
      #print 'Adding block', binary_to_hex(headHash, endOut=BIGENDIAN), ' Diff = ', head.getDifficulty()
      self.blockHeadersMap[headHash] = head
      if justHeaders:
         pass
      else:
         calcRoot = data.getMerkleRoot()
         assert(calcRoot == head.merkleRoot)
         self.txHashListMap[headHash] = data.getTxHashList()
         for i,tx in enumerate(data.txList):
            self.txDataMap[data.merkleTree[i]] = tx

   def getBlockChainStats(self):
      return (len(self.blockHeadersMap), len(self.txDataMap))  
         

   def getBlockHeaderByHash(self, txHash):
      if(self.blockHeadersMap.has_key(txHash)):
         return self.blockHeadersMap[txHash]
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


class BitcoinAccount(object):
   def __init__(self, name, addrFile, keyFile=None):
      pass
      
