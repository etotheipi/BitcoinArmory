#! /usr/bin/python
from pybtcengine import *
import os
from time import time


blkfile = open('/home/alan/.bitcoin/blk0001.dat','r')
blkfile.seek(8,0)
genBlock = PyBlock().unserialize(blkfile.read(80 + 1 + 285))
blkfile.close()

print 'Genesis block header:'
genBlock.blockHeader.pprint()
print 'Genesis block tx:'
genBlock.blockData.txList[0].pprint()


satoshiPubKey = hex_to_binary('04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f')

   

# We have to have a 
AddrA  = PyBtcAddress().createFromPublicKey(satoshiPubKey)
AddrB  = PyBtcAddress().generateNew()
AddrC  = PyBtcAddress().generateNew()
AddrD  = PyBtcAddress().generateNew()
print 'Addr A:', AddrA.getAddrStr(), ' (Satoshi)'
print 'Addr B:', AddrB.getAddrStr()
print 'Addr C:', AddrC.getAddrStr()
print 'Addr D:', AddrD.getAddrStr()

btcValue = lambda btc: btc*(10**8)


#Block 1
Blk1_Tx0  = PyCreateAndSignTx(    [-1],                [[AddrB, btcValue(50)]] )

#Block 2
Blk2_Tx0  = PyCreateAndSignTx(    [-1],                [[AddrB, btcValue(50)]] )
Blk2_Tx1  = PyCreateAndSignTx( [[AddrB, Blk1_Tx0, 0]], [[AddrC, btcValue(10)], \
                                               [AddrB, btcValue(40)]] )

#Block 3
Blk3_Tx0  = PyCreateAndSignTx(    [-1],                [[AddrC, btcValue(50)]] )
Blk3_Tx1  = PyCreateAndSignTx( [[AddrB, Blk2_Tx1, 1]], [[AddrD, btcValue(40)]] )
Blk3_Tx2  = PyCreateAndSignTx( [[AddrC, Blk2_Tx1, 0]], [[AddrD, btcValue(10)]] )

#Block 4
Blk4_Tx0  = PyCreateAndSignTx(    [-1],                [[AddrA, btcValue(50)]] )

#Block 3-alternate
Blk3A_Tx0 = PyCreateAndSignTx(    [-1],                [[AddrA, btcValue(50)]] )
Blk3A_Tx1 = PyCreateAndSignTx( [[AddrB, Blk2_Tx1, 1]], [[AddrD, btcValue(40)]] )
Blk3A_Tx2 = PyCreateAndSignTx( [[AddrC, Blk2_Tx1, 0]], [[AddrB, btcValue(10)]] )

#Block 4-alternate
Blk4A_Tx0 = PyCreateAndSignTx(    [-1],                [[AddrA, btcValue(50)]] )

#Block 5-alternate
Blk5A_Tx0 = PyCreateAndSignTx(    [-1],                [[AddrA, btcValue(50)]] )


################################################################################
# Finally, actually create the blocks

################################################################################
def findNonce(blkHeader, nZeros=4):
   startTime = time()
   for n in xrange(0):
      blkHeader.nonce = n
      theHash = hash256(blkHeader.serialize())
      if theHash[-nZeros:] == '\x00'*nZeros:
         break
   print 'Time to execute nonce search:', (time() - startTime), 'sec'
   return blkHeader.nonce

def printHashEnds(theHash):
   intList = [ord(c) for c in theHash]
   print 'First 4 LE bytes:', intList[:4], 'First 4 BE bytes:', intList[::-1][:4]

################################################################################
def createPyBlock(prevBlkHeader, txlist):
   print 'Creating block (%d tx):  Computing nonce...' % len(txlist),
   blk = PyBlock(prevBlkHeader, txlist)
   aGoodNonce = findNonce(blk.blockHeader, 4)
   blk.blockHeader.nonce = aGoodNonce
   print 'Done!  (%d)' % aGoodNonce
   print '   Header:', binary_to_hex(blk.blockHeader.getHash())
   print '         :', printHashEnds(blk.blockHeader.getHash())
   print '   Prev  :', binary_to_hex(blk.blockHeader.prevBlkHash)
   for i,tx in enumerate(txlist):
      print '   Tx %d  :'%i, binary_to_hex(tx.getHash())
      print '          :', printHashEnds(tx.getHash())
   return blk


Blk1 = createPyBlock(genBlock.blockHeader, [Blk1_Tx0] )
Blk2 = createPyBlock(Blk1.blockHeader,     [Blk2_Tx0, Blk2_Tx1] )
Blk3 = createPyBlock(Blk2.blockHeader,     [Blk3_Tx0, Blk3_Tx1, Blk3_Tx2] )
Blk4 = createPyBlock(Blk3.blockHeader,     [Blk4_Tx0] )

Blk3A = createPyBlock(Blk2.blockHeader,    [Blk3A_Tx0, Blk3A_Tx1, Blk3A_Tx2] )
Blk4A = createPyBlock(Blk3A.blockHeader,   [Blk4A_Tx0])
Blk5A = createPyBlock(Blk4A.blockHeader,   [Blk5A_Tx0])


################################################################################
# Now serialize the block data into .dat files so we can feed them into a 
# program that claims to handle reorgs

def writeBlk(fileHandle, blk):
   blkFirstChain.write( hex_to_binary('f9beb4d9') )
   blkFirstChain.write( int_to_binary(blk.getSize(), widthBytes=4) )
   blkFirstChain.write( blk.serialize() )
   print 'Block:'
   print '  ', 'f9beb4d9'
   print '  ', int_to_hex(blk.getSize(), widthBytes=4)
   print '  ', prettyHex(binary_to_hex(blk.blockHeader.serialize()), '   ', False)
   print '  ', int_to_hex(blk.getNumTx(), widthBytes=1)
   for tx in blk.blockData.txList:
      print '  ', prettyHex(binary_to_hex(tx.serialize()), '   ', False)
   

print '\n\nWriting blocks to ReorgTest/ directory'
blkFirstChain = open('ReorgTest/blk_0_to_4.dat','wb')
for blk in [genBlock, Blk1, Blk2, Blk3, Blk4]:
   writeBlk(blkFirstChain, blk)
blkFirstChain.close()

for blk,suffix in [[Blk3A,'3A'], [Blk4A, '4A'], [Blk5A, '5A']]:
   blkAlt = open('ReorgTest/blk_%s.dat'%suffix,'wb')
   writeBlk(blkAlt, blk)
   blkAlt.close()

print '\nDone!'
