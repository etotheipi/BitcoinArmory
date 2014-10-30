#! /usr/bin/python
import sys
sys.path.append('..')
from armoryengine.Block import *
from armoryengine.ArmoryUtils import *
from armoryengine.PyBtcAddress import *
from armoryengine.Transaction import *
from CppBlockUtils import BlockHeader    as CppBlockHeader
from CppBlockUtils import Tx             as CppTx
from CppBlockUtils import TxIn           as CppTxIn
from CppBlockUtils import TxOut          as CppTxOut
from CppBlockUtils import BtcWallet      as CppBtcWallet
import os
from time import time, sleep

# Use the genesis block to kick things off. (Assume we're on Linux for now.)
blkfile = open('/home/alan/.bitcoin/blocks/blk00000.dat','r')
blkfile.seek(8,0)
genBlock = PyBlock().unserialize(blkfile.read(80 + 1 + 285))
blkfile.close()

print 'Genesis block header:'
genBlock.blockHeader.pprint()
print 'Genesis block tx:'
genBlock.blockData.txList[0].pprint()

# Receiver of the genesis block.
satoshiPubKey = hex_to_binary('04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f')

################################################################################
def printHashEnds(theHash):
   intList = [ord(c) for c in theHash]
   print 'First 4 LE bytes: [%03d,%03d,%03d,%03d]' % tuple(intList[:4]),
   print 'First 4 BE bytes: [%03d,%03d,%03d,%03d]' % tuple(intList[::-1][:4])


def printBlkInfo(blk, suffix):
   print 'BLOCK (', suffix ,')'
   print '   Head  :', binary_to_hex(blk.blockHeader.getHash())
   for i,tx in enumerate(blk.blockData.txList):
      print '      Tx :', binary_to_hex(tx.getHash())

   print '\n'
   print '   ',
   printHashEnds(blk.blockHeader.getHash())
   for i,tx in enumerate(blk.blockData.txList):
      print '   ',
      printHashEnds(tx.getHash())
   print '\n'

   print '   RawHeader  :', binary_to_hex(blk.blockHeader.getHash())
   pprintHex(binary_to_hex(blk.blockHeader.serialize()), indent=' '*12, withAddr=False)
   for i,tx in enumerate(blk.blockData.txList):
      print '       RawTx  :', binary_to_hex(tx.getHash())
      print '       PrevOut: %s' % binary_to_hex(tx.inputs[0].outpoint.serialize())
      pprintHex(binary_to_hex(tx.serialize()), indent=' '*12, withAddr=False)

   print '\n'

################################################################################
def createPyBlock(prevBlkHeader, txlist):
   
   print 'Creating block (%d tx):  Computing nonce...' % len(txlist),
   extraNonce = random.randrange(2**32)
   txlist[0].inputs[0].binScript = int_to_binary(extraNonce, widthBytes=4)
   aGoodNonce = 0
   numTries = 0
   newbh = CppBlockHeader()

   # Keep searching for a good nonce 'til we find one.
   # NB: This script had modded the timestamp if a good nonce wasn't found. (See
   # http://bitcoin.stackexchange.com/questions/5048/what-is-the-extranonce for
   # more info.) The C++ block's timestamp is now read-only, so we just bump the
   # nonce.
   while aGoodNonce == 0:
      blk = PyBlock(prevBlkHeader, txlist)
      newbh = CppBlockHeader()
      newbh.unserialize_1_(blk.blockHeader.serialize())
      aGoodNonce = newbh.findNonce()
      numTries += 1
      extraNonce += 1
      txlist[0].inputs[0].binScript = int_to_binary(extraNonce, widthBytes=4)

   blk.blockHeader.nonce = aGoodNonce
   blk.blockHeader.timestamp = newbh.getTimestamp()
   print 'Done!'
   return blk


# We have to have multiple addresses.
AddrA  = PyBtcAddress().createFromPublicKey(satoshiPubKey)
AddrB  = PyBtcAddress().createFromPrivateKey(hex_to_int('bb'*32))
AddrC  = PyBtcAddress().createFromPrivateKey(hex_to_int('cc'*32))
AddrD  = PyBtcAddress().createFromPrivateKey(hex_to_int('dd'*32))
print 'Addr A: %s' % AddrA.getAddrStr(), ' (Satoshi)'
for a,s in ([AddrB,'B'], [AddrC, 'C'], [AddrD, 'D']):
   print 'Addr %s: %s (PrivKey:%s)' % ( s, a.getAddrStr(), binary_to_hex(a.serializePlainPrivateKey()))

btcValue = lambda btc: btc*(10**8)
COINBASE = -1

#Block 1
Blk1_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrB, btcValue(50)]] )
Blk1      = createPyBlock(genBlock.blockHeader, [Blk1_Tx0] )
printBlkInfo(Blk1, '1')


#Block 2
Blk2_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrB, btcValue(50)]] )
Blk2_Tx1  = PyCreateAndSignTx_old( [[AddrB, Blk1.tx(0), 0]], [[AddrC, btcValue(10)], \
                                                          [AddrB, btcValue(40)]] )
