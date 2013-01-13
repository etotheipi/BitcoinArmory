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


################################################################################

################################################################################
################################################################################


class Armory_Json_Rpc_Server(jsonrpc.JSONRPC):

   def __init__(self, wallet):
      self.wallet = wallet

   def jsonrpc_getnewaddress(self):
      addr = self.wallet.getNextUnusedAddress()
      return addr.getAddrStr()

   def jsonrpc_getbalance(self):
      int_balance = self.wallet.getBalance()
      decimal_balance = decimal.Decimal(int_balance) / decimal.Decimal(ONE_BTC)
      return float(decimal_balance)

   def jsonrpc_getreceivedbyaddress(self, address):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot get received amount when offline')
      # Only gets correct amount for addresses in the wallet, otherwise 0
      addr160 = addrStr_to_hash160(address)
      txs = self.wallet.getAddrTxLedger(addr160)
      balance = sum([x.getValue() for x in txs if x.getValue() > 0])
      decimal_balance = decimal.Decimal(balance) / decimal.Decimal(ONE_BTC)
      float_balance = float(decimal_balance)
      return float_balance

   def jsonrpc_sendtoaddress(self, bitcoinaddress, amount):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot create transactions when offline')
      return self.create_unsigned_transaction(bitcoinaddress, amount)


   def jsonrpc_listtransactions(self, tx_count=10, from_tx=0):
      #TODO this needs more work
      # - populate the rest of the values in tx_info
      #     - fee
      #     - blocktime
      #     - timereceived
      # Thanks to unclescrooge for inclusions - https://bitcointalk.org/index.php?topic=92496.msg1282975#msg1282975
      # NOTE that this does not use 'account' like in the Satoshi client
      final_tx_list = []
      ledgerEntries = self.wallet.getTxLedger('blk')
      if from_tx >= len(ledgerEntries):
         return []
         
      
      for le in ledgerEntries[from_tx:]:
         le.pprint()
         account = ''
         txHashBin = le.getTxHash()
         cppTx = TheBDM.getTxByHash(txHashBin)
         pytx = PyTx().unserialize(cppTx.serialize())
         for txout in pytx.outputs:
            scrType = getTxOutScriptType(txout.binScript)
            if not scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
              continue
            address = hash160_to_addrStr(TxOutScriptExtractAddr160(txout.binScript))
            if self.wallet.hasAddr(address) == False:
              continue
            else:
               break
         if le.getValue() < 0:
            category = 'send'
         else:
            category = 'receive'
         amount = float(decimal.Decimal(le.getValue()) / decimal.Decimal(ONE_BTC))
         confirmations = TheBDM.getTopBlockHeader().getBlockHeight() - le.getBlockNum()+1
         blockhash = 'TODO'
         blockindex = 'TODO'#le.getBlockNum()
         txid = str(binary_to_hex(le.getTxHash()))
         time = 'TODO'#le.getTxTime()
         tx_info = {
            'account':account,
            'address':address,
            'category':category,
            'amount':amount,
            #'fee': -0,
            'confirmations':confirmations,
            'blockhash':blockhash,
            'blockindex':blockindex,
            #'blocktime': blocktime,
            'txid':txid,
            'time:':time,
            #'timereceived': timereceived
            }
         final_tx_list.append(tx_info)
         if len(final_tx_list) >= tx_count:
            break
      return final_tx_list


   # https://bitcointalk.org/index.php?topic=92496.msg1126310#msg1126310
   def create_unsigned_transaction(self, bitcoinaddress_str, amount_to_send_btc):
      # Get unspent TxOutList and select the coins
      addr160_recipient = addrStr_to_hash160(bitcoinaddress_str)
      totalSend, fee = long(amount_to_send_btc * ONE_BTC), 0
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

      outputPairs = []
      outputPairs.append( [addr160_recipient, totalSend] )
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
         TheBDM.getTopBlockHeader().pprint()

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
         #LOGINFO('Bailing out...')
         #LOGINFO('')
         #os._exit(1)

         # TODO: Rather than exiting, I should send it the CLI args...
         with open(ARMORYD_CONF_FILE, 'r') as f:
            usr,pas = f.readline().strip().split(':')
         
         if CLI_ARGS:
            proxyobj = ServiceProxy("http://%s:%s@127.0.0.1:%d" % (usr,pas,RPC_PORT))
            extraArgs = [] if len(CLI_ARGS)==1 else CLI_ARGS[1:]
            print proxyobj.__getattr__(CLI_ARGS[0])(*extraArgs)
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



if __name__ == "__main__":

   rpc_server = Armory_Daemon()
   rpc_server.start()






