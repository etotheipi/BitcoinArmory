################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
#                                                                              #
# Original copyright transferred from from Ian Coleman (2012)                  #
# Special thanks to Ian Coleman who created the original incarnation of        #
# this file and then transferred the rights to me so I could integrate it      #
# into the Armory project.  And even more thanks to him for his advice         #
# on upgrading its security features and other capabilities.                   #
#                                                                              #
################################################################################


#####
# ORIGINAL comments from Ian Coleman, circa July 2012:
#
# This is a json-rpc interface to armory - http://bitcoinarmory.com/
#
# Where possible this follows conventions established by the Satoshi client.
# Does not require armory to be installed or running, this is a standalone
# application. Requires bitcoind process to be running before starting armoryd.
# Requires an armory wallet (can be watching only) to be in the same folder as
# the armoryd script. Works with testnet, use --testnet flag when starting the
# script.
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

################################################################################
#
# Random JSON notes should be placed here as desired.
#
# - JSON can only send back data as strings or floats.
# - If a returned string has a newline char, JSON will convert it to the string
#   "\n" (minus quotation marks).
# - JSON can only send back data as an individual value or dictionary (i.e., no
#   lists or other structs are allowed).
# - In general, if you need to pass an actual newline via the command line, type
#   $'\n' instead of \n or \\n. (Files have no special requirements.)
# - When all else fails, and you have no clue how to pass data via JSON, read
#   RFC 4627.
#
################################################################################

import decimal

from twisted.cred.checkers import FilePasswordDB
from twisted.internet import reactor
from twisted.web import server
from txjsonrpc.auth import wrapResource
from txjsonrpc.web import jsonrpc

from armoryengine.ALL import *
from collections import defaultdict
from itertools import islice
from armoryengine.Decorators import EmailOutput

# Some non-twisted json imports from jgarzik's code and his UniversalEncoder
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
class NotEnoughCoinsError(Exception): pass
class CoinSelectError(Exception): pass
class WalletUnlockNeeded(Exception): pass
class InvalidBitcoinAddress(Exception): pass
class PrivateKeyNotFound(Exception): pass
class AddressNotInWallet(Exception): pass


NOT_IMPLEMENTED = '--Not Implemented--'

################################################################################
# Utility function that takes a list of wallet paths, gets the paths and adds
# the wallets to a wallet set (actually a dictionary, with the wallet ID as the
# key and the wallet as the value), along with adding the wallet ID to a
# separate set.
def addMultWallets(inWltPaths, inWltSet, inWltIDSet):
   '''Function that adds multiple wallets to an armoryd server.'''
   for aWlt in inWltPaths:
      # Logic basically taken from loadWalletsAndSettings()
      try:
         wltLoad = PyBtcWallet().readWalletFile(aWlt)
         wltID = wltLoad.uniqueIDB58

         # For now, no wallets are excluded. If this changes....
         #if aWlt in wltExclude or wltID in wltExclude:
         #   continue

         # A directory can have multiple versions of the same
         # wallet. We'd prefer to skip watch-only wallets.
         if wltID in inWltIDSet:
            LOGWARN('***WARNING: Duplicate wallet (%s) detected' % wltID)
            wo1 = inWltSet[wltID].watchingOnly
            wo2 = wltLoad.watchingOnly
            if wo1 and not wo2:
               prevWltPath = inWltSet[wltID].walletPath
               inWltSet[wltID] = wltLoad
               LOGWARN('First wallet is more useful than the second one...')
               LOGWARN('     Wallet 1 (loaded):  %s', aWlt)
               LOGWARN('     Wallet 2 (skipped): %s', prevWltPath)
            else:
               LOGWARN('Second wallet is more useful than the first one...')
               LOGWARN('     Wallet 1 (skipped): %s', aWlt)
               LOGWARN('     Wallet 2 (loaded):  %s', \
                       inWltSet[wltID].walletPath)
         else:
            # Update the wallet structs.
            inWltSet[wltID] = wltLoad
            inWltIDSet.add(wltID)
      except:
         LOGEXCEPT('***WARNING: Unable to load wallet %s. Skipping.', aWlt)
         raise


################################################################################
# Utility function that takes a list of lockbox paths, gets the paths and adds
# the lockboxes to a lockbox set (actually a dictionary, with the lockbox ID as
# the key and the lockbox as the value), along with adding the lockboxy ID to a
# separate set.
def addMultLockboxes(inLBPaths, inLBSet, inLBIDSet):
   '''Function that adds multiple lockboxes to an armoryd server.'''
   for curLBFile in inLBPaths:
      try:
         curLBList = readLockboxesFile(curLBFile)
         for curLB in curLBList:
            lbID = curLB.uniqueIDB58
            if lbID in inLBIDSet:
               LOGINFO('***WARNING: Duplicate lockbox (%s) detected' % lbID)
            else:
               inLBSet[lbID] = curLB
               inLBIDSet.add(lbID)
      except:
         LOGEXCEPT('***WARNING: Unable to load lockbox file %s. Skipping.', \
                   curLBFile)
         raise


