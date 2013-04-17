################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################

import sys
sys.path.append('..')
sys.path.append('.')
from armoryengine import *
from getpass import getpass


def createTxFromAddrList(walletObj, addrList, recipAmtPairList, \
                                          fee=0, changeAddr=None):
   """ 
   Create an unsigned transaction.  This method expects a wallet file,
   a list of addresses in that wallet, and then a list of recipients and
   amounts to send each one.  

   !!! YOU MUST SPECIFY ALL BITCOIN VALUES IN SATOSHIS !!!
   You can either write it out explicitly -- 150000000
   Or use floats and convert to long      -- long(1.5*ONE_BTC)

   You must also specify an address to which you want change sent.  It will 
   only be used if necessary (i.e. if you don't specify your recip list to 
   exactly match inputs minus fees)
   
   If no change address is specified, the next unused address will be 
   retrieved from the walletObj
   """
   
   if not TheBDM.isInitialized():
      # Only executed on the first call if blockchain not loaded yet.
      print '\nLoading blockchain...'
      BDM_LoadBlockchainFile()  # can add optional arg for blk0001.dat location


   # Check that all addresses are actually in the specified wallet
   for addr in addrList:
      addr160 = addrStr_to_hash160(addr)
      if not walletObj.hasAddr(addr160):
         raise WalletAddressError, 'Address is not in wallet! [%s]' % addr
   

   print '\nUpdating wallet from blockchain'
   walletObj.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
   walletObj.syncWithBlockchain()
   print 'Total Wallet Balance:',coin2str(walletObj.getBalance('Spendable'))
   

   print '\nCollecting Unspent TXOut List...'
   # getAddrTxOutList() returns a C++ vector<UnspentTxOut> object, which must 
   # be converted to a python object using the [:] notation:  it's a weird 
   # consequence of mixing C++ code with python via SWIG...
   utxoList = []
   for addr in addrList:
      addr160 = addrStr_to_hash160(addr)
      unspentTxOuts = walletObj.getAddrTxOutList(addr160, 'Spendable')
      utxoList.extend(unspentTxOuts[:])
   
   # Display what we found
   totalUtxo = sumTxOutList(utxoList)
   totalSpend   = sum([pair[1] for pair in recipList])
   print 'Available:  %d unspent outputs from %d addresses: %s BTC' % \
                  (len(utxoList), len(addrList), coin2str(totalUtxo, ndec=2))

   # Print more detailed information
   pprintUnspentTxOutList(utxoList, 'Available outputs: ')


   #############################################################################
   # IF YOU WANT TO CHANGE THE PRIORITIZATION OF HOW COINS ARE SELECTED:
   #        It's not dynamically customizable, yet.  But you can
   #        go into armoryengine.py and look for the WEIGHTS list
   #        around line 4550.  Change the values to change the 
   #        optimization.   
   #############################################################################

   # PySelectCoins() assumes that the remaining will be sent to a change addr
   print 'Selecting coins based on unspent outputs, recipients, fee...'
   selectedUtxoList = PySelectCoins(utxoList, totalSpend, fee)

   print 'Checking that minimum required fee is satisfied for this tx...'
   minValidFee = calcMinSuggestedFees(selectedUtxoList, totalSpend, fee)[1]

   if minValidFee>fee:
      print '***WARNING:'
      print 'This transaction requires a fee of at least %s BTC' % coin2str(minValidFee)
      print 'Sending of this transaction *will fail*.  Will you increase the fee?'
      confirm = raw_input('Increase Fee [Y/n]:')
      if 'n' in confirm.lower():
         print 'ABORTING'
         return None
      fee = minValidFee
      selectedUtxoList = PySelectCoins(utxoList, totalSpend, fee)

   # Convert address strings to Hash160 values (and make a copy, too)
   recip160List = [(addrStr_to_hash160(pair[0]), pair[1]) for pair in recipList]

   # Add a change output if necessary
   totalSelect = sumTxOutList(selectedUtxoList) 
   totalChange = totalSelect - (totalSpend + fee)
   if totalChange < 0:
      print '***ERROR: you are trying to spend more than your balance!'
      return None
   elif totalChange!=0:
      # Need to add a change output, get from wallet if necessary
      if not changeAddr:
         changeAddr = walletObj.getNextUnusedAddress().getAddrStr()
      recip160List.append( (addrStr_to_hash160(changeAddr), totalChange) )

   print 'Creating Distribution Proposal (just an unsigned transaction)...'
   print [(hash160_to_addrStr(r),coin2str(v)) for r,v in recip160List]

   txdp = PyTxDistProposal().createFromTxOutSelection(selectedUtxoList, recip160List)

   return txdp
   
   
   
################################################################################
if __name__ == '__main__':

   walletFile = 'armory_29KADwa1D_.wallet'
   if not os.path.exists(walletFile):
      raise FileExistsError, 'Wallet file does not exist! [%s]' % walletFile
   wlt = PyBtcWallet().readWalletFile(walletFile)

   # Only use these addresses for this tx
   addrList = ['1dyRSCSJdRiPgGYNTSE31Lodvs3Peiiqx', \
               '131t9NSPV3U1DdyQsEEcEzyyYsWrAcm1ZX']
   
   # Send money to these three outputs (change will be added if/where necessary)
   recipList =[('12V6i8PHhxyYWSEeYsXNr9kzwca1GrW5T8',  long(0.2*ONE_BTC)), \
               ('14CDNme1pFJxLKitdSMqTNETPeLzs1V4RD',  long(0.5*ONE_BTC)), \
               ('16GsZYhzJiv5BHTQaosrwpSpf9Unw3eLuC',  long(1.1*ONE_BTC))   ]
   
   # Works with or without a change address specified
   #sendChangeTo = '151kQbcEdBDehW5gt3fahrHwfBBtEjSSAx'
   sendChangeTo = None
   
   # Remember, must specify amounts in SATOSHIs
   print 'Creating Unsigned Transaction...'
   txdp = createTxFromAddrList(wlt, addrList, recipList, 50000, sendChangeTo)
   txdp.pprint()
   
   print 'Transaction created, now sign it...'
   if wlt.useEncryption and wlt.isLocked:
      passphrase = SecureBinaryData(getpass('Passphrase to unlock wallet: '))
      wlt.unlock(securePassphrase=passphrase)
      passphrase.destroy()


   print 'Signing transaction with wallet...'
   wlt.signTxDistProposal(txdp)
   
   print 'Transaction is fully signed?', 
   print txdp.checkTxHasEnoughSignatures(alsoVerify=True)
   
   print 'Preparing final transaction...'
   pytx = txdp.prepareFinalTx()

   print '\nRaw transaction (pretty):'
   pprintHex(binary_to_hex(pytx.serialize()))
   
   print '\nRaw transaction (raw hex, copy into http://bitsend.rowit.co.uk):'
   print binary_to_hex(pytx.serialize())
   
   print '\nSigned transaction to be broadcast using Armory "offline transactions"...'
   print txdp.serializeAscii()
   
