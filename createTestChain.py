#! /usr/bin/python
from pybtcengine import *


blkfile = open('/home/alan/.bitcoin/blk0001.dat','r')
blkfile.seek(8,0)
genBlock = PyBlockHeader().unserialize(blkfile.read(80))
numTx = blkfile.read(1)
genTx = PyTx().unserialize(blkfile.read(285))

print 'Genesis block header:'
genBlock.pprint()
print 'Genesis block tx:'
genTx.pprint()


################################################################################
def findDiff1Nonce(blkHeader):
   for n in range(2**33):
      h.nonce = n
      theHash = hash256(h.serialize())
      if theHash[-4:] == '\x00\x00\x00\x00':
         return h
   print 'No nonce found!'

################################################################################
# We will reference src TxOuts by the blkNum and TxIndex
#  Src TxOut ~ {tx, txoutIndex, BtcAddr}   /  COINBASE = -1
#  Dst TxOut ~ {BtcAddr, value}
def createTx(srcTxOuts, dstAddrVal):
   tx = PyTx()
   tx.numInputs  = len(srcTxOuts)
   tx.numOutputs = len(dstAddrs)
   tx.inputs     = []
   tx.outputs    = []

   coinbaseTx = False
   if tx.numInputs==1 and srcTxOuts[0] == -1:
      coinbaseTx = True
      
   
   ####################
   for i in range(tx.numOutputs):
      txout = PyTxOut()
      txout.value = dstAddrVal[i][1]
      dstAddr160 = dstAddr[i][0].getAddr160()
      if(coinbaseTx):
         txout.binPKScript = ''.join(['\x41', \
                                      dstAddr160,
                                      opCodeLookup['OP_CHECKSIG']])
      else:
         txout.binPKScript = ''.join([opCodeLookup['OP_DUP'], \
                                      opCodeLookup['OP_HASH160'], \
                                      '\x14', \
                                      dstAddr160,
                                      opCodeLookup['OP_EQUALVERIFY'], \
                                      opCodeLookup['OP_CHECKSIG']])
      tx.outputs.append(txout)

                                      
   ####################
   for i in range(tx.inputs):
      txin = PyTxIn()
      txin.outpoint = PyOutPoint()
      if(coinbaseTx):
         txin.outpoint.txOutHash = '\x00'*32
         txin.outpoint.index     = '\xff'*4
      else:
         txin.outpoint.txOutHash = hash256(srcTxOuts[0][0].serialize())
         txin.outpoint.index     = srcTxOuts[0][1]
      txin.binScript = ''.join(['\xaa\xbb\xcc\xdd'])
      txin.intSeq = 2**32-1
      tx.inputs.append(txin)                                      
      


   ####################
   # Now we apply the ultra-complicated signature procedure
   # We need a copy of the Tx with all the txin scripts blanked out
   txCopySerialized = tx.serialize()
   for i in range(tx.inputs):
      if coinbaseTx:
         pass # no sig on coinbase txs
      else:
         txCopy = PyTx().unserialize(txCopySerialized)
         thisTxIn   = txCopy.inputs[i]
         txoutIdx   = srcTxOuts[i][1]
         prevTxOut  = srcTxOuts[i][0].outputs[txoutIdx]
         btcAddr    = srcTxOuts[i][2]
         hashCode   = int_to_binary(hashtype, widthBytes=4)
         binToSign  = ''

         # Copy the script of the TxOut we're spending, into the txIn script
         thisTxIn.binScript = prevTxOut.binPKScript
         binToSign = hash256(txCopy.serialize() + hashCode)
         signature = addrPrivKey.generateDERSignature(binToSign) + '\x01'
         if len(prevTxOut.binPKScript) > 26:
            #Spend-CB: only Sig needed 
            tx.inputs[i].binScript = signature
         else
            tx.inputs[i].binScript = signature + '\x41' + addrPrivKey
      
   return tx

   
txlist = []


AddrA  = PyBtcAddress().createFromPublicKey(hex_to_binary('04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f'))
AddrB  = PyBtcAddress().generateNew()
AddrC  = PyBtcAddress().generateNew()
AddrD  = PyBtcAddress().generateNew()

def btcValue(btc):
   return btc*(10**8)

Blk0_Tx0 = createTx(    [-1],                [[AddrA, btcValue(50)]]    )
Blk1_Tx0 = createTx(    [-1],                [[AddrB, btcValue(50)]]    )
Blk2_Tx0 = createTx(    [-1],                [[AddrB, btcValue(50)]]    )
Blk2_Tx1 = createTx( [[Blk1_Tx0, 0, AddrB]], [[ AddrC,  btcValue(10)],
                                              [ AddrB,  btcValue(40)]] )
Blk3_Tx0 = createTx(    [-1],                [[AddrC, btcValue(50)]]    )
Blk3_Tx1 = createTx( [[Blk2_Tx1, 1, AddrB]]  [[AddrD, btcValue(40)]]    )
Blk3_Tx2 = createTx( [[Blk2_Tx1, 0, AddrC]]  [[AddrD, btcValue(10)]]    )