class Armory_Json_Rpc_Server(jsonrpc.JSONRPC):
   #############################################################################
   def __init__(self, wallet, inWltSet={}, inLBSet={}, inWltIDSet=set(), \
                inLBIDSet=set(), tiabRun=False):
   def __init__(self, wallet, inWltSet={}, inLBSet={}, satoshiPort=BITCOIN_PORT,
                armoryHomeDir=ARMORY_HOME_DIR):
      # Save the incoming info. If the user didn't pass in a wallet set, put the
      # wallet in the set (actually a dictionary w/ the wallet ID as the key).
      self.addressMetaData = {}
      self.curWlt = wallet
      self.serverWltSet = inWltSet
      self.serverWltIDSet = inWltIDSet
      self.serverLBSet = inLBSet
      self.serverLBIDSet = inLBIDSet

      self.armoryHomeDir = armoryHomeDir
      if wallet != None:
         wltID = wallet.uniqueIDB58
         self.serverWltSet[wltID] = wallet

      # If any variables rely on whether or not Testnet in a Box is running,
      # we'll set everything up here.
      self.satoshiPort = BITCOIN_PORT


   #############################################################################
   def jsonrpc_receivedfromaddress(self, sender):
      totalReceived = 0.0
      ledgerEntries = self.curWlt.getTxLedger('blk')
      for entry in ledgerEntries:
         cppTx = TheBDM.getTxByHash(entry.getTxHash())
         if cppTx.isInitialized():
            txBinary = cppTx.serialize()
            pyTx = PyTx().unserialize(txBinary)
            inputsFromSender = 0
            for txin in pyTx.inputs:
               txInAddr = TxInExtractAddrStrIfAvail(txin)
               if sender == txInAddr:
                  inputsFromSender += 1
            if inputsFromSender == len(pyTx.inputs):
               for txout in pyTx.outputs:
                  if self.curWlt.hasAddr(script_to_addrStr(txout.getScript())):
                     totalReceived += txout.value

            elif inputsFromSender > 0:
               # Some inputs are from the sender and other are not
               # TODO: Find the best way to handle this case
               # for now require all inputs to be from the sender to be included
               # in the tally
               pass
      return AmountToJSON(totalReceived)


   #############################################################################
   # backupFilePath is the file to backup the current wallet to.
   # It does not necessarily exist yet.
   def jsonrpc_backupwallet(self, backupFilePath):
      self.curWlt.backupWalletFile(backupFilePath)
      return "Backup succeeded."


   #############################################################################
   # Get a list of UTXOs for the currently loaded wallet.
   def jsonrpc_listunspent(self):
      # Return a dictionary with a string as the key and a wallet B58 value as
      # the value.
      utxoList = self.curWlt.getTxOutList('unspent')
      utxoDict = {}

      if TheBDM.getBDMState()=='BlockchainReady':
         curTxOut = 1
         for u in utxoList:
            curTxOutStr = 'UTXO %05d' % curTxOut
            utxoDict[curTxOutStr] = binary_to_hex(u.getOutPoint().serialize())
            curTxOut += 1
      else:
         LOGERROR('Blockchain not ready. Values will not be reported.')

      return utxoDict


   #############################################################################
   # Get a list of UTXOs for the wallet associated with the Base58 address
   # passed into the function.
   def jsonrpc_listaddrunspent(self, inB58):
      # Return a dictionary with a string as the key and a wallet B58 value as
      # the value.
      curTxOut = 1
      utxoDict = {}
      a160 = addrStr_to_hash160(inB58, False)[1]
      if self.curWlt.addrMap.has_key(a160):
         utxoList = self.curWlt.getAddrByHash160(a160).scanBlockchainForAddress()

      for u in utxoList:
         curTxOutStr = 'UTXO %05d' % curTxOut
         utxoDict[curTxOutStr] = binary_to_hex(u.getOutPoint().serialize())
         curTxOut += 1
      return utxoDict


   #############################################################################
   def jsonrpc_importprivkey(self, privkey):
      self.curWlt.importExternalAddressData(privKey=privkey)


   #############################################################################
   def jsonrpc_getrawtransaction(self, txHash, verbose=0, endianness=BIGENDIAN):
      rawTx = None
      cppTx = TheBDM.getTxByHash(hex_to_binary(txHash, endianness))
      if cppTx.isInitialized():
         txBinary = cppTx.serialize()
         pyTx = PyTx().unserialize(txBinary)
         rawTx = binary_to_hex(pyTx.serialize())
         if verbose:
            result = self.jsonrpc_decoderawtransaction(rawTx)
            result['hex'] = rawTx
         else:
            result = rawTx
      else:
         LOGERROR('Tx hash not recognized by TheBDM: %s' % txHash)
         result = None

      return result


   #############################################################################
   def jsonrpc_gettxout(self, txHash, n, binary=0):
      n = int(n)
      txOut = None
      cppTx = TheBDM.getTxByHash(hex_to_binary(txHash, BIGENDIAN))
      if cppTx.isInitialized():
         txBinary = cppTx.serialize()
         pyTx = PyTx().unserialize(txBinary)
         if n < len(pyTx.outputs):
            # If the user doesn't want binary data, return a formatted string,
            # otherwise return a hex string with the raw TxOut data.
            txOut = pyTx.outputs[n]
            result = {'value' : AmountToJSON(txOut.value),
                      'script' : txOut.binScript if binary else binary_to_hex(txOut.binScript)}
         else:
            LOGERROR('Tx output index is invalid: #%d' % n)
      else:
         LOGERROR('Tx hash not recognized by TheBDM: %s' % binary_to_hex(txHash))

      return result


   #############################################################################
   def jsonrpc_encryptwallet(self, passphrase):
      if self.curWlt.isLocked:
         raise WalletUnlockNeeded
      self.curWlt.changeWalletEncryption( securePassphrase=SecureBinaryData(passphrase) )
      self.curWlt.lock()


   #############################################################################
   def jsonrpc_unlockwallet(self, passphrase, timeout):
      self.curWlt.unlock( securePassphrase=SecureBinaryData(passphrase),
                            tempKeyLifetime=timeout)


   #############################################################################
   def getScriptPubKey(self, txOut):
      addrList = []
      scriptType = getTxOutScriptType(txOut.binScript)
      if scriptType in CPP_TXOUT_STDSINGLESIG:
         M = 1
         addrList = [script_to_addrStr(txOut.binScript)]
      elif scriptType == CPP_TXOUT_P2SH:
         M = -1
         addrList = [script_to_addrStr(txOut.binScript)]
      elif scriptType==CPP_TXOUT_MULTISIG:
         M, N, addr160List, pub65List = getMultisigScriptInfo(txOut.binScript)
         addrList = [hash160_to_addrStr(a160) for a160 in addr160List]
      elif scriptType == CPP_TXOUT_NONSTANDARD:
         M = -1

      opStringList = convertScriptToOpStrings(txOut.binScript)
      return { 'asm'       : ' '.join(opStringList),
               'hex'       : binary_to_hex(txOut.binScript),
               'reqSigs'   : M,
               'type'      : CPP_TXOUT_SCRIPT_NAMES[scriptType],
               'addresses' : addrList }


   #############################################################################
   def jsonrpc_decoderawtransaction(self, hexString):
      pyTx = PyTx().unserialize(hex_to_binary(hexString))

      #####
      # Accumulate TxIn info
      vinList = []
      for txin in pyTx.inputs:
         prevHash = txin.outpoint.txHash
         scrType = getTxInScriptType(txin)
         # ACR:  What is asm, and why is basically just binScript?
         oplist = convertScriptToOpStrings(txin.binScript)
         scriptSigDict = { 'asm' : ' '.join(oplist),
                           'hex' : binary_to_hex(txin.binScript) }

         if not scrType == CPP_TXIN_COINBASE:
            vinList.append(  { 'txid'      : binary_to_hex(prevHash, BIGENDIAN),
                               'vout'      : txin.outpoint.txOutIndex, 
                               'scriptSig' : scriptSigDict, 
                               'sequence'  : txin.intSeq})
         else:
            vinList.append( {  'coinbase'  : binary_to_hex(txin.binScript),
                               'sequence'  : txin.intSeq })

      #####
      # Accumulate TxOut info
      voutList = []
      for n,txout in enumerate(pyTx.outputs):
         voutList.append( { 'value' : AmountToJSON(txout.value),
                            'n' : n,
                            'scriptPubKey' : self.getScriptPubKey(txout) } )


      #####
      # Accumulate all the data to return
      result = { 'txid'     : pyTx.getHashHex(BIGENDIAN),
                 'version'  : pyTx.version,
                 'locktime' : pyTx.lockTime,
                 'vin'      : vinList, 
                 'vout'     : voutList }

      return result


   #############################################################################
   def jsonrpc_getnewaddress(self):
      addr = self.curWlt.getNextUnusedAddress()
      return addr.getAddrStr()


   #############################################################################
   def jsonrpc_dumpprivkey(self, addr58):
      # Cannot dump the private key for a locked wallet
      if self.curWlt.isLocked:
         raise WalletUnlockNeeded
      # The first byte must be the correct net byte, and the
      # last 4 bytes must be the correct checksum
      if not checkAddrStrValid(addr58):
         raise InvalidBitcoinAddress

      addr160 = addrStr_to_hash160(addr58, False)[1]

      pyBtcAddress = self.curWlt.getAddrByHash160(addr160)
      if pyBtcAddress == None:
         raise PrivateKeyNotFound
      return pyBtcAddress.serializePlainPrivateKey()


   #############################################################################
   def jsonrpc_getwalletinfo(self):
      self.isReady = (TheBDM.getBDMState() == 'BlockchainReady' and \
                      satoshiIsAvailable(port=self.satoshiPort))

      wltInfo = { \
                  'name':  self.curWlt.labelName,
                  'description':  self.curWlt.labelDescr,
                  'balance': AmountToJSON(self.curWlt.getBalance('Spend')) if \
                             self.isReady else -1,
                  'keypoolsize':  self.curWlt.addrPoolSize,
                  'numaddrgen': len(self.curWlt.addrMap),
                  'highestusedindex': self.curWlt.highestUsedChainIndex
                }

      return wltInfo


   #############################################################################
   def jsonrpc_getbalance(self, baltype='spendable'):
      retVal = -1

      # Proceed only if the blockchain's good. Wallet value could be unreliable
      # otherwise.
      if TheBDM.getBDMState()=='BlockchainReady' and \
         satoshiIsAvailable(port=self.satoshiPort):
         if not baltype in ['spendable', 'spend', 'unconf', 'unconfirmed', \
                            'total', 'ultimate', 'unspent', 'full']:
            LOGERROR('Unrecognized getbalance string: "%s"', baltype)
         else:
            retVal = AmountToJSON(self.curWlt.getBalance(baltype))
      else:
         LOGERROR('Blockchain not ready. Values will not be reported.')

      return retVal


   #############################################################################
   def jsonrpc_getaddrbalance(self, inB58, baltype='spendable'):
      retVal = -1

      if not baltype in ['spendable','spend', 'unconf', 'unconfirmed', \
                         'ultimate','unspent', 'full']:
         LOGERROR('Unrecognized getaddrbalance string: "%s"', baltype)
      elif not satoshiIsAvailable(port=self.satoshiPort):
         LOGERROR('Bitcoin client is not online. Will not give a balance.')
      else:
         # For now, allow only Base58 addresses.
         a160 = addrStr_to_hash160(inB58, False)[1]
         if self.curWlt.addrMap.has_key(a160):
            retVal = AmountToJSON(self.curWlt.getAddrBalance(a160, baltype))

      return retVal


   #############################################################################
   def jsonrpc_getreceivedbyaddress(self, address):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot get received amount when offline')
      # Only gets correct amount for addresses in the wallet, otherwise 0
      addr160 = addrStr_to_hash160(address, False)[1]

      txs = self.curWlt.getAddrTxLedger(addr160)
      balance = sum([x.getValue() for x in txs if x.getValue() > 0])
      return AmountToJSON(balance)


   #############################################################################
   def jsonrpc_sendtoaddress(self, bitcoinaddress, amount):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot create transactions when offline')
      script = addrStr_to_script(bitcoinaddress)
      amtCoin = JSONtoAmount(amount)
      return self.create_unsigned_transaction([[script, amtCoin]])


   #############################################################################
   def jsonrpc_sendmany(self, *args):
      if CLI_OPTIONS.offline:
         raise ValueError('Cannot create transactions when offline')

      scriptValuePairs = []
      for a in args:
         r,v = a.split(':')
         scriptValuePairs.append([addrStr_to_script(r), JSONtoAmount(v)])

      return self.create_unsigned_transaction(scriptValuePairs)


   #############################################################################
   def jsonrpc_getledgersimple(self, tx_count=10, from_tx=0):
      return self.jsonrpc_getledger(tx_count, from_tx, simple=True)


   #############################################################################
   # NB: For now, this is incompatible with lockboxes.
   def jsonrpc_getledger(self, tx_count=10, from_tx=0, simple=False):
      final_le_list = []
      tx_count = int(tx_count)
      from_tx = int(from_tx)
      ledgerEntries = self.curWlt.getTxLedger('blk')
         
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

         #cppHead = cppTx.getHeaderPtr()
         cppHead = TheBDM.getHeaderPtrForTx(cppTx)
         if not cppHead.isInitialized():
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

         scrAddrs = [cppTx.getTxOutCopy(i).getScrAddressStr() for i in range(cppTx.getNumTxOut())]
         allRecips = [CheckHash160(r) for r in scrAddrs]
         first160 = ''
         if cppTx.getNumTxOut()==1:
            first160 = allRecips[0]
            change160 = ''
         elif isToSelf:
            # Sent-to-Self tx
            amtCoins,changeIdx = determineSentToSelfAmt(le, self.curWlt)
            change160 = allRecips[changeIdx]
            for iout,recip160 in enumerate(allRecips):
               if not iout==changeIdx:
                  first160 = recip160
                  break
         elif netCoins<0:
            # Outgoing transaction (process in reverse order so get first)
            amtCoins = -1*(netCoins+feeCoins)
            for recip160 in allRecips[::-1]:
               if self.curWlt.hasAddr(recip160):
                  change160 = recip160
               else:
                  first160 = recip160
         else:
            # Incoming transaction
            amtCoins = netCoins
            for recip160 in allRecips[::-1]:
               if self.curWlt.hasAddr(recip160):
                  first160 = recip160
               else:
                  change160 = recip160


         # amtCoins: amt of BTC transacted, always positive (how big are outputs
         #           minus change?)
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

         nconf = TheBDM.getTopBlockHeader().getBlockHeight()-le.getBlockNum()+1


         myinputs,  otherinputs = [],[]
         for iin in range(cppTx.getNumTxIn()):
            sender = CheckHash160(TheBDM.getSenderScrAddr(cppTx.getTxInCopy(iin)))
            val    = TheBDM.getSentValue(cppTx.getTxInCopy(iin))
            addTo  = (myinputs if self.curWlt.hasAddr(sender) else otherinputs)
            addTo.append( {'address': hash160_to_addrStr(sender), \
                           'amount':  AmountToJSON(val)} )

         myoutputs, otheroutputs = [], []
         for iout in range(cppTx.getNumTxOut()):
            recip = CheckHash160(cppTx.getTxOutCopy(iout).getScrAddressStr())
            val   = cppTx.getTxOutCopy(iout).getValue();
            addTo = (myoutputs if self.curWlt.hasAddr(recip) else otheroutputs)
            addTo.append( {'address': hash160_to_addrStr(recip), \
                           'amount':  AmountToJSON(val)} )

         tx_info = {
                     'direction' :    txDir,
                     'wallet' :       self.curWlt.uniqueIDB58,
                     'amount' :       AmountToJSON(amtCoins),
                     'netdiff' :      AmountToJSON(netCoins),
                     'fee' :          AmountToJSON(feeCoins),
                     'txid' :         txHashHex,
                     'blockhash' :    headHashHex,
                     'confirmations': nconf,
                     'txtime' :       le.getTxTime(),
                     'txsize' :       len(cppTx.serialize()),
                     'blocktime' :    headtime,
                     'comment' :      self.curWlt.getComment(txHashBin),
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
   # NB: For now, this is incompatible with lockboxes.
   def jsonrpc_listtransactions(self, tx_count=10, from_tx=0):
      # This does not use 'account's like in the Satoshi client

      final_tx_list = []
      ledgerEntries = self.curWlt.getTxLedger('blk')

      sz = len(ledgerEntries)
      lower = min(sz, from_tx)
      upper = min(sz, from_tx+tx_count)

      txSet = set([])

      for i in range(lower,upper):

         le = ledgerEntries[i]
         txHashBin = le.getTxHash()
         if txHashBin in txSet:
            continue

         txSet.add(txHashBin)
         txHashHex = binary_to_hex(txHashBin, BIGENDIAN)

         cppTx = TheBDM.getTxByHash(txHashBin)
         if not cppTx.isInitialized():
            LOGERROR('Tx hash not recognized by TheBDM: %s' % txHashHex)

         #cppHead = cppTx.getHeaderPtr()
         cppHead = TheBDM.getHeaderPtrForTx(cppTx)
         if not cppHead.isInitialized:
            LOGERROR('Header pointer is not available!')

         blockIndex = cppTx.getBlockTxIndex()
         blockHash  = binary_to_hex(cppHead.getThisHash(), BIGENDIAN)
         blockTime  = le.getTxTime()
         isToSelf   = le.isSentToSelf()
         feeCoin   = getFeeForTx(txHashBin)
         totalBalDiff = le.getValue()
         nconf = TheBDM.getTopBlockHeader().getBlockHeight()-le.getBlockNum()+1


         # We have potentially change outputs on any outgoing transactions.
         # If sent-to-self, assume 1 change address (max chain idx), all others
         # are receives
         recipVals = []
         for iout in range(cppTx.getNumTxOut()):
            recip = CheckHash160(cppTx.getTxOutCopy(iout).getScrAddressStr())
            val   = cppTx.getTxOutCopy(iout).getValue()
            recipVals.append([recip,val])

         if cppTx.getNumTxOut()==1:
            changeAddr160 = ""
            targAddr160 = CheckHash160(cppTx.getTxOutCopy(0).getScrAddressStr())
         elif isToSelf:
            selfamt,changeIdx = determineSentToSelfAmt(le, self.curWlt)
            if changeIdx==-1:
               changeAddr160 = ""
            else:
               changeAddr160 = recipVals[changeIdx]
               del recipVals[changeIdx]
            targAddr160 = recipVals[0][0]
         elif totalBalDiff < 0:
            # This was ultimately an outgoing transaction
            for iout,rv in enumerate(recipVals):
               if self.curWlt.hasAddr(rv[0]):
                  changeAddr160 = rv[0]
                  del recipVals[iout]
                  break
            targAddr160 = recipVals[0][0]
         else:
            # Receiving transaction
            for recip,val in recipVals:
               if self.curWlt.hasAddr(recip):
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
            if totalBalDiff>0 and not self.curWlt.hasAddr(a160):
               # This is a receiving tx and this is other addr sending to other
               # addr
               continue

            if a160=='\x00'*20:
               address = '<Non-Standard Script>'
            else:
               address = hash160_to_addrStr(a160)

            if not self.curWlt.hasAddr(a160):
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
      isReady = (TheBDM.getBDMState() == 'BlockchainReady' and \
                 satoshiIsAvailable(port=self.satoshiPort))

      info = { \
               'version':           getVersionInt(BTCARMORY_VERSION),
               'protocolversion':   0,  
               'walletversion':     getVersionInt(PYBTCWALLET_VERSION),
               'bdmstate':          TheBDM.getBDMState(),
               'balance':           AmountToJSON(self.curWlt.getBalance()) if isReady else -1,
               'blocks':            TheBDM.getTopBlockHeight(),
               'connections':       (0 if isReady else 1),
               'proxy':             '',
               'difficulty':        TheBDM.getTopBlockHeader().getDifficulty() if isReady else -1,
               'testnet':           USE_TESTNET,
               'keypoolsize':       self.curWlt.addrPoolSize            }
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
      # TODO fix size. It returns max int, as does # Tx. They're never set.
      # out['size'] = head.getBlockSize()
      out['height'] = head.getBlockHeight()
      out['time'] = head.getTimestamp()
      out['nonce'] = head.getNonce()
      out['difficulty'] = head.getDifficulty()
      out['difficultysum'] = head.getDifficultySum()
      out['mainbranch'] = head.isMainBranch()
      out['bits'] = binary_to_hex(head.getDiffBits(), BIGENDIAN)
      out['merkleroot'] = binary_to_hex(head.getMerkleRoot(), BIGENDIAN)
      out['version'] = head.getVersion()
      out['rawheader'] = binary_to_hex(head.serialize())

      # TODO: Fix this part. getTxRefPtrList was never defined.
      # txlist = head.getTxRefPtrList() 
      # ntx = len(txlist)
      # out['tx'] = ['']*ntx
      # for i in range(ntx):
      #    out['tx'][i] = binary_to_hex(txlist[i].getThisHash(), BIGENDIAN)

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
         op = tx.getTxInCopy(i).getOutPoint()
         prevtx = TheBDM.getTxByHash(op.getTxHash())
         if not prevtx.isInitialized():
            haveAllInputs = False
            txindata.append( { 'address': '00'*32, 
                               'value':   '-1',
                               'ismine':   False,
                               'fromtxid': binary_to_hex(op.getTxHash(), BIGENDIAN),
                               'fromtxindex': op.getTxOutIndex()})
         else:
            txout = prevtx.getTxOutCopy(op.getTxOutIndex())
            inputvalues.append(txout.getValue())
            recip160 = CheckHash160(txout.getScrAddressStr())
            txindata.append( { 'address': hash160_to_addrStr(recip160),
                               'value':   AmountToJSON(txout.getValue()),
                               'ismine':   self.curWlt.hasAddr(recip160),
                               'fromtxid': binary_to_hex(op.getTxHash(), BIGENDIAN),
                               'fromtxindex': op.getTxOutIndex()})

      txoutdata = []
      for i in range(tx.getNumTxOut()): 
         txout = tx.getTxOutCopy(i)
         a160 = CheckHash160(txout.getScrAddressStr())
         txoutdata.append( { 'value': AmountToJSON(txout.getValue()),
                             'ismine':  self.curWlt.hasAddr(a160),
                             'address': hash160_to_addrStr(a160)})
         outputvalues.append(txout.getValue())

      fee = sum(inputvalues)-sum(outputvalues)
      out['fee'] = AmountToJSON(fee)

      out['infomissing'] = not haveAllInputs
      out['inputs'] = txindata
      out['outputs'] = txoutdata

      if not tx.isMainBranch():
         return out

      # The tx is in a block, fill in the rest of the data
      out['confirmations'] = TheBDM.getTopBlockHeight()-tx.getBlockHeight()+1
      out['time'] = tx.getBlockTimestamp()
      out['orderinblock'] = tx.getBlockTxIndex()

      le = self.curWlt.cppWallet.calcLedgerEntryForTx(tx)
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
   def create_unsigned_transaction(self, scriptValuePairs):
      # Get unspent TxOutList and select the coins
      #addr160_recipient = addrStr_to_hash160(bitcoinaddress_str)

      totalSend = long( sum([rv[1] for rv in scriptValuePairs]) )
      fee = 0

      spendBal = self.curWlt.getBalance('Spendable')
      utxoList = self.curWlt.getTxOutList('Spendable')
      utxoSelect = PySelectCoins(utxoList, totalSend, fee)

      minFeeRec = calcMinSuggestedFees(utxoSelect, totalSend, fee, len(scriptValuePairs))[1]
      if fee<minFeeRec:
         if totalSend + minFeeRec > spendBal:
            raise NotEnoughCoinsError, "You can't afford the fee!"
         utxoSelect = PySelectCoins(utxoList, totalSend, minFeeRec)
         fee = minFeeRec

      if len(utxoSelect)==0:
         raise CoinSelectError, "Coin selection failed. This shouldn't happen."

      totalSelected = sum([u.getValue() for u in utxoSelect])
      totalChange = totalSelected - (totalSend  + fee)

      outputPairs = scriptValuePairs[:]
      if totalChange > 0:
         nextAddr = self.curWlt.getNextUnusedAddress().getAddrStr()
         outputPairs.append( [addrStr_to_script(nextAddr), totalChange] )

      random.shuffle(outputPairs)

      # If this has nothing to do with lockboxes, we need to make sure
      # we're providing a key map for the inputs
      pubKeyMap = {}
      for utxo in utxoSelect:
         scrType = getTxOutScriptType(utxo.getScript())
         if scrType in CPP_TXOUT_STDSINGLESIG:
            scrAddr = utxo.getRecipientScrAddr()
            a160 = scrAddr_to_hash160(scrAddr)[1]
            addrObj = self.curWlt.getAddrByHash160(a160)
            if addrObj:
               pubKeyMap[scrAddr] = addrObj.binPublicKey65.toBinStr()

      txdp = UnsignedTransaction().createFromTxOutSelection(utxoSelect, outputPairs, pubKeyMap)

      return txdp.serializeAscii()


   #############################################################################
   # Helper function that gets an uncompressed public key from a wallet, based
   # on an index value.
   def getPKFromWallet(self, inWlt, inIdx):
      retStr = ''
      lbWltAddrList = inWlt.getAddrList()
      if lbWltAddrList[inIdx].hasPubKey():
         retStr = lbWltAddrList[inIdx].getPubKey().toHexStr()
      else:
         retStr = 'Wallet %s doesn\'t have a public key at index %d' % \
                  (inWlt.uniqueIDB58, inIdx)
      return retStr


   #############################################################################
   # Create a multisig lockbox. The user must specify the number of keys needed
   # to unlock a lockbox and the number of keys in a lockbox. Optionally, the
   # user may specify the public keys or wallets to use. If wallets are
   # specified, an address will be chosen from the wallet. If public keys are
   # specified, keys may be compressed or uncompressed. (For now, compressed
   # keys will be decompressed inside Armory before being used.) If no extra
   # arguments are specified, the number of addresses in the lockbox must be
   # less than or equal to the number currently loaded into armoryd, and one
   # address each will be chosen from a random subset of lockboxes.
   #
   # Example: We wish to create a 2-of-3 lockbox based on 2 loaded wallets
   # (27TchD13 and AaAaaAQ4) and a compressed public key. The following command
   # would be executed.
   # armoryd 2 3 27TchD13 AaAaaAQ4 02010203040506070809....
   def jsonrpc_createlockbox(self, numM, numN, *args):
      m = int(numM)
      n = int(numN)
      errStr = ''
      errName = 'Error'
      retDict = {}

      # Do some basic error checking before proceeding.
      if m > n:
         errStr = 'The user requires more addresses to unlock a lockbox (%d) ' \
                  'than are required to create a lockbox (%d).' % (m, n)
         LOGERROR(errStr)
         retDict[errName] = errStr
      elif m > LB_MAXM:
         errStr = 'The number of signatures required to unlock a lockbox ' \
                  '(%d) exceeds the maximum allowed (%d)' % (m, LB_MAXM)
         LOGERROR(errStr)
         retDict[errName] = errStr
      elif n > LB_MAXN:
         errStr = 'The number of wallets required to create a lockbox (%d) ' \
                  'exceeds the maximum allowed (%d)' % (n, LB_MAXN)
         LOGERROR(errStr)
         retDict[errName] = errStr
      elif args and len(args) > n:
         errStr = 'The number of arguments specified to create a lockbox ' \
                  '(%d) exceeds the number required to create the lockbox ' \
                  '(%d)' % (len(args), n)
         LOGERROR(errStr)
         retDict[errName] = errStr
      elif not args and n > len(self.serverWltSet):
         errStr = 'The number of addresses required to create a lockbox ' \
                  '(%d) exceeds the number of loaded wallets (%d)' % \
                  (n, len(self.serverWltSet))
         LOGERROR(errStr)
         retDict[errName] = errStr
      else:
         allArgsValid = True
         badArg = ''
         addrList = [] # Starts as string list, eventually becomes binary.
         addrNameList = [] # String list

         # We need to determine which args are keys, which are wallets and which
         # are garbage.
         if args:
            for lockboxItem in args:
               # First, check if the arg is a wallet ID. If not, check if it's a
               # valid pub key. If not, the input's invalid.
               try:
                  # If search item's a pub key, it'll cause a KeyError to be
                  # thrown. That's fine. We can catch it and keep on truckin'.
                  lbWlt = self.serverWltSet[lockboxItem]
                  lbWltHighestIdx = lbWlt.getHighestUsedIndex()
                  lbWltPK = self.getPKFromWallet(lbWlt, lbWltHighestIdx)
                  addrList.append(lbWltPK)
                  addrName = 'Addr %d from wallet %s' % (lbWltHighestIdx, \
                                                         lockboxItem)
                  addrNameList.append(addrName)

               except KeyError:
                  # A screwy wallet ID will end up here, so we need to catch a
                  # TypeError. End of the line if the error's thrown.
                  try:
                     # A pub key could be fake but in the proper form, so we
                     # have a second place where a value can fail. Catch it.
                     if isValidPK(lockboxItem, True):
                        addrList.append(lockboxItem)
                        addrName = 'Addr starting with %s' % lockboxItem[0:12]
                        addrNameList.append(addrName)
                     else:
                        badArg = lockboxItem
                        allArgsValid = False
                        break

                  except TypeError:
                     badArg = lockboxItem
                     allArgsValid = False
                     break

         else:
            # If we have no args, we'll just dip into the loaded wallets. Just
            # make sure we get the proper # of wallets. For now, the wallets we
            # use will essentially be chosen at random.
            numWlts = min(n, len(self.serverWltSet))
            for lbWlt in islice(self.serverWltSet.values(), 0, numWlts):
               lbWltHighestIdx = lbWlt.getHighestUsedIndex()
               lbWltPK = self.getPKFromWallet(lbWlt, lbWltHighestIdx)
               addrList.append(lbWltPK)
               addrName = 'Addr %d from wallet %s' % (lbWltHighestIdx, \
                                                      lbWlt.uniqueIDB58)
               addrNameList.append(addrName)

         # Do some basic error checking before proceeding.
         if allArgsValid == False:
            errStr = 'The user has specified an argument (%s) that is ' \
                     'invalid.' % badArg
            LOGERROR(errStr)
            retDict[errName] = errStr
         else:
            # We must sort the addresses and comments together. It's important
            # to keep this code in sync with any other code creating lockboxes.
            # Also, convert the key list from hex to binary to support multisig
            # conversion while also minimizing coding.
            decorated  = [[pk,comm] for pk,comm in zip(addrList, \
                                                       addrNameList)]
            decorSort  = sorted(decorated, key=lambda pair: pair[0])
            for i, pair in enumerate(decorSort):
               addrList[i]     = hex_to_binary(pair[0])
               addrNameList[i] = pair[1]

            # Let the lockbox creation begin! We'll write it to a file and
            # return the hex representation via JSON.
            pkListScript = pubkeylist_to_multisig_script(addrList, m)
            lbID = calcLockboxID(pkListScript)
            lbCreateDate = long(RightNow())
            lbName = 'Lockbox %s' % lbID
            lbDescrip = '%s - %d-of-%d - Created by armoryd' % (lbID, m, n)
            self.lockbox = MultiSigLockbox(pkListScript, lbName, \
                                           lbDescrip, addrNameList, \
                                           lbCreateDate)

            # To be safe, we'll write the LB only if Armory doesn't already have
            # a copy.
            if lbID in self.serverLBSet.keys():
               errStr = 'Lockbox %s already exists' % lbID
               LOGWARN(errStr)
               retDict[errName] = errStr
            else:
               # Write to the "master" LB list used by Armory and an individual
               # file, and load the LB into our LB set.
               lbFileName = 'Multisig_%s.lockbox.txt' % lbID
               lbFilePath = os.path.join(self.armoryHomeDir, lbFileName)
               writeLockboxesFile([self.lockbox], 
                                  os.path.join(self.armoryHomeDir, MULTISIG_FILE_NAME), True)
               writeLockboxesFile([self.lockbox], lbFilePath, False)
               self.serverLBSet[lbID] = self.lockbox

               # Finally, we'll write lockbox data to the return dict.
               for curKeyNum, curKey in enumerate(addrList):
                  curKeyStr = 'Key %02d' % (curKeyNum + 1)
                  retDict[curKeyStr] = binary_to_hex(curKey)

               for curKeyComNum, curKeyCom in enumerate(addrNameList):
                  curKeyComStr = 'Key %02d Comment' % (curKeyComNum + 1)
                  retDict[curKeyComStr] = curKeyCom

               lbDStr = 'Lockbox Description'
               retDict[lbDStr] = lbDescrip
               lbStr = 'Lockbox ID'
               retDict[lbStr] = lbID
               reqSigStr = 'Required Signature Number'
               retDict[reqSigStr] = numM
               totalSigStr = 'Total Signature Number'
               retDict[totalSigStr] = numN

      return retDict

   #############################################################################
   # Get a multisig lockbox info. 
   def jsonrpc_getlockboxinfo(self, lockboxString):
      retDict = {}
      lockbox = MultiSigLockbox().unserializeAscii(lockboxString)
      
      # Finally, we'll write lockbox data to the return dict.
      for curKeyNum, curKey in enumerate(lockbox.pubKeys):
         curKeyStr = 'Key %02d' % (curKeyNum + 1)
         retDict[curKeyStr] = binary_to_hex(curKey)

      for curKeyComNum, curKeyCom in enumerate(lockbox.commentList):
         curKeyComStr = 'Key %02d Comment' % (curKeyComNum + 1)
         retDict[curKeyComStr] = curKeyCom

      lbDStr = 'Lockbox Description'
      retDict[lbDStr] = lockbox.longDescr
      lbStr = 'Lockbox ID'
      retDict[lbStr] = lockbox.uniqueIDB58
      reqSigStr = 'Required Signature Number'
      retDict[reqSigStr] = lockbox.M
      totalSigStr = 'Total Signature Number'
      retDict[totalSigStr] = lockbox.N

      return retDict

   #############################################################################
   # Receive a e-mail notification when money is sent from the active wallet.
   # The e-mail will list the address(es) that sent the money, along with the
   # accompanying transaction(s) and any metadata associated with the
   # address(es). Examples of usage are as follows, with clarification of
   # command line arguments provided as needed.
   #
   # 1)SMTP server port specified, 1 recipient, e-mail subject specified,
   #   "add" command used by default.
   #   armoryd watchwallet s@x.com smtp.x.com:465 myPass123 r@y.org Hi\ Friend\!
   # 2)SMTP server port defaults to 587, 2 recipients (delimited by a colon), no
   #   subject specified, "add" command specified.
   #   armoryd watchwallet sender@a.com smtp.a.com 321PassMy
   #     recip1@gmail.com:recip2@yahoo.com watchCmd=add
   # 3)E-mail notifications from a given e-mail address are stopped.
   #   armoryd watchwallet sender@c.net watchCmd=remove
   def jsonrpc_watchwallet(self, send_from, smtpServer=None, password=None,
                           send_to=None, subject=None, watchCmd='add'):
      retStr = 'watchwallet command failed due to a bad command.'

      if not watchCmd in ['add', 'remove']:
         LOGERROR('Unrecognized watchwallet command: "%s"', watchCmd)
      else:
         send_to = send_to.split(":")

         # Write the funct to be run when a block arrives with a transaction
         # where a wallet has sent money.
         @EmailOutput(send_from, smtpServer, password, send_to, subject)
         def reportTxFromAddrInNewBlock(pyHeader, pyTxList):
            result = ''
            for pyTx in pyTxList:
               for pyTxIn in pyTx.inputs:
                  sendingAddrStr = TxInExtractAddrStrIfAvail(pyTxIn)
                  if len(sendingAddrStr) > 0:
                     sendingAddrHash160 = addrStr_to_hash160(sendingAddrStr, \
                                                             False)[1]
                     if self.curWlt.addrMap.has_key(sendingAddrHash160):
                        sendingAddr = self.curWlt.addrMap[sendingAddrHash160]
                        result = ''.join([result, '\n', sendingAddr.toString(), \
                                          '\n'])
                        # print the meta data
                        if sendingAddrStr in self.addressMetaData:
                           result = ''.join([result, "\nMeta Data: ", \
                                             str(self.addressMetaData[sendingAddrStr]), \
                                             '\n'])
                        result = ''.join([result, '\n', pyTx.toString()])

            return result

         # Add or remove e-mail functs based on the user's command.
         if watchCmd == 'add':
            rpc_server.newBlockFunctions[send_from].append(reportTxFromAddrInNewBlock)
         elif watchCmd == 'remove':
            rpc_server.newBlockFunctions[send_from] = []
         retStr = 'watchwallet command succeeded.'

      return retStr


   #############################################################################
   # Send ASCII-encoded lockboxes to recipients via e-mail. For now, only
   # lockboxes from ArmoryQt's master list (multisigs.txt) or from the Armory
   # home directory will be searched.
   def jsonrpc_sendlockbox(self, lbIDs, sender, server, pwd, recips,
                           msgSubj=None):
      # Initial setup
      retStr = 'sendlockbox command succeeded.'
      if msgSubj == None:
         msgSubj = 'Armory Lockboxes'
      lbIDs = lbIDs.split(":")

      # Write the decorated function that will send the e-mail out.
      @EmailOutput(sender, server, pwd, recips, msgSubj)
      def sendLockboxes(lockboxes):
         emailText = '%s has sent you lockboxes used by Armory.' % sender
         emailText += ' The lockboxes can be found printed below.\n\n'
         emailText += 'TOTAL LOCKBOXES: %d\n\n' % len(lockboxes)
         for curLB in lockboxes:
            emailText += self.serverLBSet[curLB].serializeAscii() + '\n\n'

         return emailText

      # Do these lockboxes actually exist? If not, let the user know and bail.
      allLBsValid = True
      for curLB in lbIDs:
         if not curLB in self.serverLBSet.keys():
            LOGERROR('Lockbox %s does not exist! Exiting.' % curLB)
            allLBsValid = False
            retStr = 'sendlockbox command failed. %s does not exist.' % curLB
            break

      # Send the lockbox notifications if all the lockboxes exist.
      if allLBsValid:
         sendLockboxes(lbIDs)

      return retStr


   #############################################################################
   # Associate meta data to an address or addresses
   # Example input:  "{\"mzAtXhy3Z6SLd7rAwNJrL17e8mQkjDVDXh\": {\"chain\": 5,
   # \"index\": 2}, \"mkF5L93F5HLhLmQagX26TdXcvPGHvfjoTM\": {\"CrazyField\": \"what\",
   # \"1\": 1, \"2\": 2}}"
   def jsonrpc_setaddressmetadata(self, newAddressMetaData):
      # Loop once to check the addresses
      # Don't add any meta data if one of the addresses wrong.
      for addr in newAddressMetaData.keys():
         if not checkAddrStrValid(addr):
            raise InvalidBitcoinAddress
         if not self.curWlt.addrMap.has_key(addrStr_to_hash160(addr, False)[1]):
            raise AddressNotInWallet
      self.addressMetaData.update(newAddressMetaData)


   #############################################################################
   # Clear the metadata.
   def jsonrpc_clearaddressmetadata(self):
      self.addressMetaData = {}


   #############################################################################
   # Get the metadata.
   def jsonrpc_getaddressmetadata(self):
      return self.addressMetaData


   #############################################################################
   # Function that gets the B58 string of the currently active wallet.
   def jsonrpc_getactivewallet(self):
      # Return the B58 string of the currently active wallet.
      return self.curWlt.uniqueIDB58


   #############################################################################
   # Function that sets theactive wallet using a B58 string.
   # NB: It appears that more neds to be done here. Certain functionality
   # doesn't seem to be correct when a wallet is switched.
   def jsonrpc_setactivewallet(self, newIDB58):
      # Return a string indicating whether or not the active wallet was set to a
      # new wallet. If the change fails, keep the currently active wallet.
      retStr = ''
      try:
         newWlt = self.serverWltSet[newIDB58]
         self.curWlt = newWlt  # Separate in case ID's wrong & error's thrown.
         LOGINFO('Syncing wallet: %s' % newIDB58)
         self.curWlt.syncWithBlockchain() # Call after each BDM operation.
         retStr = 'Wallet %s is now active.' % newIDB58
      except:
         LOGERROR('setactivewallet - Wallet %s does not exist.' % newIDB58)
         retStr = 'Wallet %s does not exist.' % newIDB58
      return retStr


   #############################################################################
   # Function that lists all the loaded wallets.
   def jsonrpc_listloadedwallets(self):
      # Return a dictionary with a string as the key and a wallet B58 value as
      # the value.
      curKey = 1
      walletList = {}
      for k in self.serverWltSet.keys():
         curWltStr = 'Wallet %04d' % curKey
         walletList[curWltStr] = k
         curKey += 1
      return walletList


   #############################################################################
   # Pull in a signed Tx and get the raw Tx hex data to broadcast. This call
   # works with a regular signed Tx and a signed lockbox Tx if there are already
   # enough signatures.
   def jsonrpc_gethextxtobroadcast(self, txASCIIFile):
      ustxObj = None
      enoughSigs = False
      sigStatus = None
      sigsValid = False
      ustxReadable = False
      allData = ''
      finalTx = None
      self.retStr = 'The transaction data cannot be broadcast'

      # Read in the signed Tx data. HANDLE UNREADABLE FILE!!!
      with open(txASCIIFile, 'r') as lbTxData:
         allData = lbTxData.read()

      # Try to decipher the Tx and make sure it's actually signed.
      try:
         ustxObj = UnsignedTransaction().unserializeAscii(allData)
         sigStatus = ustxObj.evaluateSigningStatus()
         enoughSigs = sigStatus.canBroadcast
         sigsValid = ustxObj.verifySigsAllInputs()
         ustxReadable = True
      except BadAddressError:
         LOGERROR('This transaction contains inconsistent information. This ' \
                  'is probably not your fault...')
         ustxObj = None
         ustxReadable = False
      except NetworkIDError:
         LOGERROR('This transaction is actually for a different network! Did' \
                  'you load the correct transaction?')
         ustxObj = None
         ustxReadable = False
      except (UnserializeError, IndexError, ValueError):
         LOGERROR('This transaction can\'t be read.')
         ustxObj = None
         ustxReadable = False

      # If we have a signed Tx object, let's make sure it's actually usable.
      if ustxObj:
         if not enoughSigs or not sigsValid or not ustxReadable:
            if not ustxReadable:
               if len(allData) > 0:
                  LOGERROR('The Tx data was read but was corrupt.')
               else:
                  LOGERROR('The Tx data couldn\'t be read.')
            if not sigsValid:
                  LOGERROR('The Tx data doesn\'t have valid signatures.')
            if not enoughSigs:
                  LOGERROR('The Tx data doesn\'t have enough signatures.')
         else:
            finalTx = ustxObj.getBroadcastTxIfReady()
            if finalTx:
               newTxHash = finalTx.getHash()
               LOGINFO('Tx %s may be broadcast - %s' % \
                       (binary_to_hex(newTxHash), finalTx.serialize()))
               self.retStr = binary_to_hex(finalTx.serialize())
            else:
               LOGERROR('The Tx data isn\'t ready to be broadcast')

      return self.retStr


   #############################################################################
   # Function that takes new wallets and adds them to the wallet set available
   # to armoryd. Wallet paths are passed in and delineated by colons.
   def jsonrpc_addwallets(self, newWltPaths):
      newWltPaths = newWltPaths.split(":")
      wltPaths = readWalletFiles(newWltPaths)
      addMultWallets(wltPaths, self.serverWltSet, self.serverWltIDSet)

      # TO DO: Return list of wallets added. Mod addMultWallets to return added wallets.


   #############################################################################
   # Function that takes new lockboxes and adds them to the lockbox set
   # available to armoryd. Lockbox paths are passed in and delineated by colons.
   def jsonrpc_addlockboxes(self, newLBPaths):
      newLBPaths = newLBPaths.split(":")
      lbPaths = readWalletFiles(newLBPaths)
      addMultLockboxes(lbPaths, self.serverLBSet, self.serverLBIDSet)

      # TO DO: Return list of lockboxes added. Mod addMultLockboxes to return added lockboxes.


################################################################################
class Armory_Daemon(object):
   def __init__(self, wlt=None, lb=None):
      # NB: These objects contain ONLY wallet/lockbox data loaded at startup.
      # Armory_Json_Rpc_Server will contain the active wallet/LB lists.
      self.wltSet = {}
      self.wltIDSet = set()
      self.lbSet = {}
      self.lbIDSet = set()

      # Check if armoryd is already running, bail if it is
      armorydIsRunning = self.checkForAlreadyRunning()
      if armorydIsRunning == True:
         # Execute the command and return to the command line.
         self.executeCommand()
         os._exit(0)
      else:
         self.lock = threading.Lock()
         self.lastChecked = None

         #check wallet consistency every hour
         self.checkStep = 3600

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

         # Otherwise, set up the server. This includes a defaultdict with a list
         # of functs to execute. This is done so that multiple functs can be
         # associated with the same search key.
         self.newTxFunctions = []
         self.heartbeatFunctions = []
         self.newBlockFunctions = defaultdict(list)

         # The only argument that armoryd.py takes, other than "--testnet" and
         # armoryd commands, is the wallet to load on the server. If no wallets
         # are specified, all wallets in the Armory home directory will be
         # loaded instead.
         if wlt:
            self.curWlt = wlt
         else:
            # Get the wallets in the Armory home directory and store pointers
            # to them if no wallets are specified. Also, set the current
            # wallet to the 1st wallet in the set. (The choice is arbitrary.)
            wltPaths = readWalletFiles()
            addMultWallets(wltPaths, self.wltSet, self.wltIDSet)
            if len(CLI_ARGS)==0:
               if len(self.wltSet) > 0:
                  self.curWlt = self.wltSet[self.wltSet.keys()[0]]

            # Load the specified wallet if it exists.
            else:
               wltpath = CLI_ARGS[0]
               if not os.path.exists(wltpath):
                  LOGERROR('Wallet does not exist!  (%s)', wltpath)
                  return

               self.curWlt = PyBtcWallet().readWalletFile(wltpath)
               self.wltSet[self.curWlt.uniqueIDB58] = self.curWlt
               self.wltIDSet.add(self.curWlt.uniqueIDB58)

         # Let's load all the lockboxes too.
         # NB: For now, lockboxes can't be loaded into armoryd like one can load
         # a wallet. They're loaded to build a base for future features.
         if lb:
            self.curLB = lb
         else:
            lbPaths = getLockboxFilePaths()
            addMultLockboxes(lbPaths, self.lbSet, self.lbIDSet)

         # Log info on the wallets we've loaded.
         numWallets = len(self.wltSet)
         LOGINFO('Number of wallets read in: %d', numWallets)
         for wltID, wlt in self.wltSet.iteritems():
            dispStr  = ('   Wallet (%s):' % wltID).ljust(25)
            dispStr +=  '"'+wlt.labelName.ljust(32)+'"   '
            dispStr +=  '(Encrypted)' if wlt.useEncryption else '(No Encryption)'
            LOGINFO(dispStr)

         # Log info on the lockboxes we've loaded.
         numLockboxes = len(self.lbSet)
         LOGINFO('Number of lockboxes read in: %d', numLockboxes)
         for lockboxID, lockbox in self.lbSet.iteritems():
            dispStr  = ('   Lockbox (%s):' % lockboxID).ljust(25)
            dispStr += '"' + lockbox.shortName.ljust(32) + '"'
            LOGINFO(dispStr)

         # Check and make sure we have at least 1 wallet.
         if numWallets > 0:
            LOGWARN('Active wallet is set to %s' % self.curWlt.uniqueIDB58)
         else:
            LOGWARN('No wallets could be loaded!')
            os._exit(0)

         LOGINFO("Initialising RPC server on port %d", ARMORY_RPC_PORT)
         resource = Armory_Json_Rpc_Server(self.curWlt, self.wltSet, \
                                           self.lbSet, self.wltIDSet, \
                                           self.lbIDSet)
         secured_resource = self.set_auth(resource)

         # This is LISTEN call for armory RPC server
         reactor.listenTCP(ARMORY_RPC_PORT, \
                           server.Site(secured_resource), \
                           interface="127.0.0.1")

         # Setup the heartbeat function to run every 
         reactor.callLater(3, self.Heartbeat)


   #############################################################################
   def set_auth(self, resource):
      passwordfile = ARMORYD_CONF_FILE
      # Create User Name & Password file to use locally
      if not os.path.exists(passwordfile):
         with open(passwordfile,'a') as f:
            # Don't wait for Python or the OS to write the file. Flush buffers.
            genVal = SecureBinaryData().GenerateRandom(32).toBinStr()
            f.write('generated_by_armory:%s' % binary_to_base58(genVal))
            f.flush()
            os.fsync(f.fileno())

      checker = FilePasswordDB(passwordfile)
      realmName = "Armory JSON-RPC App"
      wrapper = wrapResource(resource, [checker], realmName=realmName)
      return wrapper


   #############################################################################
   def start(self):
      #run a wallet consistency check before starting the BDM
      self.checkWallet()
      
      #try to grab checkWallet lock to block start() until the check is over
      self.lock.acquire()
      self.lock.release()

      # This is not a UI so no need to worry about the main thread being
      # blocked. Any UI that uses this Daemon can put the call to the Daemon on
      # its own thread.
      TheBDM.setBlocking(True)
      LOGWARN('Server started...')
      if(not TheBDM.getBDMState()=='Offline'):
         # Put the BDM in online mode only after registering all wallets.
         for wltID, wlt in self.wltSet.iteritems():
            LOGWARN('Registering wallet: %s' % wltID)
            TheBDM.registerWallet(wlt)
         TheBDM.setOnlineMode(True)

         LOGINFO('Blockchain loading')
         while not TheBDM.getBDMState()=='BlockchainReady':
            time.sleep(2)

         self.latestBlockNum = TheBDM.getTopBlockHeight()
         LOGINFO('Blockchain loading finished.  Top block is %d', \
                 TheBDM.getTopBlockHeight())

         mempoolfile = os.path.join(self.armoryHomeDir,'mempool.bin')
         self.checkMemoryPoolCorruption(mempoolfile)
         TheBDM.enableZeroConf(mempoolfile)
         LOGINFO('Syncing wallet: %s' % self.curWlt.uniqueIDB58)
         self.curWlt.syncWithBlockchain()
         LOGINFO('Blockchain load and wallet sync finished')
         LOGINFO('Wallet balance: %s' % coin2str(self.curWlt.getBalance('Spendable')))

         # This is CONNECT call for armoryd to talk to bitcoind
         LOGINFO('Set up connection to bitcoind')
         self.NetworkingFactory = ArmoryClientFactory( \
                        TheBDM,
                        func_loseConnect = self.showOfflineMsg, \
                        func_madeConnect = self.showOnlineMsg, \
                        func_newTx       = self.execOnNewTx, \
                        func_newBlock    = self.execOnNewBlock)
         reactor.connectTCP('127.0.0.1', BITCOIN_PORT, self.NetworkingFactory)
      reactor.run()


   #############################################################################
   @classmethod
   def checkForAlreadyRunning(self):
      retVal = True
      sock = socket.socket()

      # Try to create a connection to the Armory server. If an error is thrown,
      # that means the server doesn't exist.
      try:
         # For now, all we want to do is see if the server exists.
         sock = socket.create_connection(('127.0.0.1',ARMORY_RPC_PORT), 0.1);
      except socket.error:
         LOGINFO('No other armoryd.py instance is running.  We\'re the first.')
         retVal = False

      # Clean up the socket and return the result.
      sock.close()
      return retVal


   #############################################################################
   def executeCommand(self):
      # Open the armoryd.conf config file. At present, it's just a username and
      # password (e.g., "frank:abc123").
      '''
      Function that sets up and executes an armoryd command using JSON-RPC.
      '''
      with open(ARMORYD_CONF_FILE, 'r') as f:
         usr,pwd = f.readline().strip().split(':')

      # If the user gave a command, create a connection to the armoryd server
      # and attempt to execute the command.
      if CLI_ARGS:
         # Make sure the command is lowercase.
         CLI_ARGS[0] = CLI_ARGS[0].lower()

         # Create a proxy pointing to the armoryd server.
         proxyobj = ServiceProxy("http://%s:%s@127.0.0.1:%d" % \
                                 (usr,pwd,ARMORY_RPC_PORT))

         # Let's try to get everything set up for successful command execution.
         try:
            #if not proxyobj.__hasattr__(CLI_ARGS[0]):
               #raise UnrecognizedCommand, 'No json command %s'%CLI_ARGS[0]
            extraArgs = []
            for arg in ([] if len(CLI_ARGS)==1 else CLI_ARGS[1:]):
               # It is possible to pass in JSON-formatted data (e.g.,
               # {"myName":"Terry"}). This isn't smart because no armoryd
               # commands can handle them. But, just in case this changes in the
               # future, we'll decode them anyway and let the functions fail on
               # their own terms. "Normal" args, however, will work for now.
               if arg[0] == '{':
                  # JSON input example:  {"Ages":(10.23, 39.21)}
                  # json.loads() output: {u'Ages', [10.23, 39.21]}
                  extraArgs.append(json.loads(arg))
               else:
                  extraArgs.append(arg)

            # Just in case we wish to give the user any info/warnings before the
            # command is executed, do it here.
            emailWarning = 'WARNING: For now, the password for your e-mail ' \
                           'account will sit in memory and in your shell ' \
                           'history. We highly recommend that you use a ' \
                           'disposable account which may be compromised ' \
                           'without exposing sensitive information.'
            if CLI_ARGS[0] == 'watchwallet' or CLI_ARGS[0] == 'sendlockbox':
               print emailWarning

            # Call the user's command (e.g., "getbalance full" ->
            # jsonrpc_getbalance(full)) and print results.
            result = proxyobj.__getattr__(CLI_ARGS[0])(*extraArgs)
            print json.dumps(result, indent=4, sort_keys=True, \
                             cls=UniversalEncoder)

         except Exception as e:
            # The command was bad. Print a message.
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


   #############################################################################
   def execOnNewTx(self, pytxObj):
      # Gotta do this on every new Tx
      TheBDM.addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True)
      TheBDM.rescanWalletZeroConf(self.curWlt.cppWallet)

      # Add anything else you'd like to do on a new transaction
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
   @AllowAsync
   def checkWallet(self):
      if self.lock.acquire(False):
         wltStatus = PyBtcWalletRecovery().ProcessWallet(None, self.curWlt, \
                                                         Mode=5)
         if wltStatus != 0:
            print 'Wallet consistency check failed in wallet %s!!!' \
                   % (self.curWlt.uniqueIDB58)
            print 'Aborting...'

            quit()
         else:
            self.lastChecked = RightNow()

      self.lock.release()


   #############################################################################
   def Heartbeat(self, nextBeatSec=1):
      """
      This method is invoked when the app is initialized, and will
      run every 2 seconds, or whatever is specified in the nextBeatSec
      argument.
      """
      # Check for new blocks in the latest blk0XXXX.dat file.
      if TheBDM.getBDMState()=='BlockchainReady':
         #check wallet every checkStep seconds
         nextCheck = self.lastChecked + self.checkStep
         if RightNow() >= nextCheck:
            self.checkWallet()

         # Check for new blocks in the blk000X.dat file
         prevTopBlock = TheBDM.getTopBlockHeight()
         newBlks = TheBDM.readBlkFileUpdate()
         if newBlks>0:
            self.latestBlockNum = TheBDM.getTopBlockHeight()
            self.topTimestamp   = TheBDM.getTopBlockHeader().getTimestamp()

            self.curWlt.syncWithBlockchain()
            TheBDM.rescanWalletZeroConf(self.curWlt.cppWallet)

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
                  pyHeader = PyBlockHeader().unserialize(cppHeader.serialize())
                  
                  cppBlock = TheBDM.getMainBlockFromDB(blknum)
                  pyTxList = [PyTx().unserialize(cppBlock.getSerializedTx(i)) for
                                 i in range(cppBlock.getNumTx())]
                  for funcKey in self.newBlockFunctions:
                     for blockFunc in self.newBlockFunctions[funcKey]:
                        blockFunc(pyHeader, pyTxList)

      self.curWlt.checkWalletLockTimeout()
      reactor.callLater(nextBeatSec, self.Heartbeat)


if __name__ == "__main__":
   rpc_server = Armory_Daemon()
   rpc_server.start()
