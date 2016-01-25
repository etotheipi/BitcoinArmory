#! /usr/bin/python
import sys
import errno
import argparse
from armoryengine.Block import *
from armoryengine.ArmoryUtils import *
from armoryengine.PyBtcAddress import *
from armoryengine.Transaction import *
from armoryengine.MultiSigUtils import *
from CppBlockUtils import BlockHeader    as CppBlockHeader
from CppBlockUtils import Tx             as CppTx
from CppBlockUtils import TxIn           as CppTxIn
from CppBlockUtils import TxOut          as CppTxOut
from CppBlockUtils import BtcWallet      as CppBtcWallet
import os
from time import time, sleep

### NOTE: THIS MUST BE RUN FROM THE ARMORY ROOT DIRECTORY, OTHERWISE IT'LL FAIL!

if not os.path.isdir('cppForSwig/reorgTest'):
   print "This program must be run from the armory source root dir. Copy this " \
      "file to the root directory and run it from there."
   sys.exit(1);

# Real blocks have to be properly mined, which takes hours. If messing with this
# file, using fake blocks will be a lot faster and allow almost all C++ unit
# tests to pass. (Command line args are ideal but this script collides with the
# parser in ArmoryUtils.)
fakeBlocks=False

# Use the genesis block to kick things off. (Might not work on Windows.)
blkfile = open(os.environ['HOME'] + '/.bitcoin/blocks/blk00000.dat','r')
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
def createPyBlock(prevBlkHeader, txlist, useMinDiff=True):
   print 'Creating block (%d tx):  Computing nonce...' % len(txlist)
   extraNonce = random.randrange(2**32)
   txlist[0].inputs[0].binScript = int_to_binary(extraNonce, widthBytes=4)
   aGoodNonce = False
   numTries = 0
   newbh = CppBlockHeader()

   # Keep searching for a good nonce 'til we find one. See
   # http://bitcoin.stackexchange.com/questions/5048/what-is-the-extranonce for
   # more info on why we mod the timestamp instead of the coinbase script
   # (extraNonce).
   nonceVal = -1
   while not aGoodNonce:
      blk = PyBlock(prevBlkHeader, txlist)
      blk.blockHeader.timestamp += numTries

      # Set up the difficulty-related vars. Assume min diff (0x1d00ffff) unless
      # indicated otherwise, then use values for next-highest diff (0x1d00fffe).
      diffHex = 'FFFF0000000000000000000000000000000000000000000000000000h'
      if not useMinDiff:
         blk.blockHeader.diffBits = hex_to_binary('1d00fffe', BIGENDIAN)
         diffHex = 'FFFE0000000000000000000000000000000000000000000000000000h'

      newbh = CppBlockHeader()
      newbh.unserialize_1_(blk.blockHeader.serialize())
      if fakeBlocks:
         nonceVal = 1414
         aGoodNonce = True
      else:
         # C++ returns -1 if a nonce isn't found.
         nonceVal = newbh.findNonce(diffHex)
         if nonceVal != -1:
            aGoodNonce = True
      numTries += 1

   blk.blockHeader.nonce = nonceVal
   blk.blockHeader.timestamp = newbh.getTimestamp()
   print 'Done!'
   return blk


# We have to have multiple addresses.
AddrA  = PyBtcAddress().createFromPublicKey(satoshiPubKey)
AddrB  = PyBtcAddress().createFromPrivateKey(hex_to_int('bb'*32))
AddrC  = PyBtcAddress().createFromPrivateKey(hex_to_int('cc'*32))
AddrD  = PyBtcAddress().createFromPrivateKey(hex_to_int('dd'*32))
AddrE  = PyBtcAddress().createFromPrivateKey(hex_to_int('ee'*32))
AddrF  = PyBtcAddress().createFromPrivateKey(hex_to_int('ef'*32))
print 'Addr A: %s' % AddrA.getAddrStr(), ' (Satoshi)'
for a,s in ([AddrB, 'B'], [AddrC, 'C'], [AddrD, 'D'], [AddrE, 'E'], [AddrF, 'F']):
   print 'Addr %s: %s (PrivKey:%s)' % (s, a.getAddrStr(),
                                       binary_to_hex(a.serializePlainPrivateKey()))

# Lists of who signs off on lockbox transactions.
signList1A = []
signList1B = []
signList1C = []
signList2 = []
signList1A.append(AddrB)
signList1B.append(AddrC)
signList1C.append(AddrB)
signList1C.append(AddrC)
signList2.append(AddrD)
signList2.append(AddrE)

# Let's create a couple of lockboxes too.
name = 'LB 1'
descr = 'Lockbox 1 has B & C (1-of-2)'
m = 1
n = 2
key1 = DecoratedPublicKey(AddrB.getPubKey().toBinStr())
key2 = DecoratedPublicKey(AddrC.getPubKey().toBinStr())
keyList1 = []
keyList1.append(key1)
keyList1.append(key2)
LB1 = MultiSigLockbox(name, descr, m, n, keyList1)
name = 'LB 2'
descr = 'Lockbox 2 has D & E (2-of-2)'
m = 2
n = 2
key3 = DecoratedPublicKey(AddrD.getPubKey().toBinStr())
key4 = DecoratedPublicKey(AddrE.getPubKey().toBinStr())
keyList2 = []
keyList2.append(key3)
keyList2.append(key4)
LB2 = MultiSigLockbox(name, descr, m, n, keyList2)

