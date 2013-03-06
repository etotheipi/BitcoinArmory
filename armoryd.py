################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
# Original copyright transferred from from Ian Coleman (2012)
# Special thanks to Ian Coleman who created the original incarnation of
# this file and then transferred the rights to me so I could integrate it
# into the Armory project.  And even more thanks to him for his advice
# on upgrading its security features and other capabilities.
#
################################################################################


      #####
   #####
#####
#
# As OF 10 Jan, 2013, this code does not work reliably.  Please do not use this
# until this message disappears from a future release.
# (To be fair, getting new addresses and balances APPEAR to work, but
#  listtransactions
#
#####
   #####
      #####


#####
# ORIGINAL comments from Ian Coleman:
#
# This is a json-rpc interface to armory - http://bitcoinarmory.com/
#
# Where possible this follows conventions established by the Satoshi client.
# Does not require armory to be installed or running, this is a standalone application.
# Requires bitcoind process to be running before starting armory-daemon.
# Requires an armory watch-only wallet to be in the same folder as the
# armory-daemon script.
# Works with testnet, use --testnet flag when starting the script.
#
# BEWARE:
# This is relatively untested, please use caution. There should be no chance for
# irreversible damage to be done by this software, but it is still in the early
# development stage so treat it with the appropriate level of skepticism.
#
# Many thanks must go to etotheipi who started the armory client, and who has
# provided immense amounts of help with this. This app is mostly chunks
# of code taken from armory and refurbished into an rpc client.
# See the bitcontalk thread for more details about this software:
# https://bitcointalk.org/index.php?topic=92496.0
#####

from twisted.internet import reactor
from twisted.web import server
from txjsonrpc.web import jsonrpc
from txjsonrpc.auth import wrapResource
from twisted.cred.checkers import FilePasswordDB

from armoryengine import *

import datetime
import decimal
import os
import sys
import time
import socket

# Some non-twisted json imports from jgarzik's code and his UniversalEncoder
import json
from   jsonrpc import ServiceProxy
class UniversalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

ARMORYD_CONF_FILE = os.path.join(ARMORY_HOME_DIR, 'armoryd.conf')



# From https://en.bitcoin.it/wiki/Proper_Money_Handling_(JSON-RPC)
def JSONtoAmount(value):
    return long(round(float(value) * 1e8))
def AmountToJSON(amount):
    return float(amount / 1e8)


# Define some specific errors that can be thrown and caught
class UnrecognizedCommand(Exception): pass


################################################################################

################################################################################
################################################################################