Blk2      = createPyBlock(Blk1.blockHeader, [Blk2_Tx0, Blk2_Tx1] )
printBlkInfo(Blk2, '2')


#Block 3
Blk3_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrC, btcValue(50)]] )  # will be reversed
Blk3_Tx1  = PyCreateAndSignTx_old( [[AddrB, Blk2.tx(1), 1]], [[AddrD, btcValue(40)]] )  # will be in both chains
Blk3_Tx2  = PyCreateAndSignTx_old( [[AddrC, Blk2.tx(1), 0]], [[AddrD, btcValue(10)]] )  # will be reversed
Blk3      = createPyBlock(Blk2.blockHeader, [Blk3_Tx0, Blk3_Tx1, Blk3_Tx2] )
printBlkInfo(Blk3, '3')


#Block 4
Blk4_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrA, btcValue(50)]] )
Blk4_Tx1  = PyCreateAndSignTx_old( [[AddrB, Blk2.tx(0), 0]], [[AddrD, btcValue(50)]] )  # will be moved blk5A
Blk4      = createPyBlock(Blk3.blockHeader, [Blk4_Tx0, Blk4_Tx1] )
printBlkInfo(Blk4, '4')


#Block 3-alternate
Blk3A_Tx0 = PyCreateAndSignTx_old( [COINBASE],               [[AddrD, btcValue(50)]] )
Blk3A_Tx1 = PyTx().unserialize(Blk3.tx(1).serialize())
Blk3A_Tx2 = PyCreateAndSignTx_old( [[AddrC, Blk2.tx(1), 0]], [[AddrB, btcValue(10)]] )
Blk3A        = createPyBlock(Blk2.blockHeader, [Blk3A_Tx0, Blk3A_Tx1, Blk3A_Tx2] )
printBlkInfo(Blk3A, '3A')


#Block 4-alternate
Blk4A_Tx0 = PyCreateAndSignTx_old( [COINBASE],             [[AddrA, btcValue(50)]] )
Blk4A        = createPyBlock(Blk3A.blockHeader, [Blk4A_Tx0])
printBlkInfo(Blk4A, '4A')

#Block 5-alternate
Blk5A_Tx0 = PyCreateAndSignTx_old( [COINBASE],             [[AddrA, btcValue(50)]] )
Blk5A_Tx1 = PyTx().unserialize(Blk4.tx(1).serialize())
Blk5A        = createPyBlock(Blk4A.blockHeader, [Blk5A_Tx0, Blk5A_Tx1] )
printBlkInfo(Blk5A, '5A')


################################################################################
# Now serialize the block data into .dat files so we can feed them into a 
# program that claims to handle reorgs

def writeBlkBin(fileHandle, blk):
   fileHandle.write( hex_to_binary('f9beb4d9') )
   fileHandle.write( int_to_binary(blk.getSize(), widthBytes=4) )
   fileHandle.write( blk.serialize() )

def writeBlkPrettyHex(fileHandle, blk):
   fileHandle.write( 'f9beb4d9' + '\n')
   fileHandle.write( int_to_hex(blk.getSize(), widthBytes=4) + '\n');
   fileHandle.write( prettyHex(binary_to_hex(blk.blockHeader.serialize()), \
                              indent=' '*6, withAddr=False) + '\n')
   fileHandle.write( int_to_hex(blk.getNumTx())  + '\n')
   for tx in blk.blockData.txList:
      fileHandle.write( prettyHex(binary_to_hex(tx.serialize()), \
                              indent=' '*6, withAddr=False) + '\n')
   fileHandle.write('\n')

# Make sure the directory exists.
filePath = os.path.join(os.getcwd(), "reorgTest")
try:
   os.makedirs(filePath)
except OSError as exception:
   if exception.errno != errno.EEXIST:
      raise

# Write the files.
rtfile = open('reorgTest/reorgTest.hex','w+')
def pr(prstr):
   print prstr
   rtfile.write(prstr + '\n')

pr('\n\nWriting blocks to ReorgTest/ directory')
pr( 'File path: ' + 'reorgTest/blk_0_to_4.dat' )
blkFirstChain = open('reorgTest/blk_0_to_4.dat','wb+')
for blk in [genBlock, Blk1, Blk2, Blk3, Blk4]:
   writeBlkBin(blkFirstChain, blk)
   writeBlkPrettyHex(rtfile, blk)
blkFirstChain.close()

for blk,suffix in [[Blk3A,'3A'], [Blk4A, '4A'], [Blk5A, '5A']]:
   filename = 'reorgTest/blk_%s.dat' % suffix
   pr( 'File path: ' + filename + '\n')
   blkAlt = open(filename, 'wb+')
   sleep(1)
   writeBlkBin(blkAlt, blk)
   writeBlkPrettyHex(rtfile, blk)

   blkAlt.close()

pr( '\nDone!')