# Get the data needed for the C++ unit tests
print 'LB1 B58 ID: %s' % LB1.uniqueIDB58
print 'LB1 scrAddr: %s' % binary_to_hex(LB1.scrAddr)
print 'LB1 scrAddr (P2SH): %s' % binary_to_hex(LB1.p2shScrAddr)
print 'LB2 B58 ID: %s' % LB2.uniqueIDB58
print 'LB2 scrAddr: %s' % binary_to_hex(LB2.scrAddr)
print 'LB2 scrAddr (P2SH): %s' % binary_to_hex(LB2.p2shScrAddr)

btcValue = lambda btc: btc*(10**8)
COINBASE = -1

#Block 1
Blk1_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrB, btcValue(50)]] )
Blk1      = createPyBlock(genBlock.blockHeader, [Blk1_Tx0] )
printBlkInfo(Blk1, '1')

#Block 2
Blk2_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrB, btcValue(50)]] )
Blk2_Tx1  = PyCreateAndSignTx_old( [[AddrB, Blk1.tx(0), 0]], [[LB1, btcValue(15), True], \
                                                              [LB2, btcValue(10), False],
                                                              [AddrB, btcValue(25)]] )
Blk2_Tx2  = PyCreateAndSignTx_old( [[AddrB, Blk2_Tx1, 2]], [[AddrF, btcValue(20)],
                                                            [AddrB, btcValue(5)]] )
Blk2      = createPyBlock(Blk1.blockHeader, [Blk2_Tx0, Blk2_Tx1, Blk2_Tx2] )
printBlkInfo(Blk2, '2')

#Block 3
Blk3_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrC, btcValue(50)]] )  # will be reversed
Blk3_Tx1  = PyCreateAndSignTx_old( [[AddrF, Blk2.tx(2), 0]], [[AddrD, btcValue(5)],
                                                              [AddrF, btcValue(15)]] )  # will be in both chains
Blk3_Tx2  = PyCreateAndSignTx_old( [[LB1, Blk2.tx(1), 0, signList1A, True]], [[AddrE, btcValue(5)],
                                                                              [LB1, btcValue(10), False]] )  # will be reversed
Blk3_Tx3  = PyCreateAndSignTx_old( [[LB2, Blk2.tx(1), 1, signList2, False]], [[AddrC, btcValue(5)],
                                                                              [LB2, btcValue(5), True]] )  # will be reversed
Blk3_Tx4  = PyCreateAndSignTx_old( [[AddrB, Blk2.tx(0), 0],
                                    [AddrB, Blk2.tx(2), 1]], [[AddrE, btcValue(25)],
                                                              [AddrB, btcValue(30)]] )  # will be in both chains
Blk3_Tx5  = PyCreateAndSignTx_old( [[AddrF, Blk3_Tx1, 1]], [[LB2, btcValue(10), False],
                                                            [AddrF, btcValue(5)]] )  # will be in both chains
Blk3      = createPyBlock(Blk2.blockHeader, [Blk3_Tx0, Blk3_Tx1, Blk3_Tx2, Blk3_Tx3, Blk3_Tx4, Blk3_Tx5] )
printBlkInfo(Blk3, '3')

#Block 4
Blk4_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrD, btcValue(50)]] )  # will be reversed
Blk4_Tx1  = PyCreateAndSignTx_old( [[LB1, Blk3.tx(2), 1, signList1C, False]], [[AddrF, btcValue(5)],
                                                                               [LB1, btcValue(5), False]] )  # will be reversed
Blk4_Tx2  = PyCreateAndSignTx_old( [[LB2, Blk3.tx(3), 1, signList2, True]], [[AddrD, btcValue(5)]] )  # will be reversed
Blk4_Tx3  = PyCreateAndSignTx_old( [[AddrC, Blk3.tx(0), 0],
                                    [AddrC, Blk3.tx(3), 0]], [[LB1, btcValue(25), True],
                                                              [LB2, btcValue(20), False],
                                                              [AddrC, btcValue(10)]] )  # will be in both chains
Blk4      = createPyBlock(Blk3.blockHeader, [Blk4_Tx0, Blk4_Tx1, Blk4_Tx2, Blk4_Tx3] )
printBlkInfo(Blk4, '4')

#Block 5
Blk5_Tx0  = PyCreateAndSignTx_old( [COINBASE],               [[AddrB, btcValue(50)]] )  # will be reversed
Blk5_Tx1  = PyCreateAndSignTx_old( [[AddrB, Blk3.tx(4), 1]], [[AddrC, btcValue(10)],
                                                              [AddrB, btcValue(20)]] )  # will be in both chains
