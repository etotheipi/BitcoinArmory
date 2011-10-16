from pybtcengine import *
import os
from os import path
import bsddb


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
      #self.headerDB          = bsddb.btopen('bsddb.headers.bin', 'c')
      #self.dataDB            = bsddb.btopen('bsddb.data.bin', 'c')
      #self.txDB              = bsddb.btopen('bsddb.tx.bin', 'c')
      #self.lastChainCalc   = UNINITIALIZED  # will contain the last time we calculated the chain

   def readBlockChainFile(self, bcfilename, justHeaders=False):
      # We will try reading directly from file, to see if this improves the
      # speed compared to using binary unpacker
      assert(path.exists(bcfilename))
      bcFile = open(bcfilename, 'r')
      #binUnpacker = BinaryUnpacker(bcFile.read(BUF_SIZE))
      fileSizeLeft = os.stat(bcfilename).st_size

      print 'File %s is %0.2f MB' % (bcfilename, (fileSizeLeft)/float(1024**2))
      print 'Reading blockdata',
      if justHeaders:
         print '(just headers)',
      print ''

      i = 0
      while fileSizeLeft > 0: # or binUnpacker.getRemainingSize() > 1:
         if( i%10000 == 0):
            print '\tBlocks read:', i
         # Each block starts with 4 magic bytes
         #magicBytes = binary_to_hex(binUnpacker.get(BINARY_CHUNK, 4))
         #nextBlockSize = binUnpacker.get(UINT32)
         bytes8 = bcFile.read(8)
         magicBytes = binary_to_hex(bytes8[:4])
         nextBlockSize = binary_to_int(bytes8[4:])
         
         blockStartByte = bcFile.tell() + 80 # where to start reading BlockData
         nextBlockStr = bcFile.read(nextBlockSize)
         fileSizeLeft -= nextBlockSize+8

         thisHeader = BlockHeader().unserialize( nextBlockStr )
         thisHeader.fileByteLoc = blockStartByte
         txData    = []
         thisTxList  = []
         if not justHeaders:
            txData = BlockData().unserialize( nextBlockStr[80:] )
            thisHeader.numTx = txData.numTx
            
         self.addBlockToMemoryPool(thisHeader, txData, justHeaders=justHeaders)   
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

      # 4 magic bytes at beginning, 80 bytes-per-header
      sizeHeaderFile = os.stat(headfilename).st_size

      first8 = headFile.read(8)
      self.networkMagicBytes = binary_to_hex( first8[:4] )
      numBlocks = binary_to_int( first8[4:] )
      bytesPerHeader = (sizeHeaderFile-8)/numBlocks

      for i in range(numBlocks):
         header = BlockHeader().unserializeWithExtra( headFile.read(bytesPerHeader) )
         self.addBlockToMemoryPool(header, justHeaders=True)
         
      print 'Done reading headers file'
      print 'Headers file size is:    ', float(sizeHeaderFile) / float(1024**2), 'MB'
      print 'Number of headers:       ', numBlocks
      print 'Bytes for each header:   ', bytesPerHeader, '(80 official bytes,', bytesPerHeader-80,' extra bytes)'
      print 'Headers are for network: ', ' '.join([self.networkMagicBytes[i:i+2] for i in range(0,8,2)])

      headFile.close()
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
       
      headFile = open(headfilename, 'wb')
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
         prevBlk.isMainChain = True
          
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
      genBlk.isMainChain = True

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
         thisBlk.isMainChain = True
         nextHash = thisBlk.theHash
         
      return self.topBlockHash

               
      
         
   #############################################################################
   #############################################################################
      
      


   def addBlockToMemoryPool(self, head, data=[], itsHash=None, justHeaders=False):
      if itsHash==None:
         itsHash = hash256(head.serialize())
      #print 'Adding block', binary_to_hex(itsHash, endOut=BIGENDIAN), ' Diff = ', head.getDifficulty()
      self.blockHeadersMap[itsHash] = head
      if justHeaders:
         pass
      else:
         calcRoot = data.getMerkleRoot()
         assert(calcRoot == head.merkleRoot)
         self.txHashListMap[itsHash] = data.getTxHashList()
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






class ArmoryWallet(object):
   def __init__(self, name='<no name>'):
      self.name = name
      self.addrDataMap = {}
      self.fileList = []
      self.remotes = []
      self.isMine = []
      






