from armoryengine import *

run_WalletCreate    = False
run_LoadBlockchain  = True
run_WalletRescan    = False
run_DiffChangeList  = False
run_UniqueAddresses = False
run_SatoshiDice     = True


################################################################################
if run_WalletCreate:
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
   TheBDM.registerWallet(cppWallet)


################################################################################
if run_LoadBlockchain:
   start = RightNow()
   BDM_LoadBlockchainFile()  # optional argument to specify blk0001.dat location
   print 'Loading blockchain took %0.1f sec' % (RightNow() - start)


   topBlock = TheBDM.getTopBlockHeight()
   print '\n\nCurrent Top Block is:', topBlock
   TheBDM.getTopBlockHeader().pprint()


################################################################################
if run_WalletRescan:
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



################################################################################
if run_DiffChangeList:
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



################################################################################
if run_UniqueAddresses:
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


################################################################################
if run_SatoshiDice:
   print '\n\nLet look at all the bets ever placed at SatoshiDice.com'
   diceOddsTable = [line.split() for line in open('dicelist.txt').readlines()]
   diceTargetMap = {}
   dicePctWinMap  = {}
   diceWinMultMap = {}
   diceBetsMadeMap = {}
   diceBetsPaidOut = {}
   WIN, LOSE, REFUND = 0,1,2
   for row in diceOddsTable:
      diceAddr = addrStr_to_hash160(row[1])
      diceTargetMap[diceAddr]         = int(row[0])
      dicePctWinMap[diceAddr]         = float(row[2][:-1])
      diceWinMultMap[diceAddr]        = float(row[3][:-1])
      diceLoseMultiplier              = 536./(2*65536.)
      diceBetsMadeMap[diceAddr]       = 0
      diceBetsPaidOut[diceAddr]       = [0, 0, 0]
   
   betsIn  = {}
   totalBets = 0
   
   try:
      for h in xrange(170000,topBlock+1):
         if h%10000 == 0:
            print '\tSearched %d blocks' % h
   
         header = TheBDM.getHeaderByHeight(h)
         txList = header.getTxRefPtrList()
         for tx in txList:
   
            # Check every TxOut in this transaction for SatoshiDice bets
            for nout in range(tx.getNumTxOut()):
               txout = tx.getTxOutRef(nout)
               if txout.isStandard():
                  if dicePctWinMap.has_key(txout.getRecipientAddr()):
                     # This is a SatoshiDice bet!
                     totalBets += 1
                     diceAddr = txout.getRecipientAddr()
                     betAmt = txout.getValue()
                     betWin = betAmt * diceWinMultMap[diceAddr]
                     betLos = betAmt * diceLoseMultiplier
   
                     # The payout always goes to first input
                     firstTxIn = tx.getTxInRef(0)
                     bettorAddr = TheBDM.getSenderAddr20(firstTxIn)
   
                     # For sure, a bet was made to this address
                     diceBetsMadeMap[diceAddr] += 1
   
                     # Lookup table for the bettor's addresses to find payout later
                     if not betsIn.has_key(bettorAddr):
                        betsIn[bettorAddr] = []
   
                     betsIn[bettorAddr].append([betWin, betLos, betAmt, diceAddr])
   
   
                  if betsIn.has_key(txout.getRecipientAddr()):
                     bettorAddr = txout.getRecipientAddr()
                     for i in range(len(betsIn[bettorAddr])):
                        diceAddr = betsIn[bettorAddr][i][3]
                        recvAmt = txout.getValue()
                        loseAmt = betsIn[bettorAddr][i][LOSE]
                        if abs(betsIn[bettorAddr][i][WIN]-recvAmt) < 2*loseAmt :
                           diceBetsPaidOut[diceAddr][WIN] += 1
                           del betsIn[bettorAddr][i]
                           break;
                        elif abs(betsIn[bettorAddr][i][LOSE]-recvAmt) < 2*loseAmt:
                           diceBetsPaidOut[diceAddr][LOSE] += 1
                           del betsIn[bettorAddr][i]
                           break;
                        elif abs(betsIn[bettorAddr][i][REFUND]-recvAmt) < 2*loseAmt:
                           diceBetsPaidOut[diceAddr][REFUND] += 1
                           del betsIn[bettorAddr][i]
                           break;
   except:
      pass
   
   
   print 'Results:'
   print '   ',
   print 'Address'.rjust(12),
   print 'Target'.rjust(12),
   print 'Theory'.rjust(12),
   print 'Total Bets'.rjust(12),
   print 'Win'.center(16),
   print 'Lose'.center(16),
   print 'Refunds'.center(16),
   print 'Accounted-for'
   
   diceAddrList = []
   for a160,ct in diceBetsMadeMap.iteritems():
      diceAddrList.append([a160, diceTargetMap[a160]])
   
   diceAddrList.sort(key=(lambda x: x[1]))
   
   for a160,targ in diceAddrList:
      total   = diceBetsMadeMap[a160]
      winners = diceBetsPaidOut[a160][WIN]
      losers  = diceBetsPaidOut[a160][LOSE]
      refunds = diceBetsPaidOut[a160][REFUND]
      total2  = winners+losers
      print '   ',
      print hash160_to_addrStr(a160)[:8].rjust(12),
      print str(targ).rjust(12),
      print ('%0.3f' % (targ/65536.)).rjust(12),
      print str(total).rjust(12),
   
      print str(winners).rjust(7), ('%0.3f'%(winners/float(total2))).rjust(7),
      print str(losers).rjust(7),  ('%0.3f'%(losers/float(total2))).rjust(7),
      print str(refunds).rjust(7), ('%0.3f'%(refunds/float(total2))).rjust(7),

      print '\t(%0.3f)' % ((winners+losers+refunds)/float(total))


