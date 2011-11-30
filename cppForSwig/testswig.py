#! /usr/bin/python
################################################################################
#                                                                              #
#  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>               #
#  Distributed under the GNU Affero General Public License (AGPL v3)           #
#  See LICENSE or http://www.gnu.org/licenses/agpl.html                        #
#                                                                              #
################################################################################

from sys import path as PYPATH, argv
PYPATH.append('..')
from btcarmoryengine import *
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

if len(sys.argv) > 1:
   blkfile = sys.argv[1]

print '*'*80
print 'Importing BlockUtils module...',
#from CppBlockUtils import *
import CppBlockUtils as Cpp
print 'Done!'
print ''

print 'Constructing BlockDataManager... ',
bdm = Cpp.BlockDataManager().getBDM()
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
print binary_to_hex(prevhash, BIGENDIAN)
print 'Done!'
print ''


print 'Testing SWIG typemaps!'
pyhashstr = hex_to_binary('a4deb66c0d726b0aefb03ed51be407fbad7331c6e8f9eef231b7000000000000')
head100k = bdm.getHeaderByHash(pyhashstr)
print 'Got header:', head100k.getBlockHeight() 
bdstr = head100k.getPrevHash()
print 'This BinaryData obj should\'ve been converted to pystr', binary_to_hex(bdstr)

print 'Getting almost-top-block'
topm1 = bdm.getHeaderByHash(prevhash)
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
   print 'Tx:', binary_to_hex(txptr.getThisHash(), BIGENDIAN)[:16],
   blkHead = txptr.getHeaderPtr()
   print 'Blk:', blkHead.getBlockHeight(),
   print 'Timestamp:', unixTimeToFormatStr(blkHead.getTimestamp()),
   nIn  = txptr.getNumTxIn()
   nOut = txptr.getNumTxOut()
   print '(in,out) = (%d,%d)' % (nIn, nOut)

   for i in range(nIn):
      txptr.getTxInRef(i).pprint()

   for i in range(nOut):
      txptr.getTxOutRef(i).pprint()



print '*'*80
print '\n\nPrint some random scripts:'
someBlk = bdm.getHeaderByHeight(100014)
print someBlk.pprint()
for tx in someBlk.getTxRefPtrList():
   print 'Tx:', binary_to_hex(tx.getThisHash())
   for i in range(tx.getNumTxIn()):
      print 'TxIn:', i
      txin = tx.getTxInRef(i)
      binScript = txin.getScript()
      if txin.isCoinbase():
         print 'Script: '
         print '   <COINBASE/ARBITRARY>'
         print '  ', binary_to_hex(binScript)
      else:
         pprintScript(binScript)
      print ''
   for i in range(tx.getNumTxOut()):
      print 'TxOut:', i
      binScript = tx.getTxOutRef(i).getScript()
      pprintScript(binScript)
      print ''



   
print '*'*80
print '\n\nScanning Blockchain for transactions...',


addrStr1 = hex_to_binary("abda0c878dd7b4197daa9622d96704a606d2cd14");
addrStr2 = hex_to_binary("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31");
addrStr3 = hex_to_binary("f62242a747ec1cb02afd56aac978faf05b90462e");
addrStr4 = hex_to_binary("baa72d8650baec634cdc439c1b84a982b2e596b2");
addrStr5 = hex_to_binary("6300bf4c5c2a724c280b893807afb976ec78a92b");
addrStr6 = hex_to_binary('0e0aec36fe2545fb31a41164fb6954adcd96b342');

# The _1_ methods are to avoid quirks with SWIG related using overloaded methods
# requiring arguments that were typemap'd (BinaryData, in this case)
cppWallet = Cpp.BtcWallet()
cppWallet.addAddress_1_(addrStr1);
cppWallet.addAddress_1_(addrStr2);
cppWallet.addAddress_1_(addrStr3);
bdm.scanBlockchainForTx_FromScratch(cppWallet);
print 'Done!'

print 'Wallet addresses: ', cppWallet.getNumAddr()
for i in range(cppWallet.getNumAddr()):
   addr = cppWallet.getAddrByIndex(i)
   print '\t', hash160_to_addrStr(addr.getAddrStr20()),
   print '\tBalance:', coin2str(addr.getBalance())

print 'Getting Ledger for addresses:'
ledger1 = cppWallet.getTxLedger()
for i,l in enumerate(ledger1):
   print i, 
   print '\tFrom/To:', hash160_to_addrStr(l.getAddrStr20()), 
   print '\tBlock:',   l.getBlockNum(), 
   print '\tAmt:',     coin2str(l.getValue()),
   txptr = bdm.getTxByHash(l.getTxHash())
   headptr = txptr.getHeaderPtr()
   htime = headptr.getTimestamp()
   print '\tRcvd:', unixTimeToFormatStr(htime)


print '\n\nAdding address to wallet that has non-std tx.  Rescan wallet:'
cppWallet.addAddress_1_(addrStr4)
cppWallet.addAddress_1_(addrStr5)
cppWallet.addAddress_1_(addrStr6)
bdm.scanBlockchainForTx_FromScratch(cppWallet);
print 'Done!'

print 'Wallet addresses: ', cppWallet.getNumAddr()
for i in range(cppWallet.getNumAddr()):
   addr = cppWallet.getAddrByIndex(i)
   print '\t', hash160_to_addrStr(addr.getAddrStr20()),
   print '\tBalance:', coin2str(addr.getBalance())

print 'Getting Ledger for addresses:'
ledger1 = cppWallet.getTxLedger()
for i,l in enumerate(ledger1):
   print i, 
   print '\tFrom/To:', hash160_to_addrStr(l.getAddrStr20()), 
   print '\tBlock:',   l.getBlockNum(), 
   print '\tAmt:',     coin2str(l.getValue()),
   txptr = bdm.getTxByHash(l.getTxHash())
   headptr = txptr.getHeaderPtr()
   htime = headptr.getTimestamp()
   print '\tRcvd:', unixTimeToFormatStr(htime)

print ''



print 'Getting unspent TxOuts for addresses:'
utxolist = bdm.getUnspentTxOutsForWallet(cppWallet)
pprintUnspentTxOutList(utxolist, "All utxos:")

