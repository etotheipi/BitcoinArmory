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

   # First, get the Satoshi dice page so we can extract the addresses and payouts
   import urllib
   httppage = urllib.urlopen('http://www.satoshidice.com').read().split('\n')

   # Given this line is part of the wager/addr table, get all the data from it
   def extractLineData(line):
      line2 = line.replace('<','~').replace('>','~').replace('=','~').replace(' ','~')
      pcs = line2.split('~')
      out = []
      ltflag = False
      for pc in pcs:
         if pc=='lessthan':
            ltflag = True
         if ltflag and pc.isdigit():
            out.append(pc)
            ltflag = False   
         if pc.startswith('1dice') or pc.endswith('%') or pc.endswith('x'):
            out.append(pc)
      return out


   # We have a webpage and a method to process the relevant lines
   diceTargetMap = {}
   dicePctWinMap  = {}
   diceWinMultMap = {}
   diceLoseMultMap = {}
   diceBetsMadeMap = {}
   diceBetsPaidOut = {}
   WIN, LOSE, REFUND = 0,1,2
   for line in httppage:
      if 'lessthan' in line and '1dice' in line:
         targ,addr,winr,mult,hous,rtrn   = extractLineData(line)
         diceAddr                        = addrStr_to_hash160(addr)
         diceTargetMap[diceAddr]         = int(targ)
         dicePctWinMap[diceAddr]         = float(winr[:-1])/100.0
         diceWinMultMap[diceAddr]        = float(mult[:-1])
         diceLoseMultMap[diceAddr]       =(float(hous[:-1])/100.0)/2.0
         diceBetsMadeMap[diceAddr]       = 0
         diceBetsPaidOut[diceAddr]       = [0, 0, 0]

   
   betsIn  = {}
   sdRecvAmt = 0
   sdRtrnAmt = 0
   sdFeePaid = 0
   totalBets = 0


   def getTxFee(tx):
      btcIn, btcOut = 0,0
      for i in range(tx.getNumTxIn()):
         btcIn += TheBDM.getSentValue(tx.getTxInRef(i))
      for i in range(tx.getNumTxOut()):
         btcOut += tx.getTxOutRef(i).getValue()
      return (btcIn - btcOut)

      
         

   try:
      for h in xrange(175000,topBlock+1):
         if h%10000 == 0:
            print '\tSearched %d blocks' % h
   
         header = TheBDM.getHeaderByHeight(h)
         txList = header.getTxRefPtrList()

         for tx in txList:
            # Check every TxOut in this transaction for SatoshiDice bets
            txHash = tx.getThisHash()
            for nout in range(tx.getNumTxOut()):
               txout = tx.getTxOutRef(nout)
               if txout.isStandard():
                  if dicePctWinMap.has_key(txout.getRecipientAddr()):
                     # This is a SatoshiDice bet!
                     totalBets += 1
                     diceAddr = txout.getRecipientAddr()
                     betAmt = txout.getValue()
                     betWin = betAmt * diceWinMultMap[diceAddr]
                     betLos = betAmt * diceLoseMultMap[diceAddr]

                     firstTxIn = tx.getTxInRef(0)
                     bettorAddr = TheBDM.getSenderAddr20(firstTxIn)
   
                     ## Create the serialized OutPoint, store the tx
                     outpointStr = txHash + int_to_binary(nout, widthBytes=4)
                     betsIn[outpointStr] = [betAmt, betWin, betLos, diceAddr, bettorAddr]
                     sdRecvAmt += betAmt
                     diceBetsMadeMap[diceAddr] += 1


            for nin in range(tx.getNumTxIn()):
               txin = tx.getTxInRef(nin)
               op = txin.getOutPoint()
               opStr = op.getTxHash() + int_to_binary(op.getTxOutIndex(), widthBytes=4)
               returned = -1
               if betsIn.has_key(opStr):
                  betAmt, betWin, betLos, diceAddr, addr160 = betsIn[opStr]
                  for nout in range(tx.getNumTxOut()):
                     if addr160 == tx.getTxOutRef(nout).getRecipientAddr():
                        returned = tx.getTxOutRef(nout).getValue()
                        sdRtrnAmt += returned
                        sdFeePaid += getTxFee(tx)
                        break

                  if returned==-1:
                     print 'Did not find recip, failed...'
                     continue
                  else:
                     if returned <= betLos*1.25:
                        diceBetsPaidOut[diceAddr][LOSE] += 1
                     elif abs(returned - betAmt) < betLos/2.0:
                        diceBetsPaidOut[diceAddr][REFUND] += 1
                     else:
                        diceBetsPaidOut[diceAddr][WIN] += 1
                     del betsIn[opStr]
                     break
                        
   except:
      raise
   

   
   print 'Unaccounted-for Bets:'
   i = 0
   unacctBTC = 0
   for key,val in betsIn.iteritems():
      txid   = binary_to_hex(key[:32 ])
      outidx = binary_to_int(key[ 32:])
      betAmt = val[0]
      sdAddr = val[3]
      recip1 = val[4]

      print i, hex_switchEndian(txid), '%03d'%outidx, coin2str(betAmt), 
      print hash160_to_addrStr(sdAddr)[:8], hash160_to_addrStr(recip1)[:8]
      i += 1
      unacctBTC += betAmt


   print 'Results:', unixTimeToFormatStr(RightNow())
   print ''
   print 'Address'.rjust(10),
   print 'Target'.rjust(8),
   print 'Should Win'.rjust(12), '|',
   print '#Bets'.rjust(8), '|',
   print 'Win'.center(16), '|',
   print 'Lose'.center(16), '|',
   print 'Refunds'.center(17), '|',
   print 'Accounted-for'
   print '-'*118
   
   totalBets = 0
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
      print hash160_to_addrStr(a160)[:9].rjust(10),
      print str(targ).rjust(8),
      print ('%0.5f' % (targ/65536.)).rjust(12),
      print '|', str(total).rjust(8),
   
      print '|', str(winners).rjust(6), ('(%0.5f)'%(winners/float(total2))).rjust(8), 
      print '|', str(losers).rjust(6),  ('(%0.5f)'%(losers/float(total2))).rjust(8), 
      print '|', str(refunds).rjust(6), ('(%0.5f)'%(refunds/float(total2))).rjust(8), 

      print '|', '(%0.3f)'.rjust(10) % ((winners+losers+refunds)/float(total))
      totalBets += total

   print '-'*118
   print ' '*32, '|', str(totalBets).rjust(8), '|'
   print ''
   print '-'*118
   print 'Total Bets Made:              ', totalBets
   print 'Cumulative Wagers:        ', coin2str(sdRecvAmt), 'BTC'
   print 'Cumulative Rewards:       ', coin2str(sdRtrnAmt), 'BTC'
   print 'Cumulative Fees Paid:     ', coin2str(sdFeePaid), 'BTC'
   print 'Cumulative Unreturned:    ', coin2str(unacctBTC), 'BTC'
   print '----'
   print 'SatoshiDice Profit/Loss:  ', coin2str(sdRecvAmt - (sdRtrnAmt + sdFeePaid)), 'BTC'