Blk5_Tx2  = PyCreateAndSignTx_old( [[AddrF, Blk4.tx(1), 0]], [[AddrD, btcValue(5)]] )  # will be reversed
Blk5      = createPyBlock(Blk4.blockHeader, [Blk5_Tx0, Blk5_Tx1, Blk5_Tx2] )
printBlkInfo(Blk5, '5')

#Block 4-alternate
Blk4A_Tx0 = PyCreateAndSignTx_old( [COINBASE],             [[AddrF, btcValue(50)]] )
Blk4A        = createPyBlock(Blk3.blockHeader, [Blk4A_Tx0])
printBlkInfo(Blk4A, '4A')

#Block 5-alternate  (Uses a slightly higher difficulty to trigger a reorg)
Blk5A_Tx0 = PyCreateAndSignTx_old( [COINBASE],             [[AddrD, btcValue(50)]] )
Blk5A_Tx1 = PyTx().unserialize(Blk4.tx(1).serialize())
Blk5A_Tx2 = PyTx().unserialize(Blk4.tx(2).serialize())
Blk5A        = createPyBlock(Blk4A.blockHeader, [Blk5A_Tx0, Blk5A_Tx1, Blk5A_Tx2], False )
printBlkInfo(Blk5A, '')


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

# Write a C++header file that'll have all the data from this test. This makes it
# easier to make changes on both Python and C++.
addrfile = open('cppForSwig/reorgTest/blkdata.h', 'w+')
addrfile.write("// DO NOT MODIFY THIS FILE\n")
addrfile.write("// this file generated by createTestChain.py. Modify that script instead.\n")
addrfile.write("#ifndef BLKDATA_H\n#define BLKDATA_H\n\n")

addrfile.write("namespace TestChain\n{\n")
addrfile.write("const BinaryData addrA = BinaryData::CreateFromHex(\"" + binary_to_hex(AddrA.getAddr160()) + "\");\n")
addrfile.write("const BinaryData scrAddrA = HASH160PREFIX + addrA;\n")

for a,s in ([AddrB, 'B'], [AddrC, 'C'], [AddrD, 'D'], [AddrE, 'E'], [AddrF, 'F']):
   addrfile.write("const BinaryData addr" + s + " = BinaryData::CreateFromHex(\"" + binary_to_hex(a.getAddr160()) + "\");\n")
   addrfile.write("const BinaryData scrAddr" + s + " = HASH160PREFIX + addr" + s + ";\n")
   addrfile.write("const BinaryData privKeyAddr" + s + " = BinaryData::CreateFromHex(\"" + binary_to_hex(a.serializePlainPrivateKey()) + "\");\n")

addrfile.write("\n")

# Write the information
addrfile.write("// LB1 = AddrB + AddrC\n")
addrfile.write("// LB2 = AddrD + AddrE\n")
addrfile.write("const string lb1B58ID = \"" + LB1.uniqueIDB58 + "\";\n")
addrfile.write("const BinaryData lb1ScrAddr = BinaryData::CreateFromHex(\"" + binary_to_hex(LB1.scrAddr) + "\");\n")
addrfile.write("const BinaryData lb1ScrAddrP2SH = BinaryData::CreateFromHex(\"" + binary_to_hex(LB1.p2shScrAddr) + "\");\n")
addrfile.write("const string lb2B58ID = \"" + LB2.uniqueIDB58 + "\";\n")
addrfile.write("const BinaryData lb2ScrAddr = BinaryData::CreateFromHex(\"" + binary_to_hex(LB2.scrAddr) + "\");\n")
addrfile.write("const BinaryData lb2ScrAddrP2SH = BinaryData::CreateFromHex(\"" + binary_to_hex(LB2.p2shScrAddr) + "\");\n\n")

for blk,name in ([genBlock, '0'], [Blk1, '1'], [Blk2, '2'], [Blk3, '3'], \
      [Blk4, '4'], [Blk5, '5'], [Blk4A, '4A'], [Blk5A, '5A']):
   blkfile = open('cppForSwig/reorgTest/blk_' + name + '.dat','wb+')
   writeBlkBin(blkfile, blk)
   blkfile.close()
   
   addrfile.write("const BinaryData blkHash" + name + " = BinaryData::CreateFromHex(\"" + binary_to_hex(blk.blockHeader.theHash) + "\");\n")
addrfile.write("\n")

# Finally, write Blk5/Tx1 & Blk4/Tx1 to indiv. files for specialized tests.
b5tx1File = open('cppForSwig/reorgTest/ZCtx.tx','wb+')
b5tx1File.write(Blk5_Tx1.serialize())
addrfile.write("const unsigned int zcTxSize = " + str(b5tx1File.tell()) + ";\n")
addrfile.write("const string zcTxHash256 = \"" + binary_to_hex(hash256(Blk5_Tx1.serialize())) + "\";\n")
b5tx1File.close()
b4tx1File = open('cppForSwig/reorgTest/LBZC.tx','wb+')
b4tx1File.write(Blk4_Tx1.serialize())
addrfile.write("const unsigned int lbZCTxSize = " + str(b4tx1File.tell()) + ";\n")
b4tx1File.close()

addrfile.write("}\n")
addrfile.write("\n#endif\n")
addrfile.close()
