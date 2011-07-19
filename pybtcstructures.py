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

      print 'File %s is %0.2f MB' % (bcfilename, fileSizeLeft/float(1024**2))
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
               binUnpacker.append( bcFile.read(BUF_SIZE) )
               fileSizeLeft -= BUF_SIZE


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
      print 'Headers are for network: ', [self.networkMagicBytes[i:i+2] for i in range(4)]

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
      
      
   #############################################################################
   #############################################################################

   #def calcLongestChain(self, startHash=GENESIS_BLOCK_HASH):
      ## This method is exceptionally complicated, because it would best
      ## be solved using recursion, but we don't want to do any recursion
      ## because we'd quickly hit the recursion limit with such long chains.
      ## This could also be made dramatically simpler by just making ANY
      ## reasonable assumptions, such as there will never be multiple branching
      ## or orphan branches longer than some amount.  Instead, I opted to 
      ## write the most general method possible, that will work on any 
      ## block chain under even the craziest circumstances.  That's just how
      ## I roll...
      #leafList = []
      #branchNodeStack = []
      #headers = self.blockHeadersMap  # gonna be accessing this alot, make ref
      #
#
      ## Step 1:  Iterate through all the blocks we have in the memory pool 
      ##          and set their prev-nodes' nextBlkHash values
      ##          Since we will be searching the entire memory pool but may
      ##          be starting from the end of an already-calculated chain,
      ##          we skip any block that already has its blkHeight calculated
      ##          Then the following steps will on operate from startNode up
      #for blkhash, thisBlk in headers.iteritems():
         #if thisBlk.blkHeight == UNINITIALIZED:
            #thisBlk.nextBlkHash = [NOHASH]
         #if thisBlk.blkHeight == UNINITIALIZED and headers.has_key(thisBlk.prevBlkHash):
            #prevBlk = headers[thisBlk.prevBlkHash]
            #prevBlk.isLeafNode   = False
            #prevBlk.alreadyCalc  = False
            #if (prevBlk.nextBlkHash==UNINITIALIZED) or (prevBlk.nextBlkHash==NOHASH):
               #prevBlk.nextBlkHash  = [[blkhash, False]]
               #prevBlk.isBranchNode = False
            #else:
               #prevBlk.nextBlkHash.append([blkhash, False])
               #prevBlk.isBranchNode = True
               #
      ## Step 2: Now the longest chain can be followed from the start block
      ##         but we're going to hit lots of branches along the way up,
      ##         so we have to traverse each branch, without recursion
      ##         We do this by pushing each branch node onto a stack, and
      ##         then restart from that node when we hit a leaf.  This will
      ##         essentially do a depth-first search of the tree
      #def getNextUnsolvedBranchIndex(node):
         #for i in range(len(node.nextBlkHash)):
            #if node.nextBlkHash[i][1] == False:
               #return i
      #
      #prevIntDiff, prevSumDiff, prevBlkHeight = 0,0,0
      #thisBlk = headers[startHash]
      #if thisBlk.theHash == GENESIS_BLOCK_HASH:
         #prevIntDiff  = 0
         #prevSumDiff  = 0
         #prevBlkHeight = -1
      #else:
         #prevIntDiff  = thisBlk.intDifficult
         #prevSumDiff  = thisBlk.sumDifficult
         #prevBlkHeight = thisBlk.blkHeight
         #thisBlk = thisBlk.nextBlkHash
#
      ## We know that if we're at a leaf node, and there was no more branches,
      ## we've finished the entire search
      #while not (thisBlk.isLeafNode and len(branchNodeStack) == 0):
#
         #if not thisBlk.alreadyCalc:
            #thisBlk.sumDifficult = prevSumDiff + thisBlk.getDifficulty()
            #thisBlk.blkHeight    = prevBlkHeight + 1
            #thisBlk.alreadyCalc  = True
#
         #prevIntDiff   = thisBlk.getDifficulty()
         #prevSumDiff   = thisBlk.sumDifficult
         #prevBlkHeight = thisBlk.blkHeight
#
         #if not thisBlk.isLeafNode:
            ## Else, we get the next block to search, which may be a branch child
            #nBranch = len(thisBlk.nextBlkHash)
            #nextBranchIndex = getNextUnsolvedBranchIndex(thisBlk)
            #if nextBranchIndex == nBranch-1 and nBranch > 1:
               ## This node must've previously been added to the branch stack, but we're done
               ## searching it after this 
               #del branchNodeStack[-1]
            #nextNodeHash = thisBlk.nextBlkHash[nextBranchIndex][0]
            #thisBlk.nextBlkHash[nextBranchIndex][1] = True
            ## If we're about to search the last branch of this branchNode, remove it from the stack
            #thisBlk = headers[nextNodeHash]
         #else:
            ## If we're at the end of a chain, go back to the last branch
            #leafList.append(thisBlk.theHash)
            #if len(branchNodeStack) == 0:
               #break
            #else:
               #thisBlk = headers[branchNodeStack[-1]]
         #
         #thisBlk.pprint()
         #print 'height:', thisBlk.blkHeight
         #print branchNodeStack
         #if not thisBlk.isLeafNode:
            #if len(thisBlk.nextBlkHash) > 1:
               #branchNodeStack.append(thisBlk.theHash)
#
            #
      ## Step 3: Finally, let's follow each leaf node back to the genesis block, 
      ##         and fix the nextBlkHash values -- convert from list of branches, 
      #         to just the one branch that is the longest.  We can then follow 
      ##         the other leaves back, too, to fix the branches, and just stop 
      ##         when they hit a branch node that has already been fixed
      #
      #leafHeights = [ (headers[L].theHash, headers[L].blkHeight) for L in leafList ]
      #def cmpLeaves(a,b):
         #if   a[1] > b[1]: return  1
         #elif a[1] < b[1]: return -1
         #else:             return  0
      #leafHeights.sort(cmpLeaves)
      #self.topBlockHash = leafHeights[0][0]
#
        #
      #for L in [b[0] for b in leafHeights]:
         #headers[L].nextBlkHash = NOHASH  # Leaves have no next-blk
         #blkhash = headers[L].prevBlkHash
         #nextBlkHash = L
         ## Stop when we get to the start hash, or a block that's already been finalized
         #while (not blkhash == startHash) and isinstance(headers[blkhash].nextBlkHash, list):
            #headers[blkhash].nextBlkHash = nextBlkHash
            #nextBlkHash = blkhash
            #blkhash = headers[blkhash].prevBlkHash
#
      #return self.topBlockHash
      
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
         for i,tx in enumerate(theBlock.blockData.txList):
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


class SavingsAccount(object):
   def __init__(self, name, addrFile, keyFile=None):
      pass
      