class Armory_Json_Rpc_Server(jsonrpc.JSONRPC):

   #############################################################################
   def __init__(self, wallet):
      self.wallet = wallet

   #############################################################################
   def jsonrpc_getnewaddress(self):
      addr = self.wallet.getNextUnusedAddress()
      return addr.getAddrStr()

   #############################################################################
   def jsonrpc_getwalletinfo(self):
      wltInfo = { \
                  'name':  self.wallet.labelName,
                  'description':  self.wallet.labelDescr,
                  'balance':  AmountToJSON(self.wallet.getBalance('Spend')),
                  'keypoolsize':  self.wallet.addrPoolSize,
                  'numaddrgen': len(self.wallet.addrMap),
                  'highestusedindex': self.wallet.highestUsedChainIndex
               }
      return wltInfo


   #############################################################################
   def jsonrpc_getbalance(self, baltype='spendable'):
      if not baltype in ['spendable','spend', 'unconf', 'unconfirmed', \
                          'total', 'ultimate','unspent', 'full']:
         LOGERROR('Unrecognized getbalance string: "%s"', baltype)
         return -1
         
      return AmountToJSON(self.wallet.getBalance(baltype))

   #############################################################################
   def jsonrpc_getreceivedbyaddress(self, address):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot get received amount when offline')
      # Only gets correct amount for addresses in the wallet, otherwise 0
      addr160 = addrStr_to_hash160(address)
      txs = self.wallet.getAddrTxLedger(addr160)
      balance = sum([x.getValue() for x in txs if x.getValue() > 0])
      return AmountToJSON(balance)

   #############################################################################
   def jsonrpc_sendtoaddress(self, bitcoinaddress, amount):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot create transactions when offline')
      addr160 = addrStr_to_hash160(bitcoinaddress)
      amtCoin = JSONtoAmount(amount)
      return self.create_unsigned_transaction([[addr160, amtCoin]])

   #############################################################################
   def jsonrpc_sendmany(self, *args):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot create transactions when offline')

      recipvalpairs = []
      for a in args:
         r,v = a.split(':')
         recipvalpairs.append([addrStr_to_hash160(r), JSONtoAmount(v)])

      return self.create_unsigned_transaction(recipvalpairs)


   #############################################################################
   def jsonrpc_getledgersimple(self, tx_count=10, from_tx=0):
      return self.jsonrpc_getledger(tx_count, from_tx, simple=True)

   #############################################################################
   def jsonrpc_getledger(self, tx_count=10, from_tx=0, simple=False):
      final_le_list = []
      ledgerEntries = self.wallet.getTxLedger('blk')
         
      sz = len(ledgerEntries)
      lower = min(sz, from_tx)
      upper = min(sz, from_tx+tx_count)

      txSet = set([])

      for i in range(lower,upper):
         le = ledgerEntries[i]
         txHashBin = le.getTxHash()
         txHashHex = binary_to_hex(txHashBin, BIGENDIAN)

         cppTx = TheBDM.getTxByHash(txHashBin)
         if not cppTx.isInitialized():
            LOGERROR('Tx hash not recognized by TheBDM: %s' % txHashHex)

         cppHead = cppTx.getHeaderPtr()
         if not cppHead.isInitialized:
            LOGERROR('Header pointer is not available!')
            headHashBin = ''
            headHashHex = ''
            headtime    = 0
         else:
            headHashBin = cppHead.getThisHash()
            headHashHex = binary_to_hex(headHashBin, BIGENDIAN)
            headtime    = cppHead.getTimestamp()

         isToSelf = le.isSentToSelf()
         netCoins = le.getValue()
         feeCoins = getFeeForTx(txHashBin)
      
         allRecips = [cppTx.getTxOut(i).getRecipientAddr() for i in range(cppTx.getNumTxOut())]
         first160 = ''
         if cppTx.getNumTxOut()==1:
            first160 = allRecips[0]
            change160 = ''
         elif isToSelf:
            # Sent-to-Self tx
            amtCoins,changeIdx = determineSentToSelfAmt(le, self.wallet)
            change160 = allRecips[changeIdx]
            for iout,recip160 in enumerate(allRecips):
               if not iout==changeIdx:
                  first160 = recip160
                  break
         elif netCoins<0:
            # Outgoing transaction (process in reverse order so get first)
            amtCoins = -1*(netCoins+feeCoins)
            for recip160 in allRecips[::-1]:
               if self.wallet.hasAddr(recip160):
                  change160 = recip160
               else:
                  first160 = recip160
         else:
            # Incoming transaction
            amtCoins = netCoins
            for recip160 in allRecips[::-1]:
               if self.wallet.hasAddr(recip160):
                  first160 = recip160
               else:
                  change160 = recip160


         # amtCoins: amt of BTC transacted, always positive (how big are outputs minus change?)
         # netCoins: net effect on wallet (positive or negative)
         # feeCoins: how much fee was paid for this tx 

         if netCoins < -feeCoins:
            txDir = 'send'
         elif netCoins > -feeCoins:
            txDir = 'receive'
         else:
            txDir = 'toself'

         # Convert to address strings
         firstAddr = hash160_to_addrStr(first160)
         changeAddr = '' if len(change160)==0 else hash160_to_addrStr(change160)

         nconf = TheBDM.getTopBlockHeader().getBlockHeight() - le.getBlockNum() + 1


         myinputs,  otherinputs = [],[]
         for iin in range(cppTx.getNumTxIn()):
            sender = TheBDM.getSenderAddr20(cppTx.getTxIn(iin))
            val    = TheBDM.getSentValue(cppTx.getTxIn(iin))
            addTo  = (myinputs if self.wallet.hasAddr(sender) else otherinputs)
            addTo.append( {'address': hash160_to_addrStr(sender), \
                           'amount':  AmountToJSON(val)} )
            

         myoutputs, otheroutputs = [], []
         for iout in range(cppTx.getNumTxOut()):
            recip = cppTx.getTxOut(iout).getRecipientAddr();
            val   = cppTx.getTxOut(iout).getValue();
            addTo = (myoutputs if self.wallet.hasAddr(recip) else otheroutputs)
            addTo.append( {'address': hash160_to_addrStr(recip), \
                           'amount':  AmountToJSON(val)} )

         
         tx_info = {
                     'direction' :    txDir,
                     'wallet' :       self.wallet.uniqueIDB58,
                     'amount' :       AmountToJSON(amtCoins),
                     'netdiff' :      AmountToJSON(netCoins),
                     'fee' :          AmountToJSON(feeCoins),
                     'txid' :         txHashHex,
                     'blockhash' :    headHashHex,
                     'confirmations': nconf,
                     'txtime' :       le.getTxTime(),
                     'txsize' :       len(cppTx.serialize()),
                     'blocktime' :    headtime,
                     'comment' :      self.wallet.getComment(txHashBin),
                     'firstrecip':    firstAddr,
                     'changerecip':   changeAddr
                  }

         if not simple:
            tx_info['senderme']     = myinputs
            tx_info['senderother']  = otherinputs
            tx_info['recipme']      = myoutputs
            tx_info['recipother']   = otheroutputs
         
         final_le_list.append(tx_info)

      return final_le_list
      




   #############################################################################
   def jsonrpc_listtransactions(self, tx_count=10, from_tx=0):
      # This does not use 'account's like in the Satoshi client

      final_tx_list = []
      ledgerEntries = self.wallet.getTxLedger('blk')
         
      sz = len(ledgerEntries)
      lower = min(sz, from_tx)
      upper = min(sz, from_tx+tx_count)

      txSet = set([])

      for i in range(sz):

         le = ledgerEntries[i]
         txHashBin = le.getTxHash()
         if txHashBin in txSet:
            continue

         txSet.add(txHashBin)
         txHashHex = binary_to_hex(txHashBin, BIGENDIAN)

         cppTx = TheBDM.getTxByHash(txHashBin)
         if not cppTx.isInitialized():
            LOGERROR('Tx hash not recognized by TheBDM: %s' % txHashHex)

         cppHead = cppTx.getHeaderPtr()
         if not cppHead.isInitialized:
            LOGERROR('Header pointer is not available!')

         blockIndex = cppTx.getBlockTxIndex()
         blockHash  = binary_to_hex(cppHead.getThisHash(), BIGENDIAN)
         blockTime  = le.getTxTime()
         isToSelf   = le.isSentToSelf()
         feeCoin   = getFeeForTx(txHashBin)
         totalBalDiff = le.getValue()
         nconf = TheBDM.getTopBlockHeader().getBlockHeight() - le.getBlockNum() + 1


         # We have potentially change outputs on any outgoing transactions.
         # If sent-to-self, assume 1 change address (max chain idx), all others
         # are receives
         recipVals = []
         for iout in range(cppTx.getNumTxOut()):
            recip = cppTx.getTxOut(iout).getRecipientAddr()
            val   = cppTx.getTxOut(iout).getValue()
            recipVals.append([recip,val])
            


         if cppTx.getNumTxOut()==1:
            changeAddr160 = ""
            targAddr160 = cppTx.getTxOut(0).getRecipientAddr()
         elif isToSelf:
            selfamt,changeIdx = determineSentToSelfAmt(le, self.wallet)
            if changeIdx==-1:
               changeAddr160 = ""
            else:
               changeAddr160 = recipVals[changeIdx]
               del recipVals[changeIdx]
            targAddr160 = recipVals[0][0]
         elif totalBalDiff < 0:
            # This was ultimately an outgoing transaction
            for iout,rv in enumerate(recipVals):
               if self.wallet.hasAddr(rv[0]):
                  changeAddr160 = rv[0]
                  del recipVals[iout]
                  break
            targAddr160 = recipVals[0][0]
         else:
            # Receiving transaction
            for recip,val in recipVals:
               if self.wallet.hasAddr(recip):
                  targAddr160 = recip
                  break
            targAddr160 = recipVals[0][0]
            changeAddr160 = ''
            

         # We always add one entry for the total balance diff on outgoing tx
         if totalBalDiff<-feeCoin:
            category = 'send'
            amt =  AmountToJSON(le.getValue()+feeCoin)
            fee = -AmountToJSON(feeCoin)
            tx_info = {
                        "account" :        "",
                        "address" :        hash160_to_addrStr(targAddr160),
                        "category" :       category,
                        "amount" :         amt,
                        "fee" :            fee,
                        "confirmations" :  nconf,
                        "blockhash" :      blockHash,
                        "blockindex" :     blockIndex,
                        "blocktime" :      blockTime,
                        "txid" :           txHashHex,
                        "time" :           blockTime,
                        "timereceived" :   blockTime 
                     }
            final_tx_list.append(tx_info)




         for a160,val in recipVals:
            # Change outputs have already been removed
            if totalBalDiff>0 and not self.wallet.hasAddr(a160):
               # This is a receiving tx and this is other addr sending to other addr
               continue

            if a160=='\x00'*20:
               address = '<Non-Standard Script>'
            else:
               address = hash160_to_addrStr(a160)
            
            if not self.wallet.hasAddr(a160):
               category = 'send'
               amt = -AmountToJSON(val)
               fee = -AmountToJSON(feeCoin)
               tx_info = {
                           "account" :        "",
                           "address" :        address,
                           "category" :       category,
                           "amount" :         amt,
                           "fee" :            fee,
                           "confirmations" :  nconf,
                           "blockhash" :      blockHash,
                           "blockindex" :     blockIndex,
                           "blocktime" :      blockTime,
                           "txid" :           txHashHex,
                           "time" :           blockTime,
                           "timereceived" :   blockTime 
                        }
            else:
               category = 'receive'
               amt = AmountToJSON(val)
               tx_info = {
                           "account" : "",
                           "address" : address,
                           "category" : category,
                           "amount" : amt,
                           "confirmations" : nconf,
                           "blockhash" : blockHash,
                           "blockindex" : blockIndex,
                           "blocktime" : blockTime,
                           "txid" : txHashHex,
                           "time" : blockTime,
                           "timereceived" : blockTime
                        }

            final_tx_list.append(tx_info)

      return final_tx_list




   
   #############################################################################
   def jsonrpc_getinfo(self):
      isReady = TheBDM.getBDMState() == 'BlockchainReady'
      info = { \
               'version':           getVersionInt(BTCARMORY_VERSION),
               'protocolversion':   0,  
               'walletversion':     getVersionInt(PYBTCWALLET_VERSION),
               'bdmstate':          TheBDM.getBDMState(),
               'balance':           AmountToJSON(self.wallet.getBalance()) if isReady else -1,
               'blocks':            TheBDM.getTopBlockHeight(),
               'connections':       (0 if isReady else 1),
               'proxy':             '',
               'difficulty':        TheBDM.getTopBlockHeader().getDifficulty() if isReady else -1,
               'testnet':           USE_TESTNET,
               'keypoolsize':       self.wallet.addrPoolSize
            }
      return info


   #############################################################################
   def jsonrpc_getblock(self, blkhash):
      if TheBDM.getBDMState() in ['Uninitialized', 'Offline']:
         return {'error': 'armoryd is offline'}

      head = TheBDM.getHeaderByHash(hex_to_binary(blkhash, BIGENDIAN))

      if not head:
         return {'error': 'header not found'}
      
      out = {}
      out['hash'] = blkhash
      out['confirmations'] = TheBDM.getTopBlockHeight()-head.getBlockHeight()+1
      out['size'] = head.getBlockSize()
      out['height'] = head.getBlockHeight()
      out['time'] = head.getTimestamp()
      out['nonce'] = head.getNonce()
      out['difficulty'] = head.getDifficulty()
      out['difficultysum'] = head.getDifficultySum()
      out['mainbranch'] = head.isMainBranch()
      out['bits'] = binary_to_hex(head.getDiffBits())
      out['merkleroot'] = binary_to_hex(head.getMerkleRoot(), BIGENDIAN)
      out['version'] = head.getVersion()
      out['rawheader'] = binary_to_hex(head.serialize())
      
      txlist = head.getTxRefPtrList() 
      ntx = len(txlist)
      out['tx'] = ['']*ntx
      for i in range(ntx):
         out['tx'][i] = binary_to_hex(txlist[i].getThisHash(), BIGENDIAN)
   
      return out
      

   #############################################################################
   def jsonrpc_gettransaction(self, txHash):
      if TheBDM.getBDMState() in ['Uninitialized', 'Offline']:
         return {'error': 'armoryd is offline'}

      binhash = hex_to_binary(txHash, BIGENDIAN)
      tx = TheBDM.getTxByHash(binhash)
      if not tx.isInitialized():
         return {'error': 'transaction not found'}
      
      out = {}
      out['txid'] = txHash
      out['mainbranch'] = tx.isMainBranch()
      out['numtxin'] = tx.getNumTxIn()
      out['numtxout'] = tx.getNumTxOut()

      haveAllInputs = True
      txindata = []
      inputvalues = []
      outputvalues = []
      for i in range(tx.getNumTxIn()): 
         op = tx.getTxIn(i).getOutPoint()
         prevtx = TheBDM.getTxByHash(op.getTxHash())
         if not prevtx.isInitialized():
            haveAllInputs = False
            txindata.append( { 'address': '00'*32, 
                               'value':   '-1',
                               'ismine':   False,
                               'fromtxid': binary_to_hex(op.getTxHash(), BIGENDIAN),
                               'fromtxindex': op.getTxOutIndex()})
                               
         else:
            txout = prevtx.getTxOut(op.getTxOutIndex())
            inputvalues.append(txout.getValue())
            recip160 = txout.getRecipientAddr()
            txindata.append( { 'address': hash160_to_addrStr(recip160),
                               'value':   AmountToJSON(txout.getValue()),
                               'ismine':   self.wallet.hasAddr(recip160),
                               'fromtxid': binary_to_hex(op.getTxHash(), BIGENDIAN),
                               'fromtxindex': op.getTxOutIndex()})

      txoutdata = []
      for i in range(tx.getNumTxOut()): 
         txout = tx.getTxOut(i)
         txoutdata.append( { 'value': AmountToJSON(txout.getValue()),
                             'ismine':   self.wallet.hasAddr(txout.getRecipientAddr()),
                             'address': hash160_to_addrStr(txout.getRecipientAddr())})
         outputvalues.append(txout.getValue())

      fee = sum(inputvalues)-sum(outputvalues)
      out['fee'] = AmountToJSON(fee)

      out['infomissing'] = not haveAllInputs
      out['inputs'] = txindata
      out['outputs'] = txoutdata

      if not tx.isMainBranch():
         return out

      # The tx is in a block, fill in the rest of the data
      out['confirmations'] = TheBDM.getTopBlockHeight() - tx.getBlockHeight() + 1
      out['time'] = tx.getBlockTimestamp()
      out['orderinblock'] = tx.getBlockTxIndex()

      le = self.wallet.cppWallet.calcLedgerEntryForTx(tx)
      amt = le.getValue()
      out['netdiff']     = AmountToJSON(amt)
      out['totalinputs'] = AmountToJSON(sum(inputvalues))
   
      if le.getTxHash()=='\x00'*32:
         out['category']  = 'unrelated'
         out['direction'] = 'unrelated'
      elif le.isSentToSelf():
         out['category']  = 'toself'
         out['direction'] = 'toself'
      elif amt<-fee:
         out['category']  = 'send'
         out['direction'] = 'send'
      else:
         out['category']  = 'receive'
         out['direction'] = 'receive'
         

   
      return out

   #############################################################################
   # https://bitcointalk.org/index.php?topic=92496.msg1126310#msg1126310
   def create_unsigned_transaction(self, recipValPairs):
      # Get unspent TxOutList and select the coins
      #addr160_recipient = addrStr_to_hash160(bitcoinaddress_str)

      totalSend = long( sum([rv[1] for rv in recipValPairs]) )
      fee = 0

      spendBal = self.wallet.getBalance('Spendable')
      utxoList = self.wallet.getTxOutList('Spendable')
      utxoSelect = PySelectCoins(utxoList, totalSend, fee)

      minFeeRec = calcMinSuggestedFees(utxoSelect, totalSend, fee)[1]
      if fee<minFeeRec:
         if totalSend + minFeeRec > spendBal:
            raise NotEnoughCoinsError, "You can't afford the fee!"
         utxoSelect = PySelectCoins(utxoList, totalSend, minFeeRec)
         fee = minFeeRec

      if len(utxoSelect)==0:
         raise CoinSelectError, "Somehow, coin selection failed.  This shouldn't happen"

      totalSelected = sum([u.getValue() for u in utxoSelect])
      totalChange = totalSelected - (totalSend  + fee)

      outputPairs = recipValPairs
      if totalChange > 0:
         outputPairs.append( [self.wallet.getNextUnusedAddress().getAddr160(), totalChange] )

      random.shuffle(outputPairs)
      txdp = PyTxDistProposal().createFromTxOutSelection(utxoSelect, outputPairs)

      return txdp.serializeAscii()


