#! /usr/bin/python

from sys import path
path.append('..')
from pybtcengine import *
from datetime import datetime

print 'Importing BlockUtils module...',
from BlockUtils import *
print 'Done!'
print ''

print 'Constructing BlockDataManager... ',
bdm = BlockDataManager_FullRAM.GetInstance()
print 'Done!'
print ''

print 'Loading blk0001.dat...            ',
bdm.readBlkFile_FromScratch('../blk0001.dat')
print 'Done!'
print ''

print 'Organizing the blockchain...      ',
bdm.organizeChain();
print 'Done!'
print ''

print 'Getting top block of the chain... ',
top = bdm.getTopBlockHeader()
top.printHeader()
print 'Done!...'
print ''

print 'Getting top block prevHash ...    ',
prevhash = top.getPrevHash()
print prevhash
print 'Done!'
print ''

print 'Getting almost-top-block'
topm1 = bdm.getHeaderByHash(prevhash.copy())
topm1.printHeader()
print 'Done!'
print ''

print 'Getting Block 170...'
topm1 = bdm.getHeaderByHeight(170)
topm1.printHeader()
print 'Done!'
print ''

print 'Accessing some top-block properties...'
print 'Difficulty:', top.getDifficulty()
print 'Diff Sum  :', top.getDifficultySum()
print 'Timestamp :', top.getTimestamp()
print ''

def unixTimeToFormatStr(unixTime, formatStr='%Y-%b-%d %I:%M%p'):
   dtobj = datetime.fromtimestamp(unixTime)
   dtstr = dtobj.strftime(formatStr)
   return dtstr[:-2] + dtstr[-2:].lower()

def hash160ToAddr(hash160):
   b = PyBtcAddress().createFromPublicKeyHash160(hash160)
   return b.getAddrStr()

def getTimeOfTx(txhash):
   blkTime = bdm.getTxByHash(txhash).getBlockTimestamp()

print 'Accessing some transactions...'
someBlk = bdm.getHeaderByHeight(100000)
print 'TxList for block #', someBlk.getBlockHeight()
topTxPtrList = someBlk.getTxRefPtrList()
print 'NumTx:', len(topTxPtrList)
for txptr in topTxPtrList:
   print binary_to_hex(txptr.getThisHash().toString(), BIGENDIAN),
   blkHead = txptr.getHeaderPtr()
   print 'Blk:', blkHead.getBlockHeight(),
   print 'Timestamp:', unixTimeToFormatStr(blkHead.getTimestamp())



   
print 'Scanning Blockchain for transactions...',
wallet = BtcWallet()
addrStr1 = BinaryData(hex_to_binary("abda0c878dd7b4197daa9622d96704a606d2cd14"))
addrStr2 = BinaryData(hex_to_binary("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"))
addrStr3 = BinaryData(hex_to_binary("f62242a747ec1cb02afd56aac978faf05b90462e"))
wallet.addAddress(addrStr1);
wallet.addAddress(addrStr2);
wallet.addAddress(addrStr3);
bdm.scanBlockchainForTx_FromScratch(wallet);
print 'Done!'

print 'Wallet addresses: ', wallet.getNumAddr()
for i in range(wallet.getNumAddr()):
   addr = wallet.getAddrByIndex(i)
   print '\t', binary_to_hex(addr.getAddrStr20().toString())[:8],
   print '\tBalance:', coin2str(addr.getBalance())

print 'Getting Ledger for addresses:'
ledger1 = wallet.getTxLedger()
for i,l in enumerate(ledger1):
   print i, 
   print '\tFrom/To:', hash160ToAddr(l.getAddrStr20().toString()), 
   print '\tBlock:',   l.getBlockNum(), 
   print '\tAmt:',     coin2str(l.getValue()),
   txptr = bdm.getTxByHash(l.getTxHash())
   headptr = txptr.getHeaderPtr()
   htime = headptr.getTimestamp()
   print '\tRcvd:', unixTimeToFormatStr(htime)


print ''



