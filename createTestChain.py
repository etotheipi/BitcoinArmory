#! /usr/bin/python
from pybtcengine import *
from CppBlockUtils import BlockHeader    as CppBlockHeader
from CppBlockUtils import BlockHeaderRef as CppBlockHeaderRef
from CppBlockUtils import Tx             as CppTx
from CppBlockUtils import TxIn           as CppTxIn
from CppBlockUtils import TxOut          as CppTxOut
from CppBlockUtils import BtcWallet      as CppBtcWallet
import os
from time import time, sleep


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
AddrB  = PyBtcAddress().createFromPrivateKey(hex_to_int('bb'*32))
AddrC  = PyBtcAddress().createFromPrivateKey(hex_to_int('cc'*32))
AddrD  = PyBtcAddress().createFromPrivateKey(hex_to_int('dd'*32))
print 'Addr A: %s' % AddrA.getAddrStr(), ' (Satoshi)'
for a,s in ([AddrB,'B'], [AddrC, 'C'], [AddrD, 'D']):
   print 'Addr %s: %s (PrivKey:%s)' % ( s, a.getAddrStr(), binary_to_hex(a.privKey_serialize()))

btcValue = lambda btc: btc*(10**8)

COINBASE = -1

psp = PyScriptProcessor()
#Block 1
Blk1_Tx0  = PyCreateAndSignTx( [COINBASE],             [[AddrB, btcValue(50)]] )

#Block 2
Blk2_Tx0  = PyCreateAndSignTx( [COINBASE],             [[AddrB, btcValue(50)]] )
Blk2_Tx1  = PyCreateAndSignTx( [[AddrB, Blk1_Tx0, 0]], [[AddrC, btcValue(10)], \
                                                        [AddrB, btcValue(40)]] )

#Block 3
Blk3_Tx0  = PyCreateAndSignTx( [COINBASE],             [[AddrC, btcValue(50)]] )  # will be reversed
Blk3_Tx1  = PyCreateAndSignTx( [[AddrB, Blk2_Tx1, 1]], [[AddrD, btcValue(40)]] )  # will be in both chains
Blk3_Tx2  = PyCreateAndSignTx( [[AddrC, Blk2_Tx1, 0]], [[AddrD, btcValue(10)]] )  # will be reversed

#Block 4
Blk4_Tx0  = PyCreateAndSignTx( [COINBASE],             [[AddrA, btcValue(50)]] )
Blk4_Tx1  = PyCreateAndSignTx( [[AddrB, Blk2_Tx0, 0]], [[AddrD, btcValue(50)]] )  # will be moved blk5A

#Block 3-alternate
Blk3A_Tx0 = PyCreateAndSignTx( [COINBASE],             [[AddrD, btcValue(50)]] )
Blk3A_Tx1 = PyCreateAndSignTx( [[AddrB, Blk2_Tx1, 1]], [[AddrD, btcValue(40)]] )
Blk3A_Tx2 = PyCreateAndSignTx( [[AddrC, Blk2_Tx1, 0]], [[AddrB, btcValue(10)]] )

#Block 4-alternate
Blk4A_Tx0 = PyCreateAndSignTx( [COINBASE],             [[AddrA, btcValue(50)]] )

#Block 5-alternate
Blk5A_Tx0 = PyCreateAndSignTx( [COINBASE],             [[AddrA, btcValue(50)]] )
Blk5A_Tx1 = PyCreateAndSignTx( [[AddrB, Blk2_Tx0, 0]], [[AddrD, btcValue(50)]] )  


################################################################################
# Finally, actually create the blocks

################################################################################
def printHashEnds(theHash):
   intList = [ord(c) for c in theHash]
   print 'First 4 LE bytes:', intList[:4], 'First 4 BE bytes:', intList[::-1][:4]

################################################################################
def createPyBlock(prevBlkHeader, txlist):
   
   print 'Creating block (%d tx):  Computing nonce...' % len(txlist),
   aGoodNonce = 0
   while aGoodNonce == 0:
      extraNonce = random.randrange(2**32)
      txlist[0].inputs[0].binScript = int_to_binary(extraNonce, widthBytes=4)
      blk = PyBlock(prevBlkHeader, txlist)
      newbh = CppBlockHeader()
      newbh.unserialize_1_(blk.blockHeader.serialize())
      aGoodNonce = newbh.findNonce()
      print 'Finished searching for nonce: ', aGoodNonce

   blk.blockHeader.nonce = aGoodNonce
   print 'Done!  Nonce: %d  (extra: %d)' % (aGoodNonce, extraNonce)
   print '   Head  :', binary_to_hex(blk.blockHeader.getHash())
   printHashEnds(blk.blockHeader.getHash())
   print '   RawHeader  :'
   print pprintHex(binary_to_hex(blk.blockHeader.serialize()))
   for i,tx in enumerate(txlist):
      print '   Tx :', binary_to_hex(tx.getHash())
      printHashEnds(tx.getHash())
      print '   RawTx :'
      print pprintHex(binary_to_hex(tx.serialize()))
   return blk



Blk1 = createPyBlock(genBlock.blockHeader, [Blk1_Tx0] )
Blk2 = createPyBlock(Blk1.blockHeader,     [Blk2_Tx0, Blk2_Tx1] )
Blk3 = createPyBlock(Blk2.blockHeader,     [Blk3_Tx0, Blk3_Tx1, Blk3_Tx2] )
Blk4 = createPyBlock(Blk3.blockHeader,     [Blk4_Tx0, Blk4_Tx1] )

Blk3A = createPyBlock(Blk2.blockHeader,    [Blk3A_Tx0, Blk3A_Tx1, Blk3A_Tx2] )
Blk4A = createPyBlock(Blk3A.blockHeader,   [Blk4A_Tx0])
Blk5A = createPyBlock(Blk4A.blockHeader,   [Blk5A_Tx0, Blk5A_Tx1] )


################################################################################
# Now serialize the block data into .dat files so we can feed them into a 
# program that claims to handle reorgs

def writeBlk(fileHandle, blk):
   fileHandle.write( hex_to_binary('f9beb4d9') )
   fileHandle.write( int_to_binary(blk.getSize(), widthBytes=4) )
   fileHandle.write( blk.serialize() )
   print 'Block:'
   print '  ', 'f9beb4d9'
   print '  ', int_to_hex(blk.getSize(), widthBytes=4)
   print '  ', prettyHex(binary_to_hex(blk.blockHeader.serialize()), '   ', False)
   print '  ', int_to_hex(blk.getNumTx(), widthBytes=1)
   for tx in blk.blockData.txList:
      print '  ', prettyHex(binary_to_hex(tx.serialize()), '   ', False)
   

print '\n\nWriting blocks to ReorgTest/ directory'
print 'File path: ',  'reorgTest/blk_0_to_4.dat'
blkFirstChain = open('reorgTest/blk_0_to_4.dat','wb')
for blk in [genBlock, Blk1, Blk2, Blk3, Blk4]:
   writeBlk(blkFirstChain, blk)
blkFirstChain.close()

for blk,suffix in [[Blk3A,'3A'], [Blk4A, '4A'], [Blk5A, '5A']]:
   filename = 'reorgTest/blk_%s.dat' % suffix
   print 'File path: ', filename
   blkAlt = open(filename, 'wb')
   sleep(1)
   writeBlk(blkAlt, blk)
   blkAlt.close()

print '\nDone!'
