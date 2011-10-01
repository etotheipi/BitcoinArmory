#! /usr/bin/python
################################################################################
#                                                                              #
#  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>               #
#  Distributed under the GNU Affero General Public License (AGPL v3)           #
#  See LICENSE or http://www.gnu.org/licenses/agpl.html                        #
#                                                                              #
################################################################################

from sys import path as PYPATH
PYPATH.append('..')
from pybtcengine import *
from datetime import datetime
from os import path

import platform
opsys = platform.system()
blkfile = ''
if 'win' in opsys.lower():
   blkfile = path.join(os.getenv('APPDATA'), 'Bitcoin', 'blk0001.dat')
if 'nix' in opsys.lower() or 'nux' in opsys.lower():
   blkfile = path.join(os.getenv('HOME'), '.bitcoin', 'blk0001.dat')
if 'mac' in opsys.lower() or 'osx' in opsys.lower():
   blkfile = os.path.expanduser('~/Library/Application Support/Bitcoin/blk0001.dat')

print '*'*80
print 'Importing BlockUtils module...',
from CppBlockUtils import *
print 'Done!'
print ''

print 'Constructing BlockDataManager... ',
bdm = BlockDataManager_FullRAM.GetInstance()
print 'Done!'
print ''

print 'Loading blk0001.dat...            '
bdm.readBlkFile_FromScratch(blkfile)
print 'Done!'
print ''

print 'Organizing the blockchain...      ',
bdm.organizeChain();
print 'Done!'
print ''

print '*'*80
print 'Getting top block of the chain... ',
top = bdm.getTopBlockHeader()
top.pprint()
print 'Done!...'
print ''

print 'Getting top block prevHash ...    ',
prevhash = top.getPrevHash()
print prevhash
print 'Done!'
print ''

print 'Getting almost-top-block'
topm1 = bdm.getHeaderByHash(prevhash.copy())
topm1.pprint()
print 'Done!'
print ''

print 'Getting Block 170...'
topm1 = bdm.getHeaderByHeight(170)
topm1.pprint()
print 'Done!'
print ''

print 'Accessing some top-block properties...'
print 'Difficulty:', top.getDifficulty()
print 'Diff Sum  :', top.getDifficultySum()
print 'Timestamp :', top.getTimestamp()
print ''


print '*'*80
print 'Accessing some transactions...'
someBlk = bdm.getHeaderByHeight(100014)
print 'TxList for block #', someBlk.getBlockHeight()
topTxPtrList = someBlk.getTxRefPtrList()
print 'NumTx:', len(topTxPtrList)
for txptr in topTxPtrList:
   print '\n'
   print 'Tx:', binary_to_hex(txptr.getThisHash().toBinStr(), BIGENDIAN)[:16],
   blkHead = txptr.getHeaderPtr()
   print 'Blk:', blkHead.getBlockHeight(),
   print 'Timestamp:', unixTimeToFormatStr(blkHead.getTimestamp()),
   nIn  = txptr.getNumTxIn()
   nOut = txptr.getNumTxOut()
   print '(in,out) = (%d,%d)' % (nIn, nOut)

   for i in range(nIn):
      # TxIns don't always contain the sender... you have to
      # go to find the corresponding TxOut to get it
      txptr.getTxInRef(i).pprint()
      #if txin.isCoinbase():
         #print '\tSender:', '<COINBASE/GENERATION>'.ljust(34),
         #print 'Value: 50 [probably]';
      #else:
         #print '\tSender:', hash160_to_addrStr(bdm.getSenderAddr20(txin).toBinStr()),
         #print 'Value:',  coin2str(bdm.getSentValue(txin))
         

   for i in range(nOut):
      txptr.getTxOutRef(i).pprint()
      #print '\tRecip: ', hash160_to_addrStr(txout.getRecipientAddr().toBinStr()),
      #print 'Value:', coin2str(txout.getValue())



print '*'*80
print '\n\nPrint some random scripts:'
someBlk = bdm.getHeaderByHeight(147570)
print someBlk.pprint()
for tx in someBlk.getTxRefPtrList():
   print 'Tx:', tx.getThisHash().toHexStr(False)
   for i in range(tx.getNumTxIn()):
      print 'TxIn:', i
      txin = tx.getTxInRef(i)
      binScript = txin.getScript().toBinStr()
      if txin.isCoinbase():
         print 'Script: '
         print '   <COINBASE/ARBITRARY>'
         print '  ', binary_to_hex(binScript)
      else:
         pprintScript(binScript)
      print ''
   for i in range(tx.getNumTxOut()):
      print 'TxOut:', i
      binScript = tx.getTxOutRef(i).getScript().toBinStr()
      pprintScript(binScript)
      print ''


   
print '*'*80
print '\n\nScanning Blockchain for transactions...',
wallet = BtcWallet()
addrStr1 = BinaryData(hex_to_binary("abda0c878dd7b4197daa9622d96704a606d2cd14"))
addrStr2 = BinaryData(hex_to_binary("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"))
addrStr3 = BinaryData(hex_to_binary("f62242a747ec1cb02afd56aac978faf05b90462e"))
addrStr4 = BinaryData(hex_to_binary("baa72d8650baec634cdc439c1b84a982b2e596b2"))
addrStr5 = BinaryData(hex_to_binary("6300bf4c5c2a724c280b893807afb976ec78a92b"))
wallet.addAddress(addrStr1);
wallet.addAddress(addrStr2);
wallet.addAddress(addrStr3);
bdm.scanBlockchainForTx_FromScratch(wallet);
print 'Done!'

print 'Wallet addresses: ', wallet.getNumAddr()
for i in range(wallet.getNumAddr()):
   addr = wallet.getAddrByIndex(i)
   print '\t', hash160_to_addrStr(addr.getAddrStr20().toBinStr()),
   print '\tBalance:', coin2str(addr.getBalance())

print 'Getting Ledger for addresses:'
ledger1 = wallet.getTxLedger()
for i,l in enumerate(ledger1):
   print i, 
   print '\tFrom/To:', hash160_to_addrStr(l.getAddrStr20().toBinStr()), 
   print '\tBlock:',   l.getBlockNum(), 
   print '\tAmt:',     coin2str(l.getValue()),
   txptr = bdm.getTxByHash(l.getTxHash())
   headptr = txptr.getHeaderPtr()
   htime = headptr.getTimestamp()
   print '\tRcvd:', unixTimeToFormatStr(htime)


print '\n\nAdding address to wallet that has non-std tx.  Rescan wallet:'
wallet.addAddress(addrStr4)
wallet.addAddress(addrStr5)
bdm.scanBlockchainForTx_FromScratch(wallet);
print 'Done!'

print 'Wallet addresses: ', wallet.getNumAddr()
for i in range(wallet.getNumAddr()):
   addr = wallet.getAddrByIndex(i)
   print '\t', hash160_to_addrStr(addr.getAddrStr20().toBinStr()),
   print '\tBalance:', coin2str(addr.getBalance())

print 'Getting Ledger for addresses:'
ledger1 = wallet.getTxLedger()
for i,l in enumerate(ledger1):
   print i, 
   print '\tFrom/To:', hash160_to_addrStr(l.getAddrStr20().toBinStr()), 
   print '\tBlock:',   l.getBlockNum(), 
   print '\tAmt:',     coin2str(l.getValue()),
   txptr = bdm.getTxByHash(l.getTxHash())
   headptr = txptr.getHeaderPtr()
   htime = headptr.getTimestamp()
   print '\tRcvd:', unixTimeToFormatStr(htime)

print ''



