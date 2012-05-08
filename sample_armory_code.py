from armoryengine import *

# NOTE:
#     ALL ADDRESSES THROUGHOUT EVERYTHING ARE IN 20-BYTE BINARY FORM (hash160/addr20)
#     Use hash160_to_addrStr() and addrStr_to_hash160() to convert...

print '\n\nCreating a new C++ wallet, add a few addresses...'
cppWallet = Cpp.BtcWallet()
cppWallet.addAddress_1_( hex_to_binary('11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31') )  # hash160
cppWallet.addAddress_1_( addrStr_to_hash160('1EbAUHsitefy3rSECh8eK2fdAWTUbpVUDN') )   # addrStr
cppWallet.addAddress_1_('\x1b~\xa7*\x85\t\x12\xb7=\xd4G\xf3\xbd\xc1\x00\xf1\x00\x8b\xde\xb0') # binary


print 'Addresses in this wallet:'
for i in range(cppWallet.getNumAddr()):
   print '\t', hash160_to_addrStr(cppWallet.getAddrByIndex(i).getAddrStr20())


print '\n\nRegistering the wallet with the BlockDataManager & loading...'
start = RightNow()
TheBDM.registerWallet(cppWallet)
BDM_LoadBlockchainFile()  # optional argument to specify blk0001.dat location
print 'Loading blockchain took %0.1f sec' % (RightNow() - start)


topBlock = TheBDM.getTopBlockHeight()
print '\n\nCurrent Top Block is:', topBlock
TheBDM.getTopBlockHeader().pprint()


# Add new addresses -- will rescan (which will be super fast if you ahve a lot of RAM)
cppWallet.addAddress_1_( hex_to_binary('0cdcd0f388a31b11ff11b1d8d7a9f978b37bc7af') ) 
TheBDM.scanBlockchainForTx(cppWallet)



print '\n\nBalance of this wallet:', coin2str(cppWallet.getSpendableBalance())
print 'Unspent outputs:'
unspentTxOuts = cppWallet.getSpendableTxOutList(topBlock)
for utxo in unspentTxOuts:
   utxo.pprintOneLine()

print '\n\nTransaction history of this wallet:'
ledger = cppWallet.getTxLedger()
for le in ledger:
   le.pprintOneLine()



print '\n\n'
print '-'*80
print 'Now for something completely different...'
start = RightNow()
print '\n\nCollect all difficulty changes...'
print 'Block'.rjust(10), 'Difficulty'.rjust(14), '\t', 'Date'
prevDiff = 0
maxDiff = hex_to_int('ff'*32)
minDiff = maxDiff
minDiffBlk = hex_to_int('ff'*32)
for h in xrange(0,topBlock+1):
   header = TheBDM.getHeaderByHeight(h)
   currDiff = header.getDifficulty()
   thisHash = header.getThisHash()
   thisDiff = binary_to_int(thisHash);

   if thisDiff < minDiff:
      minDiff = thisDiff
      minDiffBlk = h
   
   if not prevDiff==currDiff:
      print str(h).rjust(10),
      print ('%0.1f'%currDiff).rjust(14),
      print '\t', unixTimeToFormatStr(header.getTimestamp())
   prevDiff = currDiff

from math import log
print 'Took %0.1f seconds to collect difficulty list' % (RightNow()-start)
print '\nBlock with the lowest difficulty:'
print '   Block Num:      ', minDiffBlk
print '   Block Hash:     ', int_to_hex(minDiff, 32, BIGENDIAN)
print '   Equiv Difficult:', maxDiff/(minDiff * 2**32)
print '   Equiv Diff bits:', log(maxDiff/minDiff)/log(2)
      
      

print '\n\nCount the number of unique addresses in the blockchain'
start = RightNow()
allAddr = set()
totalTxOutEver = 0
for h in xrange(0,topBlock+1):
   if h%10000 == 0:
      print '\tScanned %d blocks' % h
      
   header = TheBDM.getHeaderByHeight(h)
   txList = header.getTxRefPtrList()
   for tx in txList:
      for nout in range(tx.getNumTxOut()):
         txout = tx.getTxOutRef(nout)
         if txout.isStandard():
            allAddr.add(txout.getRecipientAddr())
            totalTxOutEver += 1
            

print 'Took %0.1f seconds to count all addresses' % (RightNow()-start)
print 'There are %d unique addresses in the blockchain!' % len(allAddr)
print 'There are %d standard TxOuts in all blocks' % totalTxOutEver