################################################################################
################################################################################
class Armory_Daemon(object):


   #############################################################################
   def __init__(self):

      # Check if armoryd is already running, bail if it is
      self.checkForAlreadyRunning()

      print ''
      print '*'*80
      print '* '
      print '* WARNING!  WALLET FILE ACCESS IS NOT THREAD-SAFE!'
      print '*           DO NOT run armoryd at the same time as ArmoryQt if '
      print '*           they are managing the same wallet file.  If you want '
      print '*           to manage the same wallet with both applications '
      print '*           you must make a digital copy/backup of the wallet file '
      print '*           into another directory and point armoryd at that one.  '
      print '*           '
      print '*           As long as the two processes do not share the same '
      print '*           actual file, there is no risk of wallet corruption. '
      print '*           Just be aware that addresses may end up being reused '
      print '*           if you execute transactions at approximately the same '
      print '*           time with both apps. '
      print '* '
      print '*'*80
      print ''

      # ...otherwise, setup the server
      self.newTxFunctions = []
      self.newBlockFunctions = []
      self.heartbeatFunctions = []

      # The only argument that armoryd.py takes is the wallet to serve
      if len(CLI_ARGS)==0:
         LOGERROR('Please supply the wallet for this server to serve')
         LOGERROR('USAGE:  %s [--testnet] [--whatever] file.wallet' % sys.argv[0])
         os._exit(1)
      wltpath = CLI_ARGS[0]
      if not os.path.exists(wltpath):
         LOGERROR('Wallet does not exist!  (%s)', wltpath)
         return

      self.wallet = PyBtcWallet().readWalletFile(wltpath)

      LOGINFO("Initialising RPC server on port %d", RPC_PORT)
      resource = Armory_Json_Rpc_Server(self.wallet)
      secured_resource = self.set_auth(resource)

      # This is LISTEN call for armory RPC server
      reactor.listenTCP(RPC_PORT, \
                        server.Site(secured_resource), \
                        interface="127.0.0.1")


      # Setup the heartbeat function to run every 
      reactor.callLater(3, self.Heartbeat)


   #############################################################################
   def set_auth(self, resource):
      passwordfile = ARMORYD_CONF_FILE
      checker = FilePasswordDB(passwordfile)
      realmName = "Armory JSON-RPC App"
      wrapper = wrapResource(resource, [checker], realmName=realmName)
      return wrapper

   #############################################################################
   def start(self):
      LOGINFO('Server started...')
      if(not TheBDM.getBDMState()=='Offline'):
         TheBDM.registerWallet(self.wallet)
         TheBDM.setBlocking(False)
         TheBDM.setOnlineMode(True)

         LOGINFO('Blockchain loading')
         while not TheBDM.getBDMState()=='BlockchainReady':
            time.sleep(2)

         self.latestBlockNum = TheBDM.getTopBlockHeight()
         LOGINFO('Blockchain loading finished.  Top block is %d', TheBDM.getTopBlockHeight())

         mempoolfile = os.path.join(ARMORY_HOME_DIR,'mempool.bin')
         self.checkMemoryPoolCorruption(mempoolfile)
         TheBDM.enableZeroConf(mempoolfile)
         LOGINFO('Syncing wallet: %s' % self.wallet.uniqueIDB58)
         self.wallet.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
         self.wallet.syncWithBlockchain()
         LOGINFO('Blockchain load and wallet sync finished')
         LOGINFO('Wallet balance: %s' % coin2str(self.wallet.getBalance('Spendable')))

         # This is CONNECT call for armoryd to talk to bitcoind
         LOGINFO('Set up connection to bitcoind')
         self.NetworkingFactory = ArmoryClientFactory( \
                        func_loseConnect = self.showOfflineMsg, \
                        func_madeConnect = self.showOnlineMsg, \
                        func_newTx       = self.execOnNewTx, \
                        func_newBlock    = self.execOnNewBlock)
         reactor.connectTCP('127.0.0.1', BITCOIN_PORT, self.NetworkingFactory)

      reactor.run()


   #############################################################################
   def checkForAlreadyRunning(self):
      try:
         # If create doesn't throw an error, there's another Armory open already!
         sock = socket.create_connection(('127.0.0.1',RPC_PORT), 0.1);
   
         # If this is the first instance of armoryd.py, connection will fail,
         # we hit the except clause, and continue happily starting the server.
         # If armoryd is already running, the rest of this try-clause will exec.
         LOGINFO('Another instance of armoryd.py is already runnning!')
         with open(ARMORYD_CONF_FILE, 'r') as f:
            usr,pwd = f.readline().strip().split(':')
         
         if CLI_ARGS:
            proxyobj = ServiceProxy("http://%s:%s@127.0.0.1:%d" % (usr,pwd,RPC_PORT))
            extraArgs = [] if len(CLI_ARGS)==1 else CLI_ARGS[1:]
            try:
               #if not proxyobj.__hasattr__(CLI_ARGS[0]):
                  #raise UnrecognizedCommand, 'No json command %s'%CLI_ARGS[0]

               result = proxyobj.__getattr__(CLI_ARGS[0])(*extraArgs)
               print json.dumps(result,
                                indent=4, \
                                sort_keys=True, \
                                cls=UniversalEncoder)
            except Exception as e:
               errtype = str(type(e))
               errtype = errtype.replace("<class '",'')
               errtype = errtype.replace("<type '",'')
               errtype = errtype.replace("'>",'')
               errordict = { 'error': {
                                       'errortype': errtype,
                                       'jsoncommand': CLI_ARGS[0],
                                       'jsoncommandargs': ([] if len(CLI_ARGS)==1 else CLI_ARGS[1:]),
                                       'extrainfo': str(e) if len(e.args)<2 else e.args}}
                              
               print json.dumps( errordict, indent=4, sort_keys=True, cls=UniversalEncoder)
               
                
         sock.close()
         os._exit(0)
      except socket.error:
         LOGINFO('No other armoryd.py instance is running.  We\'re the first.')
         pass

   #############################################################################
   def execOnNewTx(self, pytxObj):
      # Gotta do this on every new Tx
      TheBDM.addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True)
      TheBDM.rescanWalletZeroConf(self.wallet.cppWallet)

      # Add anything else you'd like to do on a new block
      # 
      for txFunc in self.newTxFunctions:
         txFunc(pytxObj)


   #############################################################################
   def execOnNewBlock(self, pyHeader, pyTxList):
      # DO NOT PUT ANY FUNCTION HERE THAT EXPECT TheBDM TO BE UP TO DATE
      # WITH THE NEW BLOCK!  ONLY CALL FUNCTIONS THAT OPERATE PURELY ON
      # THE NEW HEADER AND TXLIST WITHOUT TheBDM.

      # Any functions that you want to execute on new blocks should go in 
      # the "if newBlocks>0: ... " clause in the Heartbeat function, below

      # Armory executes newBlock functions in the readBlkFileUpdate()
      # which occurs in the heartbeat function.  execOnNewBlock() may be 
      # called before readBlkFileUpdate() has run, and thus TheBDM may 
      # not have the new block data yet (there's a variety of reason for 
      # this design decision, I can enumerate them for you in an email...)
      
      # Therefore, if you put anything here, it should operate on the header
      # or tx data in a vacuum (without any reliance on TheBDM)
      pass

   #############################################################################
   def showOfflineMsg(self):
      LOGINFO('Offline - not tracking blockchain')

   #############################################################################
   def showOnlineMsg(self):
      LOGINFO('Online - tracking blockchain')



   #############################################################################
   def checkMemoryPoolCorruption(self, mempoolname):
      if not os.path.exists(mempoolname):
         return

      memfile = open(mempoolname, 'r')
      memdata = memfile.read()
      memfile.close()

      binunpacker = BinaryUnpacker(memdata)
      try:
         while binunpacker.getRemainingSize() > 0:
            binunpacker.get(UINT64)
            PyTx().unserialize(binunpacker)
      except:
         os.remove(mempoolname);

   #############################################################################
   def Heartbeat(self, nextBeatSec=1):
      """
      This method is invoked when the app is initialized, and will
      run every 2 seconds, or whatever is specified in the nextBeatSec
      argument.
      """
      # Check for new blocks in the blk000X.dat file
      if TheBDM.getBDMState()=='BlockchainReady':

         prevTopBlock = TheBDM.getTopBlockHeight()
         newBlks = TheBDM.readBlkFileUpdate()
         if newBlks>0:
            self.latestBlockNum = TheBDM.getTopBlockHeight()
            self.topTimestamp   = TheBDM.getTopBlockHeader().getTimestamp()

            prevLedgerSize = len(self.wallet.getTxLedger())

            self.wallet.syncWithBlockchain()
            TheBDM.rescanWalletZeroConf(self.wallet.cppWallet)

            newLedgerSize = len(self.wallet.getTxLedger())

            # If there are no functions to run, just skip all this
            if not len(self.newBlockFunctions)==0:
               # Here's where we actually execute the new-block calls, because
               # this code is guaranteed to execute AFTER the TheBDM has processed
               # the new block data.
               # We walk through headers by block height in case the new block 
               # didn't extend the main chain (this won't run), or there was a 
               # reorg with multiple blocks and we only want to process the new
               # blocks on the main chain, not the invalid ones
               for blknum in range(prevTopBlock+1, self.latestBlockNum+1):
                  cppHeader = TheBDM.getHeaderByHeight(blknum)
                  txHashToPy = lambda h: PyTx().unserialize(TheBDM.getTxByHash(h).serialize())
                  pyHeader = PyBlockHeader().unserialize(header.serialize())
                  pyTxList = [txHashToPy(hsh) for hsh in header.getTxHashList()]
                  for blockFunc in self.newBlockFunctions:
                     blockFunc(pyHeader, pyTxList)

      self.wallet.checkWalletLockTimeout()
      reactor.callLater(nextBeatSec, self.Heartbeat)



"""
# This is from jgarzik's python-bitcoinrpc tester
import decimal
import json
from jsonrpc import ServiceProxy

class UniversalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

access = ServiceProxy("http://alan:ak3lfd98031knmzwks1ke@127.0.0.1:7070")

# TODO use asserts on this, for now manual inspection will do
newaddress = access.getnewaddress()
"""



#if __name__ == "__main__":
if True:

   rpc_server = Armory_Daemon()
   rpc_server.start()






