################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
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
# provided immense amounts of help with this. This app is mostly _chunks
# of code taken from armory and refurbished into an rpc client.
# See the bitcontalk thread for more details about this software:
# https://bitcointalk.org/index.php?topic=92496.0
#####

################################################################################
# To assist users, they can access, via JSON, a dictionary with information on
# all the functions available via JSON. The dictionary will use the funct name
# as the key and another dictionary as the value. The resultant dict will have a
# description (string), a list of strings with parameter info, and the return
# value (string). The following example provides a visual guide.
#
# {
#  "functA" : {
#              "Description" : "A funct that does a thing. This has mult lines."
#              "Parameters" : [
#                              "paramA - Descrip of paramA. Mult lines exist."
#                              "paramB - A random string."
#                             ]
#              "Return Value" : "Description of the return value. Mult lines!"
# }
#
# Devs will have to remember to add the doc string when new functs are added. In
# addition, devs will have to remember to use the following format for the
# docstring, lest they risk screwing up the resultant dictionary or being unable
# to run armoryd. Note that parameters must have a single dash separating them,
# along with a single space before and after the dash!
#
# DESCRIPTION:
# A funct that does a thing.
# This has mult lines.
# PARAMETERS:
# paramA - Descrip of paramA.
#          Mult lines exist.
# paramB - A random string.
# RETURN:
# Description of the return value.
# Mult lines!
################################################################################

################################################################################
#
# Random JSON notes should be placed here as desired.
#
# - If a returned string has a newline char, JSON will convert it to the string
#   "\n" (minus quotation marks).
# - In general, if you need to pass an actual newline via the command line, type
#   $'\n' instead of \n or \\n. (Newlines in files can be left alone.)
# - The code sometimes returns "bitcoinrpc_jsonrpc.authproxy.JSONRPCException"
#   if values are returned as binary data. This is something to keep in mind if
#   bugs occur.
# - When all else fails, and you have no clue how to deal via JSON, read RFC
#   4627 and/or the Python manual's section on JSON.
#
################################################################################

import base64
import inspect
import sys
import getdns

from collections import defaultdict

from twisted.cred.checkers import FilePasswordDB
from twisted.internet import reactor
from twisted.web import server

from txjsonrpc.auth import wrapResource
from txjsonrpc.web import jsonrpc

from armoryengine.ALL import *
from armoryengine.Decorators import EmailOutput, catchErrsForJSON
from armoryengine.ArmorySettings import SettingsFile
from dnssec_dane.daneHandler import getDANERecord


class ArmoryRPC(jsonrpc.JSONRPC):

   #############################################################################
   def __init__(self, wallet, lockbox=None, inWltMap=None, inLBMap=None,
                inLBCppWalletMap=None, armoryHomeDir=None,
                addrByte=None):
      # Save the incoming info. If the user didn't pass in a wallet set, put the
      # wallet in the set (actually a dictionary w/ the wallet ID as the key).
      self.addressMetaData = {}
      self.curWlt = wallet
      self.curLB = lockbox

      # Dicts, sets and lists (and other container types?), if used as a default
      # argument, actually become references and subsequent calls to __init__
      # will not necessarily be empty objects/maps. The proper way to initialize
      # is to check for None and set to the proper type.
      if inWltMap == None:
         inWltMap = {}
      if inLBMap == None:
         inLBMap = {}
      if inLBCppWalletMap == None:
         inLBCppWalletMap = {}
      self.serverWltMap = inWltMap                 # Dict
      self.serverLBMap = inLBMap                   # Dict
      self.serverLBCppWalletMap = inLBCppWalletMap # Dict

      self.armoryHomeDir = armoryHomeDir or getArmoryHomeDir()
      if wallet is not None:
         wltID = wallet.uniqueIDB58
         if self.serverWltMap.get(wltID) is None:
            self.serverWltMap[wltID] = wallet

      # If any variables rely on whether or not Testnet in a Box is running,
      # we'll set everything up here.
      self.addrByte = addrByte or getAddrByte()

      # connection to bitcoind
      self.NetworkingFactory = None


   #############################################################################
   def checkBDM(self):
      if getBDM().getState() != BDM_BLOCKCHAIN_READY:
         raise BlockchainNotReady('Wallet is not loaded yet. Currently %s'
                                  % getBDM().getState())

   #############################################################################
   # Utility function that takes an email address, gets a PMTA record based on
   # the address, and returns the address found within.
   @catchErrsForJSON
   def jsonrpc_getdanerecfromdns(self, inAddr):
      """
      DESCRIPTION:
      Function that gets a BTCA record from DNS. Prototype.
      PARAMETRS:
      inAddr - Email address with a record in DNS.
      RETURN:
      A string with the Bitcoin address associated with the email address.
      """
      # Code basically stolen from wallet2.0-dns:dnssec_dane/getDANERec.py and
      # then slightly enhanced. This WILL require more work later!

      # For now, assume record name is an email address. Use the SMIME record format,
      # where the username is hashed using SHA224. Also, assume domain is searched.
      retDict = {}
      userAddr = ''
      recordUser, recordDomain = inAddr.split('@', 1)
      sha224Res = sha224(recordUser)
      daneReqName = binary_to_hex(sha224Res) + '._pmta.' + recordDomain

      # Go out and get the DANE record.
      pmtaRecType, daneRec = getDANERecord(daneReqName)
      if pmtaRecType == BTCAID_PAYLOAD_TYPE.PublicKeySource:
         # HACK HACK HACK: Just assume we have a PKS record that is static and
         # has a Hash160 value.
         pksRec = PublicKeySource().unserialize(daneRec)

         # Convert Hash160 to Bitcoin address.
         if daneRec != None:
            userAddr = hash160_to_addrStr(pksRec.rawSource, ADDRBYTE)

      else:
         raise InvalidDANESearchParam(inAddr + " has no DANE record")

      retDict['BTC Address'] = userAddr
      return retDict


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getreceivedfromsigner(self, *sigBlock):
      """
      DESCRIPTION:
      Verify that a message (RFC 2440: clearsign or Base64) has been signed by
      a Bitcoin address and get the amount of coins sent to the current wallet
      by the message's signer.
      PARAMETERS:
      sigBlock - Message with the RFC 2440 message to be verified. The message
                 must be enclosed in quotation marks.
      RETURN:
      A dictionary with verified message and the amount of money sent to the
      current wallet by the signer.
      """
      retDict = {}

      # We must deal with a quirk. Non-escaped spaces (i.e., spaces that aren't
      # \u0020) will cause the CL parser to split the sig into multiple lines.
      # We need to combine the lines. (NB: Strip the final space too!)
      signedMsg = (''.join((str(piece) + ' ') for piece in sigBlock))[:-1]


   #############################################################################
   def checkUnlock(self):
      if self.curWlt.useEncryption() and self.curWlt.isLocked():
         raise WalletUnlockNeeded("Wallet needs to be unlocked first")


   #############################################################################
   # Helper funct that converts the lockbox dict into a list.
   def convLBDictToList(self):
      retList = []

      for lb in self.serverLBMap.values():
         retList.append(lb)

      return retList


   #############################################################################
   # Function that takes a paired list of recipients and the amount to be sent
   # to them, and creates an unsigned transaction based on the current wallet.
   # The ASCII version of the transaction is sent back.
   # https://bitcointalk.org/index.php?topic=92496.msg1126310#msg1126310
   # contains out-of-date notes regarding how the code works. A slightly more
   # up-to-date comparison can be made against the code in
   # SendBitcoinsFrame::validateInputsGetUSTX() (ui/TxFrames.py).
   def createUSTX(self, scriptValuePairs,
                                   spendFromLboxID=None, wantfee=None):
      # Do initial setup, including choosing the coins you'll use.
      totalSend = long( sum([rv[1] for rv in scriptValuePairs]) )
      if wantfee is None:
         fee = 0
      else:
         fee = wantfee

      if totalSend + fee <= 0:
         raise InvalidTransaction("You are not spending any coins. Not a "
                                  "valid transaction")

      lbox = None
      if spendFromLboxID is None:
         spendBal = self.curWlt.getBalance('Spendable')
         utxoList = self.curWlt.getUTXOListForSpendVal(totalSend)
      else:
         lbox = self.serverLBMap[spendFromLboxID]
         cppWlt = self.serverLBCppWalletMap[spendFromLboxID]
         topBlk = getBDM().getTopBlockHeight()
         spendBal = cppWlt.getSpendableBalance(topBlk, getIgnoreZCFlag())
         utxoList = cppWlt.getSpendableTxOutListForValue(totalSend, getIgnoreZCFlag())

      if spendBal < totalSend + fee:
         raise NotEnoughCoinsError(
            "You have %s satoshis which is not enough to send %s satoshis with "
            "a fee of %s." % (spendBal, totalSend, fee))

      utxoSelect = PySelectCoins(utxoList, totalSend, fee)

      # Calculate the real fee and make sure it's affordable.
      # ACR: created new, more flexible fee-calc function.  Perhaps there's an
      #      opportunity to retro-fit this to other places we calc the min fee.
      #      Keep in mind it relies on having the UTXO script available... the
      #      fact that PyUnspentTxOut doesn't requrie that field should probably
      #      be fixed, but at the moment every code path going into it does set
      #      that member.
      minFeeRec = calcMinSuggestedFeesNew(utxoSelect, scriptValuePairs, fee)[1]

      if fee < minFeeRec:
         if wantfee:
            raise NotEnoughCoinsError(
               "A fee of %s is necessary for this transaction to go through. "
               "You put %s as the fee."  % (minFeeRec, fee))
         if (totalSend + minFeeRec) > spendBal:
            raise NotEnoughCoinsError("You can't afford the fee!")
         utxoSelect = PySelectCoins(utxoList, totalSend, minFeeRec)
         fee = minFeeRec

      # If we have no coins, bail out.
      if len(utxoSelect)==0:
         raise CoinSelectError("Coin selection failed. This shouldn't happen.")

      # Calculate the change.
      totalSelected = sum([u.getValue() for u in utxoSelect])
      totalChange = totalSelected - (totalSend  + fee)

      # Generate and shuffle the recipient list.
      outputPairs = scriptValuePairs[:]
      if lbox:
         p2shMap = {binary_to_hex(script_to_scrAddr(script_to_p2sh_script(
            lbox.binScript))) : lbox.binScript}
      else:
         p2shMap = {}
      if totalChange > 0:
         if spendFromLboxID is None:
            nextAddr = self.curWlt.getNextChangeAddress().getAddrStr()
            ustxScr = getScriptForUserString(nextAddr, self.serverWltMap,
                                             self.convLBDictToList())
            outputPairs.append( [ustxScr['Script'], totalChange] )
         else:
            outputPairs.append( [lbox.binScript, totalChange] )

      # change tx ordering for security
      reorderInputsAndOutputs(utxoSelect, outputPairs)

      # If this has nothing to do with lockboxes, we need to make sure
      # we're providing a key map for the inputs.
      pubKeyMap = {}
      for utxo in utxoSelect:
         scrType = getTxOutScriptType(utxo.getScript())
         if scrType in CPP_TXOUT_STDSINGLESIG:
            scrAddr = utxo.getRecipientScrAddr()
            addrObj = self.curWlt.getAddress(scrAddr)
            if addrObj:
               pubKeyMap[scrAddr] = addrObj.getSerializedPubKey()

      # Create an unsigned transaction and return the ASCII version.
      usTx = UnsignedTransaction().createFromTxOutSelection(
         utxoSelect, outputPairs, pubKeyMap, p2shMap=p2shMap)
      return usTx.serializeAscii()


   #############################################################################
   def getLockboxBalance(self, idB58, baltype="spendable"):
      # Proceed only if the blockchain's good. Wallet value could be unreliable
      # otherwise.
      self.checkBDM()
      cppWallet = self.serverLBCppWalletMap.get(idB58)
      if cppWallet is None:
         raise LockboxDoesNotExist("Lockbox does not exist")
      topBlockHeight = getBDM().getTopBlockHeight()
      bal = -1
      if baltype.lower() in ('spendable','spend'):
         bal = cppWallet.getSpendableBalance(topBlockHeight, getIgnoreZCFlag())
      elif baltype.lower() in ('unconfirmed','unconf'):
         bal = cppWallet.getUnconfirmedBalance(topBlockHeight, getIgnoreZCFlag())
      elif baltype.lower() in ('total','ultimate','unspent','full'):
         bal = cppWallet.getFullBalance()
      else:
         raise TypeError('Unknown balance type! "' + baltype + '"')
      return AmountToJSON(bal)


   #############################################################################
   # Get the lock box ID if the p2shAddrString is found in one of the lockboxes
   # otherwise it returns None
   def getLockboxByP2SHAddrStr(self, p2shAddrStr):
      for lboxId,lbox in self.serverLBMap.iteritems():
         if p2shAddrStr == binScript_to_p2shAddrStr(lbox.binScript):
            return lbox
      return None


   #############################################################################
   @catchErrsForJSON
   def getScriptAddrStrs(self, txOut):
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
   def getUtxoInfo(self, utxoList):
      infoList = []
      curTxOut = 0
      for u in utxoList:
         curTxOut += 1
         curUTXODict = {}

         curTxOutStr = 'utxo%05d' % curTxOut
         utxoVal = AmountToJSON(u.getValue())
         curUTXODict['txid'] = binary_to_hex(u.getOutPoint().getTxHash(),
                                             BIGENDIAN, LITTLEENDIAN)
         curUTXODict['vout'] = u.getTxOutIndex()
         try:
            curUTXODict['address']  = script_to_addrStr(u.getScript())
         except:
            LOGEXCEPT('Error parse UTXO script -- multisig or non-standard')
            curUTXODict['address']  = ''
         curUTXODict['scriptPubKey'] = binary_to_hex(u.getScript())
         curUTXODict['amount'] = utxoVal
         curUTXODict['confirmations'] = u.getNumConfirm()
         curUTXODict['priority'] = utxoVal * u.getNumConfirm()

         infoList.append(curUTXODict)
      return infoList


   #############################################################################
   # JSON-RPC functions
   # NOTE THAT THESE ARE IN ALPHABETICAL ORDER.
   # PLEASE KEEP THEM THAT WAY.
   #############################################################################


   #############################################################################
   # backupFilePath is the file to backup the current wallet to.
   # It does not necessarily exist yet.
   @catchErrsForJSON
   def jsonrpc_backupwallet(self, backupFilePath):
      """
      DESCRIPTION:
      Back up the current wallet to a file at a given location. The backup will
      occur only if the file does not exist yet.
      PARAMETERS:
      backupFilePath - Path to the location where the backup will be saved.
      RETURN:
      A dictionary indicating whether or not the backup succeeded or failed,
      with the reason for failure given if applicable.
      """

      retVal = {}
      if os.path.isfile(backupFilePath):
         raise FileExists('File %s already exists. Will not overwrite.' %
                          backupFilePath)
      else:
          if not self.curWlt.wltFileRef.backupWalletFile(backupFilePath):
             # If we have a failure here, we probably won't know why. Not much
             # to do other than ask the user to check the armoryd server.
             raise BackupFailed("Backup failed. Check the logs.")
          else:
             retVal['Result'] = "Backup succeeded."

      return retVal


   #############################################################################
   # Clear the metadata.
   @catchErrsForJSON
   def jsonrpc_clearaddressmetadata(self):
      """
      DESCRIPTION:
      Clear all armoryd-specific metadata for the currently loaded wallet.
      PARAMETERS:
      None
      RETURN:
      None
      """

      self.addressMetaData = {}


   #############################################################################
   # Create a multisig lockbox. The user must specify the number of keys needed
   # to unlock a lockbox, the number of keys in a lockbox, and the exact keys or
   # wallets to use. If wallets are specified, an address will be chosen from
   # the wallet. If public keys are specified, the keys must be uncompressed.
   # (For now, compressed keys aren't supported.)
   #
   # Example: We wish to create a 2-of-3 lockbox based on 2 loaded wallets
   # (27TchD13 and AaAaaAQ4) and an uncompressed public key. The following
   # command would be executed.
   # armoryd createlockbox 2 3 27TchD13 AaAaaAQ4 04010203040506070809....
   @catchErrsForJSON
   def jsonrpc_createlockbox(self, numM, numN, *args):
      """
      DESCRIPTION:
      Create an m-of-n lockbox associated with wallets loaded onto the
      armoryd server.
      PARAMETERS:
      numM - The number of signatures required to spend lockbox funds.
      numN - The total number of signatures associated with a lockbox.
      args - The wallets or public keys associated with a lockbox, the total of
             which must match <numN> in number. The wallets are represented by
             their Base58 IDs. The keys must be uncompressed.
      RETURN:
      A dictionary with information about the new lockbox.
      """

      m = int(numM)
      n = int(numN)
      errStr = ''
      result = {}

      # Do some basic error checking before proceeding.
      if m > n:
         errStr = 'The user requires more keys or wallets to unlock a ' \
                  'lockbox (%d) than are required to create a lockbox (%d).' % \
                  (m, n)
         LOGERROR(errStr)
         raise InvalidRequest(errStr)
      elif m > LB_MAXM:
         errStr = 'The number of signatures required to unlock a lockbox ' \
                  '(%d) exceeds the maximum allowed (%d)' % (m, LB_MAXM)
         LOGERROR(errStr)
         raise InvalidRequest(errStr)
      elif n > LB_MAXN:
         errStr = 'The number of keys or wallets required to create a ' \
                  'lockbox (%d) exceeds the maximum allowed (%d)' % (n, LB_MAXN)
         LOGERROR(errStr)
         raise InvalidRequest(errStr)
      elif not args:
         errStr = 'No keys or wallets were specified. %d wallets or keys are ' \
                  'required to create the lockbox.' % n
         LOGERROR(errStr)
         raise InvalidRequest(errStr)
      elif len(args) > n:
         errStr = 'The number of supplied keys or wallets (%d) exceeds the ' \
                  'number required to create the lockbox (%d)' % (len(args), n)
         LOGERROR(errStr)
         raise InvalidRequest(errStr)
      elif len(args) < n:
         errStr = 'The number of supplied keys or wallets (%d) is less than ' \
                  'the number of required to create the lockbox (%d)' % \
                  (len(args), n)
         LOGERROR(errStr)
         raise InvalidRequest(errStr)
      else:
         allArgsValid = True
         badArg = ''
         addrList = [] # Starts as string list, eventually becomes binary.
         addrNameList = [] # String list
         lockboxPubKeyList = []

         # We need to determine which args are keys, which are wallets and which
         # are garbage.
         for lockboxItem in args:
            # First, check if the arg is a wallet ID. If not, check if it's a
            # valid pub key. If not, the input's invalid.
            try:
               # If search item's a pub key, it'll cause a KeyError to be
               # thrown. That's fine. We can catch it and keep on truckin'.
               lbWlt = self.serverWltMap[lockboxItem]
               pubkey = lbWlt.getNextReceivingAddress().getSerializedPubKey('hex')
               addrList.append(pubkey)
               addrName = 'Public key %d from wallet %s' % (
                  lbWlt.external.getChildIndex(), lockboxItem)
               addrNameList.append(addrName)

            except KeyError:
               # A screwy wallet ID will cause a TypeError if we check to see if
               # it's a pub key. Let's catch it.
               try:
                  # A pub key could be fake but in the proper form, so we
                  # have a second place where a value can fail. Catch it.
                  if isValidPK(lockboxItem, True):
                     # Make sure we're using an uncompressed or compressed key
                     # before processing it.
                     addrList.append(lockboxItem)
                     addrName = 'Public key %s' % lockboxItem
                     addrNameList.append(addrName)
                  else:
                     badArg = lockboxItem
                     allArgsValid = False
                     break

               except TypeError:
                  badArg = lockboxItem
                  allArgsValid = False
                  break

         # Do some basic error checking before proceeding.
         if allArgsValid == False:
            errStr = 'The user has specified an argument (%s) that is ' \
                     'invalid.' % badArg
            LOGERROR(errStr)
            raise InvalidRequest(errStr)
         else:
            # We must sort the addresses and comments together. It's important
            # to keep this code in sync with any other code creating lockboxes.
            # Also, convert the key list from hex to binary to support multisig
            # conversion while also minimizing coding.
            decorated  = [[pk,comm] for pk,comm in zip(addrList,
                                                       addrNameList)]
            decorSort  = sorted(decorated, key=lambda pair: pair[0])
            for i, pair in enumerate(decorSort):
               lockboxPubKeyList.append(DecoratedPublicKey(hex_to_binary(pair[0])))
               addrList[i]     = hex_to_binary(pair[0])
               addrNameList[i] = pair[1]

            # Let the lockbox creation begin! We'll write it to the wallet and
            # return the hex representation via JSON.
            pkListScript = pubkeylist_to_multisig_script(addrList, m)
            lbID = calcLockboxID(pkListScript)
            lbCreateDate = long(time.time())
            lbName = 'Lockbox %s' % lbID
            lbDescrip = '%s - %d-of-%d - Created by armoryd' % (lbID, m, n)
            lockbox = MultiSigLockbox(lbName, lbDescrip, m, n,
                                      lockboxPubKeyList, lbCreateDate)

            # To be safe, we'll write the LB only if Armory doesn't already have
            # a copy.
            if lbID in self.serverLBMap.keys():
               errStr = 'Lockbox %s already exists.' % lbID
               LOGERROR(errStr)
               raise InvalidRequest(errStr)
            else:
               # Write to the current wallet file
               # and load the LB into our LB set.
               lockbox.copyFromWE(self.curWlt)
               lockbox.wltFileRef.addEntriesToWallet([lockbox])
               self.serverLBMap[lbID] = lockbox
               scraddrReg = script_to_scrAddr(lockbox.binScript)
               scraddrP2SH = script_to_scrAddr(script_to_p2sh_script(lockbox.binScript))
               scrAddrList = [scraddrReg, scraddrP2SH]
               LOGINFO("registering lockbox: %s" % lbID)
               LOGINFO("lockbox addrs: %s" % scrAddrList)
               self.serverLBCppWalletMap[lbID] = lockbox.registerLockbox(scrAddrList, True)
               result = lockbox.toJSONMap()

      return result


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_createlockboxustxformany(self, fee, *args):
      """
      DESCRIPTION:
      Create an unsigned transaction to be sent to multiple recipients from
      the currently loaded lockbox.
      PARAMETERS:
      fee - Amount you want to pay in transaction fees. Put 0 to make the
            fee the minimum amount for the tx to go through
      args - An indefinite number of comma-separated sets of recipients and the
             number of Bitcoins to send to the recipients. The recipients can be
             an address, a P2SH script address, a lockbox (e.g.,
             "Lockbox[83jcAqz9]" or "Lockbox[Bare:83jcAqz9]"), or a public key
             (compressed or uncompressed) string.
      RETURN:
      An ASCII-formatted unsigned transaction, similar to the one output by
      Armory for offline signing.
      """

      self.checkBDM()

      if fee is not None:
         fee = JSONtoAmount(fee)

      if fee == 0:
         fee = None

      scriptValuePairs = []
      for a in args:
         r,v = a.split(',')
         ustxScr = getScriptForUserString(r, self.serverWltMap,
                                          self.convLBDictToList())
         scriptValuePairs.append([ustxScr['Script'], JSONtoAmount(v)])

      return self.createUSTX(
         scriptValuePairs, self.curLB.uniqueIDB58, fee)


   #############################################################################
   # Create an unsigned Tx to be sent from the currently loaded wallet.
   #
   # Example: We wish to send 1 BTC to a lockbox and 0.12 BTC to a standard
   # Bitcoin address. (Publick keys and P2SH scripts can also be specified as
   # recipients but we don't use either one in this example.)
   # armoryd createustxformany Lockbox[83jcAqz9],1.0 mwpw68XWmvQKfsCJXETkDX2CWHPdchY6fi,0.12
   @catchErrsForJSON
   def jsonrpc_createustxformany(self, fee, *args):
      """
      DESCRIPTION:
      Create an unsigned transaction to be sent to multiple recipients from
      the currently loaded wallet.
      PARAMETERS:
      fee - Amount you want to pay in transaction fees. Put 0 to make the
            fee the minimum amount for the tx to go through
      args - An indefinite number of comma-separated sets of recipients and the
             number of Bitcoins to send to the recipients. The recipients can be
             an address, a P2SH script address, a lockbox (e.g.,
             "Lockbox[83jcAqz9]" or "Lockbox[Bare:83jcAqz9]"), or a public key
             (compressed or uncompressed) string.
      RETURN:
      An ASCII-formatted unsigned transaction, similar to the one output by
      Armory for offline signing.
      """

      self.checkBDM()

      if fee is not None:
         fee = JSONtoAmount(fee)

      if fee == 0:
         fee = None

      scriptValuePairs = []
      for a in args:
         r,v = a.split(',')
         ustxScr = getScriptForUserString(r, self.serverWltMap,
                                          self.convLBDictToList())
         scriptValuePairs.append([ustxScr['Script'], JSONtoAmount(v)])

      return self.createUSTX(scriptValuePairs, wantfee=fee)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_createlockboxustxtoaddress(self, recAddr, amount, fee=None):
      """
      DESCRIPTION:
      Create an unsigned transaction to be sent to one recipient from the
      currently loaded lockbox.
      PARAMETERS:
      recAddr - The recipient. This can be an address, a P2SH script address, a
                lockbox (e.g., "Lockbox[83jcAqz9]" or "Lockbox[Bare:83jcAqz9]"),
                or a public key (compressed or uncompressed) string.
      amount - The number of Bitcoins to send to the recipient.
      fee - Amount you want to pay in transaction fees.
      RETURN:
      An ASCII-formatted unsigned transaction, similar to the one output by
      Armory for offline signing.
      """

      self.checkBDM()
      ustxScr = getScriptForUserString(recAddr, self.serverWltMap,
                                       self.convLBDictToList())
      amtCoin = JSONtoAmount(amount)
      if fee is not None:
         fee = JSONtoAmount(fee)
      return self.createUSTX(
         [[str(ustxScr['Script']), amtCoin]], self.curLB.uniqueIDB58, fee)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_createustxtoaddress(self, recAddr, amount, fee=None):
      """
      DESCRIPTION:
      Create an unsigned transaction to be sent to one recipient from the
      currently loaded wallet.
      PARAMETERS:
      recAddr - The recipient. This can be an address, a P2SH script address, a
                lockbox (e.g., "Lockbox[83jcAqz9]" or "Lockbox[Bare:83jcAqz9]"),
                or a public key (compressed or uncompressed) string.
      amount - The number of Bitcoins to send to the recipient.
      fee - Amount you want to pay in transaction fees.
      RETURN:
      An ASCII-formatted unsigned transaction, similar to the one output by
      Armory for offline signing.
      """

      self.checkBDM()
      ustxScr = getScriptForUserString(recAddr, self.serverWltMap,
                                       self.convLBDictToList())
      amtCoin = JSONtoAmount(amount)
      if fee is not None:
         fee = JSONtoAmount(fee)
      return self.createUSTX([[str(ustxScr['Script']),
                                                amtCoin]], wantfee=fee)


   #############################################################################
   # Function that creates a ABEK_STDWALLET in the current wallet file
   @catchErrsForJSON
   def jsonrpc_createwallet(self, name, description):
      """
      DESCRIPTION:
      Create a new wallet within the current file.
      PARAMETERS:
      name - A human-readable name for the wallet
      description - A human-readable description for the wallet
      RETURN:
      A b58ID of the wallet.
      """
      self.checkUnlock()

      wallet = self.curWlt.getRoot().createNewWallet(name, description)
      wltID = wallet.uniqueIDB58
      self.serverWltMap[wltID] = wallet
      wallet.registerWallet()
      return wallet.uniqueIDB58


   #############################################################################
   # Function that creates a new 2.0 wallet file
   @catchErrsForJSON
   def jsonrpc_createwalletfile(self, name, passphrase):
      """
      DESCRIPTION:
      Create a new 2.0 wallet file.
      PARAMETERS:
      name - A human-readable name for the first wallet (auto-created)
             in the file
      passphrase - The passphrase that unlocks this wallet file. Use an
             empty string for an unencrypted wallet.
      RETURN:
      A b58ID of the first wallet.
      """
      entropy = SecureBinaryData().GenerateRandom(32)

      if passphrase == '':
         walletFile = ArmoryWalletFile.CreateWalletFile_NewRoot(
            name, ABEK_BIP44Seed, entropy, None, NULLCRYPTINFO(), None, None)
      else:
         pwd = SecureBinaryData(str(passphrase))
         walletFile = ArmoryWalletFile.CreateWalletFile_SinglePwd(
            name, pwd, sbdExtraEntropy=entropy)

      root = walletFile.topLevelRoots[0]

      # only one wallet gets created, so return the id of that
      wallet = root.getAllWallets()[0]
      wallet.setLabel(name, fsync=False)
      wallet.fillKeyPool(fsync=False)
      wallet.wltFileRef.fsyncUpdates()
      wltID = wallet.uniqueIDB58
      LOGINFO("loading %s" % wltID)
      self.serverWltMap[wltID] = wallet
      return wallet.uniqueIDB58


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_decoderawtransaction(self, hexString):
      """
      DESCRIPTION:
      Decode a raw transaction hex string.
      PARAMETERS:
      hexString - A string representing, in hex form, a raw transaction.
      RETURN:
      A dictionary containing the decoded transaction's information.
      """

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

         if scrType == CPP_TXIN_COINBASE:
            vinList.append( {  'coinbase'  : binary_to_hex(txin.binScript),
                               'sequence'  : txin.intSeq })
         else:
            vinList.append(  { 'txid'      : binary_to_hex(prevHash, BIGENDIAN),
                               'vout'      : txin.outpoint.txOutIndex,
                               'scriptSig' : scriptSigDict,
                               'sequence'  : txin.intSeq})

      #####
      # Accumulate TxOut info
      voutList = []
      for n,txout in enumerate(pyTx.outputs):
         voutList.append( { 'value' : AmountToJSON(txout.value),
                            'n' : n,
                            'scriptPubKey' : self.getScriptAddrStrs(txout) } )


      #####
      # Accumulate all the data to return
      result = { 'txid'     : pyTx.getHashHex(BIGENDIAN),
                 'version'  : pyTx.version,
                 'locktime' : pyTx.lockTime,
                 'vin'      : vinList,
                 'vout'     : voutList }

      return result


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_dumpprivkey(self, addr58, keyFormat='Base58'):
      """
      DESCRIPTION:
      Dump the private key for a given Base58 address associated with the
      currently loaded wallet.
      PARAMETERS:
      addr58 - A Base58 public address associated with the current wallet.
      keyFormat - (Default=Base58) The desired format of the output. "Base58"
                  and "Hex" are the available formats.
      RETURN:
      The 32 byte private key, encoded as requested by the user.
      """

      # Cannot dump the private key for a locked wallet
      self.checkUnlock()

      # The first byte must be the correct net byte, and the
      # last 4 bytes must be the correct checksum
      if not checkAddrStrValid(addr58):
         raise InvalidBitcoinAddress

      scrAddr = addrStr_to_scrAddr(addr58)
      address = self.curWlt.getAddress(scrAddr)
      if address is None:
         raise PrivateKeyNotFound("address %s not found in wallet" % addr58)
      return address.getSerializedPrivKey(keyFormat)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_encryptwalletfile(self, oldPassphrase, newPassphrase):
      """
      DESCRIPTION:
      Encrypt the wallet file with a new passphrase.
      PARAMETERS:
      oldPassphrase - The wallet file's old passphrase. Use an empty string if
                      the wallet has no encryption.
      newPassphrase - The wallet file's new passphrase. Use an empty string to
                      remove encryption.
      RETURN:
      A string indicating that the encryption was successful.
      """

      if self.curWlt.isWatchOnly:
         raise WalletUpdateError("This is a watch-only wallet, you cannot"
                                 " encrypt watch-only wallets.")

      if oldPassphrase == newPassphrase:
         raise PassphraseError("The old and new passphrases are the same!")

      wltID = self.curWlt.getUniqueIDB58()

      if oldPassphrase == '':
         if self.curWlt.useEncryption():
            raise PassphraseError("Wrong passphrase given")
         # encrypt the wallet
         sbdPassphrase = SecureBinaryData(str(newPassphrase))
         cryptInfo, masterKey = ArmoryWalletFile.generateNewSinglePwdMasterEKey(
            sbdPassphrase)
         wltFile = self.curWlt.wltFileRef
         wltFile.addCryptObjsToWallet(masterKey)
         root = self.curWlt.getRoot()
         masterKey.unlock(sbdPassphrase)
         root.changeCryptInfo(cryptInfo, masterKey)
         wltFile.fsyncUpdates()
         sbdPassphrase.destroy()
         self.curWlt.lock()
         return 'Wallet %s has been encrypted.' % wltID
      elif newPassphrase == '':
         # decrypt the wallet
         oldPassphrase = SecureBinaryData(str(oldPassphrase))
         self.curWlt.unlock(oldPassphrase)
         wltFile = self.curWlt.wltFileRef
         wltFile.addFileOperationToQueue('DeleteEntry',
                                         self.curWlt.masterEkeyRef)
         root = self.curWlt.getRoot()
         root.changeCryptInfo(None, None)
         wltFile.fsyncUpdates()
         oldPassphrase.destroy()
         return 'Wallet %s has been decrypted.' % wltID
      else:
         # encrypt the wallet with a different passphrase
         sbdPassphrase = SecureBinaryData(str(newPassphrase))
         oldPassphrase = SecureBinaryData(str(oldPassphrase))
         self.curWlt.masterEkeyRef.changeEncryptionParams(
            oldPassphrase, sbdPassphrase)
         self.curWlt.wltFileRef.fsyncUpdates()
         self.curWlt.lock()
         sbdPassphrase.destroy()
         oldPassphrase.destroy()
         return 'Wallet %s has been encrypted with the new passphrase' % wltID


   #############################################################################
   # Function that gets the B58 string of the currently active lockbox.
   @catchErrsForJSON
   def jsonrpc_getactivelockbox(self):
      """
      DESCRIPTION:
      Get the lockbox ID of the currently active lockbox.
      PARAMETERS:
      None
      RETURN:
      The Base58 ID for the currently active lockbox.
      """

      # Return the B58 string of the currently active lockbox.
      return self.curLB.uniqueIDB58 if self.curLB else None


   #############################################################################
   # Function that gets the B58 string of the currently active wallet.
   @catchErrsForJSON
   def jsonrpc_getactivewallet(self):
      """
      DESCRIPTION:
      Get the wallet ID of the currently active wallet.
      PARAMETERS:
      None
      RETURN:
      The Base58 ID for the currently active wallet.
      """

      # Return the B58 string of the currently active wallet.
      return self.curWlt.uniqueIDB58 if self.curWlt else None


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getaddrbalance(self, inB58, baltype='spendable'):
      """
      DESCRIPTION:
      Get the balance of a Base58 address associated with the currently
      loaded wallet.
      PARAMETERS:
      inB58 - The Base58 address associated with the current wallet.
      baltype - (Default=spendable) A string indicating the balance type to
                retrieve from the current wallet.
      RETURN:
      The current wallet balance (BTC), or -1 if an error occurred.
      """

      self.checkBDM()

      # TODO: use the baltype or get rid of it

      retVal = -1

      topBlk = getBDM().getTopBlockHeight()
      addrList = [a.strip() for a in inB58.split(",")]
      retBalance = 0
      for addrStr in addrList:

         atype,a160 = addrStr_to_hash160(addrStr)
         if atype == getAddrByte():
            # Already checked it's registered, regardless if in a loaded wallet
            utxoList = getUnspentTxOutsForAddr160List([a160])
         else: #p2sh
            # For P2SH, we'll require we have a loaded lockbox
            lbox = self.getLockboxByP2SHAddrStr(addrStr)
            if not lbox:
               raise BitcoindError('Import lockbox before getting P2SH unspent')

            # We simply grab the UTXO list for the lbox, both p2sh and multisig
            cppWallet = self.serverLBCppWalletMap[lbox.uniqueIDB58]
            utxoList = cppWallet.getSpendableTxOutListForValue()

         retBalance += sumTxOutList(utxoList)

      return AmountToJSON(retBalance)


   #############################################################################
   # Get the metadata.
   @catchErrsForJSON
   def jsonrpc_getaddressmetadata(self):
      """
      DESCRIPTION:
      Get all armoryd-specific metadata for the currently loaded wallet.
      PARAMETERS:
      None
      RETURN:
      A dictionary with all metadata sent to armoryd.
      """

      return self.addressMetaData


   #############################################################################
   # A semi-analogue to bitcoind's getinfo().
   @catchErrsForJSON
   def jsonrpc_getarmorydinfo(self):
      """
      DESCRIPTION:
      Get information on the version of armoryd running on the server.
      PARAMETERS:
      None
      RETURN:
      A dictionary listing version of armoryd running on the server.
      """

      isReady = getBDM().getState() == BDM_BLOCKCHAIN_READY

      info = {
               'versionstr':        getVersionString(BTCARMORY_VERSION),
               'version':           getVersionInt(BTCARMORY_VERSION),
               'build':             getArmoryBuild(),
               'walletversionstr':  getVersionString(ARMORY_WALLET_VERSION),
               'walletversion':     getVersionInt(ARMORY_WALLET_VERSION),
               'bdmstate':          getBDM().getState(),
               'balance':           AmountToJSON(self.curWlt.getBalance())
                                    if isReady else -1,
               'blocks':            getBDM().getTopBlockHeight(),
               'difficulty':        getBDM().getTopBlockDifficulty()
                                    if isReady else -1,
               'testnet':           getTestnetFlag(),
             }

      return info


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getbalance(self, baltype='spendable'):
      """
      DESCRIPTION:
      Get the balance of the currently loaded wallet.
      PARAMETERS:
      baltype - (Default=Spendable) A string indicating the balance type to
                retrieve from the current wallet.
      RETURN:
      The current wallet balance (BTC), or -1 if an error occurred.
      """

      self.checkBDM()
      return AmountToJSON(self.curWlt.getBalance(baltype))


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getblock(self, blkhash, verbose='True'):
      """
      DESCRIPTION:
      Get the block associated with a given block hash.
      PARAMETERS:
      blkhash - A hex string representing the block to obtain.
      verbose - (Default=True) If true, data regarding individual pieces of the
                block is returned. If false, the raw block data is returned.
      RETURN:
      A dictionary listing information on the desired block, or empty if the
      block wasn't found.
      """

      if getBDM().getState() in [BDM_UNINITIALIZED, BDM_OFFLINE]:
         raise OfflineError('armoryd is offline')

      head = getBDM().bdv().getHeaderByHash(hex_to_binary(blkhash, BIGENDIAN))

      if not head:
         raise InvalidRequest('Invalid Block or Block not found')

      if verbose.lower() == 'true':
         out = {}
         out['hash'] = blkhash
         out['confirmations'] = (getBDM().getTopBlockHeight() -
                                 head.getBlockHeight()) + 1
         # TODO fix size. It returns max int, as does # Tx. They're never set.
         # out['size'] = head.getBlockSize()
         out['height'] = head.getBlockHeight()
         out['version'] = head.getVersion()
         out['merkleroot'] = binary_to_hex(head.getMerkleRoot(), BIGENDIAN)

         # TODO: Fix this part. TxRef::getTxRefPtrList() was never defined.
         #txlist = head.getTxRefPtrList()
         #ntx = len(txlist)
         #out['tx'] = ['']*ntx
         #for i in range(ntx):
         #   out['tx'][i] = binary_to_hex(txlist[i].getThisHash(), BIGENDIAN)

         out['time'] = head.getTimestamp()
         out['nonce'] = head.getNonce()
         out['bits'] = binary_to_hex(head.getDiffBits(), BIGENDIAN)
         out['difficulty'] = head.getDifficulty()

         # Skip chainwork 'til chainwork data is put in the block header struct.
         # The basic formula is as follows, as reverse engineered from BC Core.
         # - For each block, convert the difficulty into an integer.
         # - Divide 2^256 by the integer.
         # - Add the result to the chainwork val of the previous block (or 0 if
         #   calculating the genesis block's chainwork).
         # - Output the result as a 32 byte, big endian integer string.

         out['previousblockhash'] = binary_to_hex(head.getPrevHash(), BIGENDIAN)
         out['nextblockhash'] = binary_to_hex(head.getNextHash(), BIGENDIAN)
         out['difficultysum'] = head.getDifficultySum()
         out['mainbranch'] = head.isMainBranch()
         out['rawheader'] = binary_to_hex(head.serialize())

      # bitcoind sends a raw block when not verbose. The C++ BlockHeader class
      # still needs to implement TxRef::getTxRefPtrList(). Until then, we can't
      # return a raw block.
      elif verbose.lower() == 'false':
         raise NotImplementedError('Raw Tx data is not available yet')
      else:
         raise InvalidRequest('\"Verbose\" variable (%s) must be \"True\" or '
                              '\"False\"' % verbose)

      return out


   #############################################################################
   # Utility function that takes an email address, gets a PMTA record based on
   # the address, and returns the address found within.
   @catchErrsForJSON
   def jsonrpc_getdanerecfromdns(self, inAddr):
      """
      DESCRIPTION:
      Function that gets a BTCA record from DNS. Prototype.
      PARAMETRS:
      inAddr - Email address with a record in DNS.
      RETURN:
      A string with the Bitcoin address associated with the email address.
      """
      # Code basically stolen from wallet2.0-dns:dnssec_dane/getDANERec.py and
      # then slightly enhanced. This WILL require more work later!

      # For now, assume record name is an email address. Use the SMIME record
      # format, where the username is hashed using SHA224. Also, assume domain
      # is searched.
      retDict = {}
      userAddr = ''
      recordUser, recordDomain = inAddr.split('@', 1)
      sha224Res = sha224(recordUser)
      daneReqName = binary_to_hex(sha224Res) + '._pmta.' + recordDomain

      # Go out and get the DANE record.
      pmtaRecType, daneRec = getDANERecord(daneReqName)
      if pmtaRecType == BTCAID_PAYLOAD_TYPE.PublicKeySource:
         # HACK HACK HACK: Just assume we have a PKS record that is static and
         # has a Hash160 value.
         pksRec = PublicKeySource().unserialize(daneRec)

         # Convert Hash160 to Bitcoin address.
         if daneRec != None:
            userAddr = hash160_to_addrStr(pksRec.rawSource)

      else:
         raise InvalidDANESearchParam(inAddr + " has no DANE record")

      retDict['BTC Address'] = userAddr
      return retDict


   #############################################################################
   # Pull in a signed Tx and get the raw Tx hex data to broadcast. This call
   # works with a regular signed Tx and a signed lockbox Tx if there are already
   # enough signatures.
   @catchErrsForJSON
   def jsonrpc_gethextxtobroadcast(self, txASCIIFile):
      """
      DESCRIPTION:
      Get a signed Tx from a file and get the raw hex data to broadcast.
      PARAMETERS:
      txASCIIFile - The path to a file with a signed transacion.
      RETURN:
      A hex string of the raw transaction data to be transmitted.
      """

      ustxObj = None
      allData = ''
      self.retStr = 'The transaction data cannot be broadcast'

      # Read in the signed Tx data. HANDLE UNREADABLE FILE!!!
      with open(txASCIIFile, 'r') as lbTxData:
         allData = lbTxData.read()

      # Try to decipher the Tx and make sure it's actually signed.
      try:
         ustxObj = UnsignedTransaction().unserializeAscii(allData)
      except BadAddressError:
         errStr = 'This transaction contains inconsistent information. This ' \
                  'is probably not your fault...'
         LOGERROR(errStr)
         raise BadAddressError(errStr)
      except NetworkIDError:
         errStr = 'This transaction is actually for a different network! Did' \
                  'you load the correct transaction?'
         LOGERROR(errStr)
         raise NetworkIDError(errStr)
      except (UnserializeError, IndexError, ValueError):
         errStr = "This transaction can't be read."
         LOGERROR(errStr)
         raise InvalidTransaction(errStr)

      # If we have a signed Tx object, let's make sure it's actually usable.
      finalTx = ustxObj.getBroadcastTxIfReady()
      if finalTx:
         newTxHash = finalTx.getHash()
         LOGINFO('Tx %s may be broadcast - %s' %
                 (binary_to_hex(newTxHash), binary_to_hex(finalTx.serialize())))
         return binary_to_hex(finalTx.serialize())
      else:
         errStr = 'The Tx data isn\'t ready to be broadcast'
         LOGERROR(errStr)
         raise InvalidTransaction(errStr)


   #############################################################################
   # NB: For now, this is incompatible with lockboxes.
   @catchErrsForJSON
   def jsonrpc_gethistorypagecount(self):
      """
      DESCRIPTION:
      Returns the number of history pages associated with the currently loaded
      wallet.
      A history page is a slice of wallet transaction history
      PARAMETERS:
      None
      RETURN:
      The number of history pages.
      """

      return self.curWlt.getHistoryPageCount()


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getledger(self, inB58ID, tx_count=10, from_tx=0, simple=False):
      """
      DESCRIPTION:
      Get a wallet or lockbox ledger.
      PARAMETERS:
      inB58ID - The Base58 ID of the wallet or lockbox from which to obtain the
                ledger. The wallet or lockbox must already be loaded.
      tx_count - (Default=10) The number of entries to get.
      from_tx - (Default=0) The first entry to get.
      simple - (Default=False) Flag indicating if the returned ledger should be
               simple in format.
      RETURN:
      A ledger list with dictionary entries for each transaction.
      """

      self.checkBDM()

      final_le_list = []
      b58Type = 'wallet'
      self.b58ID = str(inB58ID)

      # Get the wallet.
      (ledgerWlt, wltIsCPP) = getWltFromB58ID(self.b58ID, self.serverWltMap,
                                              self.serverLBMap,
                                              self.serverLBCppWalletMap)

      # Proceed only if the incoming ID (and, hence, the wallet) is valid.
      if ledgerWlt is None:
         errMsg = 'Base58 ID %s does not represent a valid wallet or ' \
                  'lockbox.' % self.b58ID
         LOGERROR(errMsg)
         raise WalletDoesNotExist(errMsg)

      # For now, lockboxes can only use C++ wallets, which use a different
      # set of calls and such. If we got back a Python wallet, convert it.
      if wltIsCPP:
         b58Type = 'lockbox'

      # Do some setup to determine how many ledger entries we'll get and
      # which entries we'll get.
      tx_count = int(tx_count)
      from_tx = int(from_tx)
      ledgerEntries = ledgerWlt.getTxLedger()
      sz = len(ledgerEntries)
      lower = min(sz, from_tx)
      upper = min(sz, from_tx+tx_count)
      txSet = set([])
      seen = {}

      # Loop through all the potential ledger entries and create what we can.
      for i in range(lower,upper):
         # Get the exact Tx we're looking for.
         le = ledgerEntries[i]
         txHashBin = le.getTxHash()
         txHashHex = binary_to_hex(txHashBin, BIGENDIAN)
         if seen.get(txHashHex):
            continue
         else:
            seen[txHashHex] = True

         # If the BDM doesn't have the C++ Tx & header, log errors.
         cppTx = getBDM().bdv().getTxByHash(txHashBin)
         cppHead = getBDM().bdv().getHeaderPtrForTx(cppTx)

         headHashBin = cppHead.getThisHash()
         headHashHex = binary_to_hex(headHashBin, BIGENDIAN)
         headtime    = cppHead.getTimestamp()

         # Get some more data.
         # amtCoins: amt of BTC transacted, always positive (how big are
         #           outputs minus change?)
         # netCoins: net effect on wallet (positive or negative)
         # feeCoins: how much fee was paid for this tx
         nconf = (getBDM().getTopBlockHeight() - le.getBlockNum()) + 1
         amtCoins = 0.0
         netCoins = 0.0
         scrAddrs = []
         isToSelf = True
         for i in range(cppTx.getNumTxIn()):
            txIn = cppTx.getTxInCopy(i)
            scrAddr = getBDM().bdv().getSenderScrAddr(txIn)
            if ledgerWlt.hasScrAddress(scrAddr):
               netCoins -= getBDM().bdv().getSentValue(txIn)

         for i in range(cppTx.getNumTxOut()):
            txOut = cppTx.getTxOutCopy(i)
            scrAddr = txOut.getScrAddressStr()
            scrAddrs.append(scrAddr)
            if ledgerWlt.hasScrAddress(scrAddr):
               netCoins += txOut.getValue()
            else:
               isToSelf = False
         feeCoins = getFeeForTx(txHashBin)

         # Find the first recipient and the change recipient.
         firstScrAddr = ''
         changeScrAddr = ''
         if cppTx.getNumTxOut() == 1:
            firstScrAddr = scrAddrs[0]
         elif isToSelf:
            # Sent-to-Self tx
            amtCoins, changeIdx = determineSentToSelfAmt(le, ledgerWlt)
            changeScrAddr = scrAddrs[changeIdx]
            for iout,recipScrAddr in enumerate(scrAddrs):
               if iout != changeIdx:
                  firstScrAddr = recipScrAddr
                  break
            else:
               raise RuntimeError("no addr in tx?") # pragma: no cover
         elif netCoins<0:
            # Outgoing transaction (process in reverse order so get first)
            amtCoins = -1*(netCoins+feeCoins)
            for recipScrAddr in scrAddrs[::-1]:
               if ledgerWlt.hasScrAddress(recipScrAddr):
                  changeScrAddr = recipScrAddr
               else:
                  firstScrAddr = recipScrAddr
            if firstScrAddr == '':
               raise RuntimeError("no addr in outgoing tx?") # pragma: no cover

         else:
            # Incoming transaction (process in reverse order so get first)
            amtCoins = netCoins
            for recipScrAddr in scrAddrs[::-1]:
               if ledgerWlt.hasScrAddress(recipScrAddr):
                  firstScrAddr = recipScrAddr
               else:
                  changeScrAddr = recipScrAddr
            if firstScrAddr == '':
               raise RuntimeError("noaddr in incoming tx?") # pragma: no cover

         # Determine the direction of the Tx based on the coin setup.
         if netCoins > -feeCoins:
            txDir = 'receive'
         elif netCoins < -feeCoins:
            txDir = 'send'
         else:
            txDir = 'toself'

         # Convert the scrAddrs to display strings.
         firstAddr = scrAddr_to_displayStr(firstScrAddr, self.serverWltMap,
                                           self.serverLBMap.values())
         changeAddr = ''
         if len(changeScrAddr):
            changeAddr = scrAddr_to_displayStr(changeScrAddr, self.serverWltMap,
                                               self.serverLBMap.values())

         # Get the address & amount from each TxIn.
         myinputs, otherinputs = [], []
         for iin in range(cppTx.getNumTxIn()):
            sender = getBDM().bdv().getSenderScrAddr(cppTx.getTxInCopy(iin))
            val    = getBDM().bdv().getSentValue(cppTx.getTxInCopy(iin))
            addTo  = (myinputs if ledgerWlt.hasScrAddress(sender) else
                      otherinputs)
            senderStr = scrAddr_to_displayStr(sender, self.serverWltMap,
                                              self.serverLBMap.values())
            addTo.append({'address': senderStr,
                          'amount':  AmountToJSON(val)})

         # Get the address & amount from each TxOut.
         myoutputs, otheroutputs = [], []
         for iout in range(cppTx.getNumTxOut()):
            recip = cppTx.getTxOutCopy(iout).getScrAddressStr()
            val   = cppTx.getTxOutCopy(iout).getValue()
            addTo = (myoutputs if ledgerWlt.hasScrAddress(recip) else
                     otheroutputs)
            recipStr = scrAddr_to_displayStr(recip, self.serverWltMap,
                                             self.serverLBMap.values())
            addTo.append({'address': recipStr,
                          'amount':  AmountToJSON(val)})

         tx_info = {
            'direction' :    txDir,
            b58Type :        inB58ID,
            'amount' :       AmountToJSON(amtCoins),
            'netdiff' :      AmountToJSON(netCoins),
            'fee' :          AmountToJSON(feeCoins),
            'txid' :         txHashHex,
            'blockhash' :    headHashHex,
            'confirmations': nconf,
            'txtime' :       le.getTxTime(),
            'txsize' :       len(cppTx.serialize()),
            'blocktime' :    headtime,
            'firstrecip':    firstAddr,
            'changerecip':   changeAddr,
            # TODO: wallet 2.0 get the txcomments to show, even on lockbox tx's 
            #'comment' :      ledgerWlt.getTxComment(txHashBin),
         }

         # Add more info if it's not a simple ledger.
         if not simple:
            tx_info['senderme']     = myinputs
            tx_info['senderother']  = otherinputs
            tx_info['recipme']      = myoutputs
            tx_info['recipother']   = otheroutputs

         # Add the ledger entry to the ledger list.
         final_le_list.append(tx_info)

      return final_le_list


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getledgersimple(self, inB58ID, tx_count=10, from_tx=0):
      """
      DESCRIPTION:
      Get a simple version of a wallet or lockbox ledger.
      PARAMETERS:
      inB58ID - The Base58 ID of the wallet or lockbox from which to obtain the
                ledger. The wallet or lockbox must already be loaded.
      tx_count - (Default=10) The number of entries to get.
      from_tx - (Default=0) The first entry to get.
      RETURN:
      A dictionary with a wallet ledger of type "simple".
      """

      return self.jsonrpc_getledger(inB58ID, tx_count, from_tx, True)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getlockboxbalance(self, baltype='spendable'):
      """
      DESCRIPTION:
      Get the balance of the currently loaded lockbox.
      PARAMETERS:
      baltype - (Default=Spendable) A string indicating the balance type to
                retrieve from the current wallet.
      RETURN:
      The current lockbox balance (BTC), or -1 if an error occurred.
      """

      return self.getLockboxBalance(self.curLB.uniqueIDB58, baltype)


   #############################################################################
   # Get info for a lockbox by lockbox ID. If no ID is specified, we'll get info
   # on the currently loaded LB if an LB exists.
   @catchErrsForJSON
   def jsonrpc_getlockboxinfo(self, inLBID=None, outForm='JSON'):
      """
      DESCRIPTION:
      Get information on the lockbox associated with a lockbox ID string or, if
      it exists, the currently active armoryd lockbox.
      PARAMETERS:
      inLBID - (Default=None) If used, armoryd will get information on the
               lockbox with the provided Base58 ID instead of the currently
               active armoryd lockbox.
      outForm - (Default=JSON) If used, armoryd will return the lockbox in a
                particular format. Choices are "JSON", "Hex", and "Base64".
      RETURN:
      If the lockbox is found, a dictionary with information on the lockbox will
      be returned.
      """

      self.lbToUse = self.curLB
      ret = None

      # We'll return info on the currently loaded LB if no LB ID has been
      # specified. If an LB ID has been specified, we'll get info on it if the
      # specified LB has been loaded.
      if inLBID in self.serverLBMap.keys():
         self.lbToUse = self.serverLBMap[inLBID]
      elif self.lbToUse is None:
         raise LockboxDoesNotExist("There are no lockboxes on the server")
      elif inLBID is not None:
         raise LockboxDoesNotExist("Lockbox %s does not exist" % inLBID)

      # Get info on the lockbox.
      self.outForm = outForm.lower()
      if self.outForm == 'json':
         ret = self.lbToUse.toJSONMap()
         ret['balance'] = self.getLockboxBalance(self.lbToUse.uniqueIDB58)
      elif self.outForm == 'hex':
         ret = binary_to_hex(self.lbToUse.serialize())
      elif self.outForm == 'base64':
         ret = base64.b64encode(binary_to_hex(self.lbToUse.serialize()))
      else:
         raise InvalidRequest('%s is an invalid output type.' % self.outForm)

      return ret


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getnewaddress(self, internal=0):
      """
      DESCRIPTION:
      Get a new Base58 address from the currently loaded wallet.
      PARAMETERS:
      internal - 1 means you will get a "change" address.
                 Ignored for Armory135 wallets
      RETURN:
      The wallet's next unused public address in Base58 form.
      """

      i = int(internal)
      if i not in (0,1):
         raise InvalidRequest("internal should be 0 or 1")

      if i == 0:
         addr = self.curWlt.getNextReceivingAddress()
      else:
         addr = self.curWlt.getNextChangeAddress()

      return addr.getAddrStr()


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getrawtransaction(self, txHash, verbose=0, endianness=BIGENDIAN):
      """
      DESCRIPTION:
      Get the raw transaction string for a given transaction hash.
      PARAMETERS:
      txHash - A string representing the hex value of a transaction ID.
      verbose - (Default=0) Integer indicating whether or not the result should
                be more verbose.
      endianness - (Default=BIGENDIAN) Indicates the endianness of the ID.
      RETURN:
      A dictionary with the decoded raw transaction and relevant information.
      """

      rawTx = None
      cppTx = getBDM().bdv().getTxByHash(hex_to_binary(txHash, endianness))
      if cppTx.isInitialized():
         txBinary = cppTx.serialize()
         pyTx = PyTx().unserialize(txBinary)
         rawTx = binary_to_hex(pyTx.serialize())
         if int(verbose):
            result = self.jsonrpc_decoderawtransaction(rawTx)
            result['hex'] = rawTx
         else:
            result = rawTx
      else:
         raise InvalidTransaction(
            'Tx hash not recognized by getBDM(): %s' % txHash)

      return result


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getreceivedbyaddress(self, address, baltype="spendable"):
      """
      DESCRIPTION:
      Get the number of coins received by a Base58 address associated with
      the currently loaded wallet.
      PARAMETERS:
      address - The Base58 address associated with the current wallet.
      baltype - (Default=spendable) Balance type
      RETURN:
      The balance received from the incoming address (BTC).
      """

      self.checkBDM()

      # TODO: use the baltype or get rid of it

      addrType, addr160 = addrStr_to_hash160(address, True)
      balance = 0
      if addrType == getAddrByte():
         balance = self.curWlt.getAddrBalance(addr160, 'full')
      else: # p2sh
         lbox = self.getLockboxByP2SHAddrStr(address)
         cppWallet = self.serverLBCppWalletMap.get(lbox.uniqueIDB58)
         balance = cppWallet.getFullBalance()

      return AmountToJSON(balance)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getreceivedfromaddress(self, sender):
      """
      DESCRIPTION:
      Return the number of coins received from a particular sender.
      PARAMETERS:
      sender - Base58 address of the sender to the current wallet.
      RETURN:
      Number of Bitcoins sent by the sender to the current wallet.
      """

      self.checkBDM()

      totalReceived = 0.0
      ledgerEntries = self.curWlt.getTxLedger('blk')

      for entry in ledgerEntries:
         cppTx = getBDM().bdv().getTxByHash(entry.getTxHash())
         if cppTx.isInitialized():
            # Only consider the first for determining received from address
            # This function should assume it is online, and actually request
            # the previous TxOut script from the BDM -- which guarantees we
            # know the sender.
            # Use getBDM().getSenderScrAddr(txin).  This takes a C++ txin
            # (which we have) and it will grab the TxOut being spent by that
            # TxIn and return the scraddr of it.  This will succeed 100% of
            # the time.
            cppTxin = cppTx.getTxInCopy(0)
            scrAddr = getBDM().bdv().getSenderScrAddr(cppTxin)
            txInAddr = scrAddr_to_addrStr(scrAddr)

            if sender == txInAddr:
               txBinary = cppTx.serialize()
               pyTx = PyTx().unserialize(txBinary)
               for txout in pyTx.outputs:
                  scrAddr = script_to_scrAddr(txout.getScript())
                  if self.curWlt.getAddress(scrAddr):
                     totalReceived += txout.value

      return AmountToJSON(totalReceived)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getreceivedfromsigner(self, *sigBlock):
      """
      DESCRIPTION:
      Verify that a message (RFC 2440: clearsign or Base64) has been signed by
      a Bitcoin address and get the amount of coins sent to the current wallet
      by the message's signer.
      PARAMETERS:
      sigBlock - Message with the RFC 2440 message to be verified. The message
                 must be enclosed in quotation marks.
      RETURN:
      A dictionary with verified message and the amount of money sent to the
      current wallet by the signer.
      """

      # We must deal with a quirk. Non-escaped spaces (i.e., spaces that aren't
      # \u0020) will cause the CL parser to split the sig into multiple lines.
      # We need to combine the lines. (NB: Strip the final space too!)
      signedMsg = (''.join((str(piece) + ' ') for piece in sigBlock))[:-1]

      verification = self.jsonrpc_verifysignature(signedMsg)
      return {
         'message': verification['message'],
         'amount': self.jsonrpc_getreceivedfromaddress(verification['address'])
      }


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_gettransaction(self, txHash):
      """
      DESCRIPTION:
      Get the transaction associated with a given transaction hash.
      PARAMETERS:
      txHash - A hex string representing the transaction to obtain.
      RETURN:
      A dictionary listing information on the desired transaction, or empty if
      the transaction wasn't found.
      """

      if getBDM().getState() in [BDM_UNINITIALIZED, BDM_OFFLINE]:
         raise OfflineError('armoryd is offline')

      binhash = hex_to_binary(txHash, BIGENDIAN)
      tx = getBDM().bdv().getTxByHash(binhash)
      if not tx.isInitialized():
         raise InvalidTransaction('transaction not found')

      out = {}
      out['txid'] = txHash
      isMainBranch = getBDM().bdv().isTxMainBranch(tx)
      out['mainbranch'] = isMainBranch
      out['numtxin'] = int(tx.getNumTxIn())
      out['numtxout'] = int( tx.getNumTxOut())

      haveAllInputs = True
      txindata = []
      inputvalues = []
      outputvalues = []
      for i in range(tx.getNumTxIn()):
         op = tx.getTxInCopy(i).getOutPoint()
         prevtx = getBDM().bdv().getTxByHash(op.getTxHash())
         txid = binary_to_hex(op.getTxHash(), BIGENDIAN)
         if prevtx.isInitialized():
            txout = prevtx.getTxOutCopy(op.getTxOutIndex())
            inputvalues.append(txout.getValue())
            recip160 = CheckHash160(txout.getScrAddressStr())
            txindata.append( { 'address': hash160_to_addrStr(recip160),
                               'value':   AmountToJSON(txout.getValue()),
                               'ismine':   self.curWlt.hasAddr(recip160),
                               'fromtxid': txid,
                               'fromtxindex': op.getTxOutIndex()})
         else:
            haveAllInputs = False
            txindata.append( { 'address': '00'*32,
                               'value':   '-1',
                               'ismine':   False,
                               'fromtxid': txid,
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

      if isMainBranch:
         # The tx is in a block, fill in the rest of the data
         out['confirmations'] = (getBDM().getTopBlockHeight() -
                                 tx.getBlockHeight()) + 1
         out['orderinblock'] = int(tx.getBlockTxIndex())

         le = self.curWlt.getLedgerEntryForTx(binhash)
         amt = le.getValue()
         out['netdiff']     = AmountToJSON(amt)
         out['totalinputs'] = AmountToJSON(sum(inputvalues))

         if le.getTxHash()=='\x00'*32:
            out['category']  = 'unrelated'
            out['direction'] = 'unrelated'
         elif le.isSentToSelf():
            out['category']  = 'toself'
            out['direction'] = 'toself'
         elif amt<fee:
            out['category']  = 'send'
            out['direction'] = 'send'
         else:
            out['category']  = 'receive'
            out['direction'] = 'receive'

      return out


   #############################################################################
   # NOTE: For now, the "includemempool" option isn't included. It seems to be a
   # dead option on bitcoind. If this ever changes, it can be implemented.
   @catchErrsForJSON
   def jsonrpc_gettxout(self, txHash, n, binary=0):
      """
      DESCRIPTION:
      Get the TxOut entries for a given transaction hash.
      PARAMETERS:
      txHash - A string representing the hex value of a transaction ID.
      n - The TxOut index to obtain.
      binary - (Default=0) Boolean value indicating whether or not the
               resultant binary script should be in binary form or converted
               to a hex string.
      RETURN:
      A dictionary with the Bitcoin amount for the TxOut and the TxOut script in
      hex string form (default) or binary form.
      """

      n = int(n)
      txOut = None
      cppTx = getBDM().bdv().getTxByHash(hex_to_binary(txHash, BIGENDIAN))
      if cppTx.isInitialized():
         txBinary = cppTx.serialize()
         pyTx = PyTx().unserialize(txBinary)
         if n < len(pyTx.outputs):
            # If the user doesn't want binary data, return a formatted string,
            # otherwise return a hex string with the raw TxOut data.
            result = {}
            txOut = pyTx.outputs[n]
            if int(binary):
               script = txOut.binScript
            else:
               script = binary_to_hex(txOut.binScript)
            result = {'value' : AmountToJSON(txOut.value),
                      'script' : script}
         else:
            errStr = 'Tx output index is invalid: #%d' % n
            LOGERROR(errStr)
            raise InvalidRequest(errStr)
      else:
         errStr = 'Tx hash not recognized by getBDM(): %s' % binary_to_hex(txHash)
         LOGERROR(errStr)
         raise InvalidTransaction(errStr)

      return result


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getwalletinfo(self, inWltID=None):
      """
      DESCRIPTION:
      Get information on the currently loaded wallet.
      PARAMETERS:
      inWltID - (Default=None) If used, armoryd will get info for the wallet for
                the provided Base58 wallet ID instead of the current wallet.
      RETURN:
      A dictionary with information on the current wallet.
      """
      wltInfo = {}
      self.isReady = getBDM().getState() == BDM_BLOCKCHAIN_READY
      self.wltToUse = self.curWlt

      # If we're not getting info on the currently loaded wallet, check to make
      # sure the incoming wallet ID points to an actual wallet.
      if inWltID:
         if self.serverWltMap.get(inWltID) is None:
            raise WalletDoesNotExist("Wallet %s is not loaded" % inWltID)

         self.wltToUse = self.serverWltMap[inWltID]

      external = self.wltToUse.external.childIndex
      internal = self.wltToUse.internal.childIndex

      return {
         "name":            self.wltToUse.getLabel(),
         "description":     self.wltToUse.getDescription(),
         "walletversion":   getVersionString(ARMORY_WALLET_VERSION),
         "balance":         AmountToJSON(self.wltToUse.getBalance('Spend')),
         "numaddrgen":      external + internal,
         "externaladdrgen": external,
         "internaladdrgen": internal,
         "createdate":      self.wltToUse.keyBornTime,
         "walletid":        self.wltToUse.uniqueIDB58,
         "islocked":        self.wltToUse.isLocked(),
         "encryption":      self.wltToUse.useEncryption(),
         "xpub":            self.wltToUse.getExtendedPubKey(),
      }


   #############################################################################
   # Get a dictionary with all functions the armoryd server can run.
   @catchErrsForJSON
   def jsonrpc_help(self):
      """
      DESCRIPTION:
      Get a directionary with all functions the armoryd server can run.
      PARAMETERS:
      None
      RETURN:
      A dictionary with all functions available on the armoryd server, along
      with the function parameters and function return value.
      """

      return jsonFuncDict


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_importprivkey(self, privKey):
      """
      DESCRIPTION:
      Import a private key into the current wallet.
      PARAMETERS:
      privKey - A private key in any format supported by Armory, including
                Base58 private keys supported by bitcoind (uncompressed public
                key support only).
      RETURN:
      A string of the private key's accompanying hexadecimal public key.
      """

      self.checkUnlock()

      # Convert string to binary
      privKey = str(privKey)
      privKeyValid = True

      # Make sure the key is one we can support
      binPrivKey, self.privKeyType = parsePrivateKeyData(privKey)
      if len(binPrivKey) == 33 and binPrivKey[-1] == b'\x01':
         binPrivKey = binPrivKey[:-1]

      self.binPrivKey = SecureBinaryData(binPrivKey)
      self.curWlt.isDisabled = True

      try:
         self.thePubKey = self.curWlt.importExternalAddressData(
            self.binPrivKey, self.privKeyType)
      except RuntimeError:
         self.binPrivKey.destroy()
         LOGERROR('Attempt to import a private key failed.')
         raise InvalidRequest('Attempt to import your private key failed. '
                              'Check if the key is already in your wallet.')

      self.binPrivKey.destroy()
      return {'PubKey': self.thePubKey}


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_importwatchonly(self, xpub):
      """
      DESCRIPTION:
      Import an extended public key as a watch-only wallet.
      Note this new wallet is set as the active wallet.
      PARAMETERS:
      xpub - An extended public key.
      RETURN:
      A string of the unique id of the wallet (base58)
      """

      wallet = ABEK_StdWallet()
      wallet.initializeFromXpub(xpub)
      wltID = wallet.uniqueIDB58

      if wltID in self.serverWltMap:
         raise WalletExistsError("Wallet %s already exists" % wltID)

      wallet.wltParentID = wltID
      wallet.fillKeyPool(False)
      wallet.setLabel("Watch Only - %s" % wltID, fsync=False)

      filename = "armory_wallet2.0_%s_watchonly.wlt" % wltID

      # now we need to put this in a file
      wltFile = ArmoryWalletFile.CreateWalletFile_BASE(
         walletName=u'Imported Watch-only Wallet',
         root=wallet,
         createInDir=self.armoryHomeDir,
         specificFilename=filename,
      )
      self.curWlt = wltFile.topLevelRoots[0]

      return self.curWlt.uniqueIDB58


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_listaddresses(self, wltID=None):
      """
      DESCRIPTION:
      list all addresses associated with the wallet
      PARAMETERS:
      wltID - (Default=currently loaded wallet) The wallet ID
      RETURN:
      A dict with two keys "external" and "internal" each of which is
      a list of base58 strings of the addresses associated with the wallet.
      """

      wlt = self.curWlt
      if wltID is not None:
         wlt = self.serverWltMap.get(wltID)
         if wlt is None:
            raise WalletDoesNotExist("Wallet %s does not exist" % wltID)

      if isinstance(wlt, ABEK_StdWallet):
         ret = {"external": [], "internal": []}

         for i, c in wlt.external.akpChildByIndex.iteritems():
            ret["external"].append(c.getAddrStr())

         for i, c in wlt.internal.akpChildByIndex.iteritems():
            ret["internal"].append(c.getAddrStr())

         return ret
      else:
         # TODO handle Armory135
         pass


   #############################################################################
   # Get a dictionary with UTXOs for the wallet associated with the Base58
   # address passed into the function. By default, zero-conf UTXOs are included.
   # The basic layout of the dictionary is as follows.
   # {
   #    addrbalance  : {
   #                     Address : Balance
   #                   }
   #    numutxo      : int
   #    totalbalance : float
   #    utxolist     : {
   #                     Same information as listunspent
   #                   }
   # }
   @catchErrsForJSON
   def jsonrpc_listaddrunspent(self, inB58):
      """
      DESCRIPTION:
      Get a list of unspent transactions for the currently loaded wallet that
      are associated with a given, comma-separated list of Base58 addresses from
      the wallet. By default, zero-conf UTXOs are included.
      PARAMETERS:
      inB58 - The Base58 address to check against the current wallet.
      RETURN:
      A dictionary containing all UTXOs for the currently loaded wallet
      associated with the given Base58 address, along with information about
      each UTXO.
      """
      # TODO:  We should probably add paging to this...

      totalTxOuts = 0
      totalBal = 0
      utxoDict = {}
      utxoList = []

      # Get the UTXO balance & list for each address.
      # The strip() makes it possible to supply addresses with
      # spaces after or before each comma
      addrList = [a.strip() for a in inB58.split(",")]
      curTxOut = 0
      topBlk = getBDM().getTopBlockHeight()
      addrBalanceMap = {}
      utxoEntries = []
      for addrStr in addrList:
         atype,a160 = addrStr_to_hash160(addrStr)
         if atype==getAddrByte():
            # Already checked it's registered, regardless if in a loaded wallet
            utxoList = getUnspentTxOutsForAddr160List([a160])
         else: # p2sh
            # For P2SH, we'll require we have a loaded lockbox
            lbox = self.getLockboxByP2SHAddrStr(addrStr)
            if not lbox:
               raise BitcoindError('Import lockbox before getting P2SH unspent')

            # We simply grab the UTXO list for the lbox, both p2sh and multisig
            cppWallet = self.serverLBCppWalletMap[lbox.uniqueIDB58]
            utxoList = cppWallet.getSpendableTxOutListForValue()

         utxoListInfo = self.getUtxoInfo(utxoList)
         utxoEntries.extend(utxoListInfo)
         totalTxOuts += len(utxoListInfo)
         utxoListBal = sum([x['amount'] for x in utxoListInfo])
         totalBal += utxoListBal
         addrBalanceMap[addrStr] = utxoListBal

      # Let's round out the master dict with more info.
      utxoDict['utxolist']     = utxoEntries
      utxoDict['numutxo']      = totalTxOuts
      utxoDict['addrbalance']  = addrBalanceMap
      utxoDict['totalbalance'] = totalBal

      return utxoDict


   #############################################################################
   # Function that lists all the loaded wallets.
   @catchErrsForJSON
   def jsonrpc_listloadedlockboxes(self):
      """
      DESCRIPTION:
      List all lockboxes loaded onto the armoryd server.
      PARAMETERS:
      None
      RETURN:
      A dictionary with the Base58 values of all lockboxes loaded in armoryd.
      """

      # Return a dictionary with a string as the key and a wallet B58 value as
      # the value.
      curKey = 1
      lockboxList = {}
      for l in self.serverLBMap.keys():
         curLBStr = 'Lockbox %04d' % curKey
         lockboxList[curLBStr] = l
         curKey += 1
      return lockboxList


   #############################################################################
   # Function that lists all the loaded wallets.
   @catchErrsForJSON
   def jsonrpc_listloadedwallets(self):
      """
      DESCRIPTION:
      List all wallets loaded onto the armoryd server.
      PARAMETERS:
      None
      RETURN:
      A dictionary with the Base58 values of all wallets loaded in armoryd.
      """

      # Return a dictionary with a string as the key and a wallet B58 value as
      # the value.
      curKey = 1
      walletList = {}
      for k, wlt in self.serverWltMap.iteritems():
         curWltStr = '%s: Wallet %04d (%s)' % (wlt.wltFileRef.uniqueIDB58,
                                               curKey, wlt.getLabel())
         walletList[curWltStr] = k
         curKey += 1
      return walletList


   #############################################################################
   # NB: For now, this is incompatible with lockboxes.
   @catchErrsForJSON
   def jsonrpc_listtransactions(self, from_page=0):
      """
      DESCRIPTION:
      List the transactions associated with the currently loaded wallet.
      PARAMETERS:
      from_page - (Default=0) The history page to get the transactions from.
      RETURN:
      A dictionary with information on the retrieved transactions.
      """

      # This does not use 'account's like in the Satoshi client

      final_tx_list = []
      #this should be in a try/catch block, since it will throw if from_page is
      #out of range
      ledgerEntries = self.curWlt.getHistoryPage(from_page)

      sz = len(ledgerEntries)
      txSet = set([])

      for i in range(sz):

         le = ledgerEntries[i]
         txHashBin = le.getTxHash()
         if txHashBin in txSet:
            continue

         txSet.add(txHashBin)
         txHashHex = binary_to_hex(txHashBin, BIGENDIAN)

         cppTx = getBDM().bdv().getTxByHash(txHashBin)
         if not cppTx.isInitialized():
            LOGERROR('Tx hash not recognized by getBDM(): %s' % txHashHex)

         #cppHead = cppTx.getHeaderPtr()
         cppHead = getBDM().bdv().getHeaderPtrForTx(cppTx)
         if not cppHead.isInitialized:
            LOGERROR('Header pointer is not available!')

         blockIndex = cppTx.getBlockTxIndex()
         blockHash  = binary_to_hex(cppHead.getThisHash(), BIGENDIAN)
         blockTime  = le.getTxTime()
         isToSelf   = le.isSentToSelf()
         feeCoin   = getFeeForTx(txHashBin)
         totalBalDiff = le.getValue()
         nconf = (getBDM().getTopBlockHeight() -
                  le.getBlockNum()) + 1

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
         if totalBalDiff < -feeCoin:
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
   # Get a list of UTXOs for the currently loaded wallet.
   @catchErrsForJSON
   def jsonrpc_listunspent(self):
      """
      DESCRIPTION:
      Get a list of unspent transactions for the currently loaded wallet. By
      default, zero-conf UTXOs are included.
      PARAMETERS:
      None
      RETURN:
      A dictionary listing information about each UTXO in the currently loaded
      wallet. The dictionary is similar to the one returned by the bitcoind
      call of the same name.
      """

      self.checkBDM()

      # Return a dictionary with a string as the key and a wallet B58 value as
      # the value.
      utxoList = self.curWlt.getFullUTXOList()
      return self.getUtxoInfo(utxoList)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_sendasciitransaction(self, txASCIIFile):
      """
      DESCRIPTION:
      Broadcast to the bitcoin network the signed tx in the txASCIIFile
      PARAMETERS:
      txASCIIFile - The path to a file with a signed transacion.
      RETURN:
      The transaction id of the tx that was broadcast
      """

      # Read in the signed Tx data. HANDLE UNREADABLE FILE!!!
      with open(txASCIIFile, 'r') as lbTxData:
         allData = lbTxData.read()

      # Try to decipher the Tx and make sure it's actually signed.
      txObj = UnsignedTransaction().unserializeAscii(allData)
      if not txObj:
         raise InvalidTransaction, "file does not contain a valid tx"
      if not txObj.verifySigsAllInputs():
         raise IncompleteTransaction("transaction needs more signatures")

      pytx = txObj.getSignedPyTx()

      self.NetworkingFactory.sendTx(pytx)
      return pytx.getHashHex(BIGENDIAN)


   #############################################################################
   # Send ASCII-encoded lockboxes to recipients via e-mail. For now, only
   # lockboxes from ArmoryQt's master list (multisigs.txt) or from the Armory
   # home directory will be searched.
   @catchErrsForJSON
   def jsonrpc_sendlockbox(self, lbIDs, sender, server, pwd, recips,
                           msgSubj='Armory Lockbox', usebasic=False):
      """
      DESCRIPTION:
      E-mail ASCII-encoded lockboxes to recipients.
      PARAMETERS:
      lbIDs - A colon-delineated list of Base58 IDs of lockboxes to send to an
              email recipient.
      sender - The email address of the sender.
      server - The SMTP email server.
      pwd - The email account password.
      recips - The recipient or, if the string is delineated by a colon, a list
               of recipients.
      msgSubj - (Default=Armory Lockbox) The email subject.
      RETURN:
      A string indicating whether or not the attempt to send was successful.
      """
      # Initial setup
      retStr = 'sendlockbox command succeeded.'
      if msgSubj == None:
         msgSubj = 'Armory Lockboxes'
      lbIDs = lbIDs.split(":")
      # Write the decorated function that will send the e-mail out.
      @EmailOutput(sender, server, pwd, recips, msgSubj, usebasic)
      def sendLockboxes(lockboxes):
         emailText = '%s has sent you lockboxes used by Armory.' % sender
         emailText += ' The lockboxes can be found printed below.\n\n'
         emailText += 'TOTAL LOCKBOXES: %d\n\n' % len(lockboxes)
         for curLB in lockboxes:
            emailText += self.serverLBMap[curLB].serializeAscii() + '\n\n'

         return emailText

      # Do these lockboxes actually exist? If not, let the user know and bail.
      allLBsValid = True
      for curLB in lbIDs:
         if not curLB in self.serverLBMap.keys():
            LOGERROR('Lockbox %s does not exist! Exiting.' % curLB)
            allLBsValid = False
            retStr = 'sendlockbox command failed. %s does not exist.' % curLB
            break
      # Send the lockbox notifications if all the lockboxes exist.
      if allLBsValid:
         sendLockboxes(lbIDs)

      return retStr


   #############################################################################
   # Function that sets the active lockbox using a B58 string.
   @catchErrsForJSON
   def jsonrpc_setactivelockbox(self, newIDB58):
      """
      DESCRIPTION:
      Set the currently active lockbox to one already loaded on the armoryd
      server.
      PARAMETERS:
      newIDB58 - The Base58 ID of the lockbox to be made active.
      RETURN:
      A string indicating whether or not the lockbox was set as desired.
      """

      # Return a string indicating whether or not the active wallet was set to a
      # new wallet. If the change fails, keep the currently active wallet.
      retStr = ''
      try:
         newLB = self.serverLBMap[newIDB58]
         self.curLB = newLB  # Separate in case ID's wrong & error's thrown.
         retStr = 'Lockbox %s is now active.' % newIDB58
      except:
         LOGERROR('setactivelockbox - Lockbox %s does not exist.' % newIDB58)
         retStr = 'Lockbox %s does not exist.' % newIDB58
      return retStr


   #############################################################################
   # Function that sets the active wallet using a B58 string.
   @catchErrsForJSON
   def jsonrpc_setactivewallet(self, newIDB58):
      """
      DESCRIPTION:
      Set the currently active wallet to one already loaded on the armoryd
      server.
      PARAMETERS:
      newIDB58 - The Base58 ID of the wallet to be made active.
      RETURN:
      A string indicating whether or not the wallet was set as desired.
      """

      # Return a string indicating whether or not the active wallet was set to a
      # new wallet. If the change fails, keep the currently active wallet.
      retStr = ''

      try:
         newWlt = self.serverWltMap[newIDB58]
         self.curWlt = newWlt  # Separate in case ID's wrong & error's thrown.
         LOGINFO('Syncing wallet: %s' % newIDB58)
         retStr = 'Wallet %s is now active.' % newIDB58
      except:
         LOGERROR('setactivewallet - Wallet %s does not exist.' % newIDB58)
         retStr = 'Wallet %s does not exist.' % newIDB58
      return retStr


   #############################################################################
   # Associate meta data to an address or addresses
   # Example input:  "{\"mzAtXhy3Z6SLd7rAwNJrL17e8mQkjDVDXh\": {\"chain\": 5,
   # \"index\": 2}, \"mkF5L93F5HLhLmQagX26TdXcvPGHvfjoTM\": {\"CrazyField\":
   # \"what\", \"1\": 1, \"2\": 2}}"
   @catchErrsForJSON
   def jsonrpc_setaddressmetadata(self, newAddressMetaData):
      """
      DESCRIPTION:
      Set armoryd-specific metadata associated with Base58 addresses.
      PARAMETERS:
      newAddressMetaData - A dictionary containing arbitrary metadata to attach
                           to Base58 addresses listed with the metadata.
      RETURN:
      None
      """

      # Loop once to check the addresses
      # Don't add any meta data if one of the addresses wrong.
      for addr in newAddressMetaData.keys():
         if not checkAddrStrValid(addr):
            raise InvalidBitcoinAddress
         if not self.curWlt.hasAddr(addrStr_to_hash160(addr, False)[1]):
            raise AddressNotInWallet
      self.addressMetaData.update(newAddressMetaData)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_setlockboxinfo(self, inLBID, name, description):
      """
      DESCRIPTION:
      Set name and description on a wallet.
      PARAMETERS:
      inLBID - base58 ID of the lockbox to set the name and description for.
      name - a label to describe the wallet
      description - a more thorough description of the wallet
      
      RETURN:
      A dictionary with information on the wallet.
      """

      lb = self.serverLBMap.get(inLBID)
      if lb is None:
         raise LockboxDoesNotExist("Lockbox %s is not loaded" % inLBID)
      lb.shortName = name
      lb.longDescr = description
      lb.fsync()
      return self.jsonrpc_getlockboxinfo(inLBID)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_setwalletinfo(self, inWltID, name, description):
      """
      DESCRIPTION:
      Set name and description on a wallet.
      PARAMETERS:
      inWltID - base58 ID of the wallet to set the name and description for.
      name - a label to describe the wallet
      description - a more thorough description of the wallet
      
      RETURN:
      A dictionary with information on the wallet.
      """

      wlt = self.serverWltMap.get(inWltID)
      if wlt is None:
         raise WalletDoesNotExist("Wallet %s is not loaded" % inWltID)
      wlt.setLabel(name)
      wlt.setDescription(description)
      wlt.fsync()
      return self.jsonrpc_getwalletinfo(inWltID)


   #############################################################################
   # Take the ASCII representation of an unsigned Tx (i.e., the data that is
   # signed by Armory's offline Tx functionality) and returns an ASCII
   # representation of the signed Tx, with the current wallet signing the Tx.
   # See SignBroadcastOfflineTxFrame::signTx() (ui/TxFrames.py) for the GUI's
   # analog. Note this function can sign multisigs as well as normal inputs.
   @catchErrsForJSON
   def jsonrpc_signasciitransaction(self, txASCIIFile):
      """
      DESCRIPTION:
      Sign whatever parts of the transaction the currently active wallet and/or
      lockbox can.
      PARAMETERS:
      txASCIIFile - The path to a file with an unsigned transacion.
      RETURN:
      An ASCII-formatted semi-signed transaction, similar to the one output by
      Armory for offline signing.
      """

      ustxObj = None
      allData = ''

      # Read in the signed Tx data. HANDLE UNREADABLE FILE!!!
      with open(txASCIIFile, 'r') as lbTxData:
         allData = lbTxData.read()

      # Try to decipher the Tx and make sure it's actually signed.
      try:
         ustxObj = UnsignedTransaction().unserializeAscii(allData)
      except BadAddressError:
         errStr = 'This transaction contains inconsistent information. This ' \
                  'is probably not your fault...'
         LOGERROR(errStr)
         raise BadAddressError(errStr)
      except NetworkIDError:
         errStr = 'This transaction is actually for a different network! Did' \
                  'you load the correct transaction?'
         LOGERROR(errStr)
         raise NetworkIDError(errStr)
      except (UnserializeError, IndexError, ValueError):
         errStr = "This transaction can't be read."
         LOGERROR(errStr)
         raise InvalidTransaction(errStr)

      stx = self.curWlt.signUnsignedTx(ustxObj)
      return stx.serializeAscii()


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_signmessage(self, addr, message):
      """
      DESCRIPTION:
      Create a message that can be verified to be coming from you
      PARAMETERS:
      addr - An address in the current wallet
      message - message to sign
      RETURN:
      A clear-signed message
      """

      self.checkUnlock()

      scrAddr = addrStr_to_scrAddr(addr)
      addrObj = self.curWlt.getAddress(scrAddr)
      if addrObj is None:
         raise BadAddressError("address %s not found in current wallet" % addr)
      return addrObj.clearSignMessage(str(message))


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_stop(self):
      """
      DESCRIPTION:
      Stop the RPC server
      PARAMETERS:
      None
      RETURN:
      None
      """

      # Stop armoryd
      reactor.stop()


   #############################################################################
   # The following is a fake example of a message that can be sent into
   # verifysignature(). The example is included primarily to show command line
   # formatting. Messages are the same type as those generated by Bitcoin Core.
   # python armoryd.py verifysignature \"-----BEGIN BITCOIN SIGNED MESSAGE-----$'\n'Comment: Hello.$'\n'-----BEGIN BITCOIN SIGNATURE-----$'\n'$'\n'junkjunkjunk$'\n'-----END BITCOIN SIGNATURE-----\"
   @catchErrsForJSON
   def jsonrpc_verifysignature(self, *sigBlock):
      """
      DESCRIPTION:
      Take a message (RFC 2440: clearsign or Base64) signed by a Bitcoin address
      and verify the message.
      PARAMETERS:
      sigBlock - Message with the RFC 2440 message to be verified. The message
                 must be enclosed in quotation marks.
      RETURN:
      A dictionary with verified message and the Base58 address of the signer.
      """
      retDict = {}

      # We must deal with a couple of quirks. First, non-escaped spaces (i.e.,
      # spaces that aren't \u0020) will cause the CL parser to split the sig
      # into multiple lines. We need to combine the lines. Second, the quotation
      # marks used to prevent Armory from treating the sig like a CL arg need
      # to be removed. (NB: The final space must be stripped too.)
      signedMsg = (''.join((str(piece) + ' ') for piece in sigBlock))[1:-2]

      # Get the signature block's signature and message. The signature must be
      # formatted for clearsign or Base64 persuant to RFC 2440.
      return verifySignedMessage(signedMsg)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_walletlock(self):
      """
      DESCRIPTION:
      Lock a wallet.
      PARAMETERS:
      None
      RETURN:
      A string indicating whether or not the wallet is locked.
      """

      # Lock the wallet. It should lock but we'll check to be safe.
      self.curWlt.lock()
      retStr = 'Wallet is %slocked.' % '' if self.curWlt.isLocked() else 'not '
      return retStr


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_walletpassphrase(self, passphrase, timeout=10):
      """
      DESCRIPTION:
      Unlock a wallet with a given passphrase and unlock time length.
      PARAMETERS:
      passphrase - The wallet's current passphrase.
      timeout - (Default=10) The time, in seconds, that the wallet will be
                unlocked.
      RETURN:
      A string indicating if the wallet was unlocked or if it was already
      unlocked.
      """

      retStr = 'Wallet %s is already unlocked.' % self.curWlt.uniqueIDB58

      if self.curWlt.isLocked():
         self.sbdPassphrase = SecureBinaryData(str(passphrase))
         self.curWlt.unlock(self.sbdPassphrase, timeout=float(timeout))
         if self.curWlt.isLocked():
            retStr = 'Wallet %s failed to unlock' % self.curWlt.uniqueIDB58
         else:
            retStr = 'Wallet %s has been unlocked.' % self.curWlt.uniqueIDB58
         self.sbdPassphrase.destroy() # Ensure SBD is destroyed.

      return retStr


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
   @catchErrsForJSON
   def jsonrpc_watchwallet(self, send_from, smtpServer=None, password=None,
                           send_to=None, subject=None, watchCmd='add',
                           usebasic=False):
      """
      DESCRIPTION:
      Send an e-mail notification when the current wallet spends money.
      PARAMETERS:
      send_from - The email address of the sender.
      smtpServer - (Default=None) The SMTP email server.
      password - (Default=None) The email account password.
      send_to - (Default=None) The recipient or, if the string is delineated by
                a colon, a list of recipients.
      subject - (Default=None) The email subject.
      watchCmd - (Default=add) A string indicating if emails from the sender
                 should be sent or, if set to "remove", emails from the sender
                 that are currently being sent should be stopped.
      usebasic - (Default=false) Don't use TLS or password authentication
      RETURN:
      None
      """

      retStr = 'watchwallet command failed due to a bad command.'

      if not watchCmd in ['add', 'remove']:
         LOGERROR('Unrecognized watchwallet command: "%s"', watchCmd)
      else:
         send_to = send_to.split(":")

         # Write the funct to be run when a block arrives with a transaction
         # where a wallet has sent money.
         @EmailOutput(send_from, smtpServer, password,
                      send_to, subject, usebasic)
         def reportTxFromAddrInNewBlock(pyHeader, pyTxList):
            result = ''
            for pyTx in pyTxList:
               for pyTxIn in pyTx.inputs:
                  sendingAddrStr = TxInExtractAddrStrIfAvail(pyTxIn)
                  if len(sendingAddrStr) > 0:
                     sendingAddrHash160 = addrStr_to_hash160(sendingAddrStr,
                                                             False)[1]
                     if self.curWlt.hasAddr(sendingAddrHash160):
                        result += "%s\n" % sendingAddrStr
                        # add the metadata
                        metadata = self.addressMetaData.get(sendingAddrStr)
                        if metadata is not None:
                           result += "Metadata: %s\n" % metadata
                        result += pyTx.toString()
            return result

         # Add or remove e-mail functs based on the user's command.
         if watchCmd == 'add':
            rpc_server.newBlockFunctions[send_from].append(
               reportTxFromAddrInNewBlock)
         elif watchCmd == 'remove':
            rpc_server.newBlockFunctions[send_from] = []
         retStr = 'watchwallet command succeeded.'

      return retStr


# A dictionary that includes the names of all functions an armoryd user can
# call from the armoryd server. Implemented on the server side so that a client
# can know what exactly the server can run. See the note above regarding the
# docstring format.
jsonFuncDict = {}

# Now that we have completed the armoryd server class, let's build the
# dict that includes the functions clients can call, along with documentation.
# Be sure to use only functs with "jsonrpc_" at the start of the funct name (and
# also strip "jsonrpc_") and get the funct's docstring ("""Funct descrip"""),
# which will be extensively parsed to create the dict.

def createFuncDict():

   jFuncPrefix = "jsonrpc_"
   jFuncs = inspect.getmembers(ArmoryRPC,
                               predicate=inspect.ismethod)

   # Check only the applicable funcs.
   for curJFunc in jFuncs:
      if curJFunc[0].startswith(jFuncPrefix):
         # Remember to strip the prefix before using the func name.
         funcDoc = {}
         funcName = curJFunc[0][len(jFuncPrefix):]

         # Save the descrip/param/return data while stripping out the targeted
         # strings (e.g., "PARAMETERS:"). Also, filter out the empty string in
         # the resultant list, which should have three entries in the end.
         m = '[ \n]*DESCRIPTION:[ \n]*|[ \n]*PARAMETERS:[ \n]*|[ \n]*RETURN:[ \n]*'
         funcSplit = filter(None, re.split(m, str(curJFunc[1].__doc__)))

         if(len(funcSplit) != 3):
            jsonFuncDict[funcName] = {
               'Error': 'The funcion description is malformed.'}
            continue

         # While the help text is still together, perform the following steps.
         # Description:  Replace newlines & extra space w/ 1 space, then strip
         #               leading & trailing whitespace. (This allows params to
         #               be described over multiple lines.)
         # Parameters:   Strip extra whitespace.
         # Return Value: Replace newlines & extra space w/ 1 space, then strip
         #               leading & trailing whitespace. (This allows vals to be
         #               described over multiple lines.)
         funcSplit[0] = re.sub(r' *\n *', ' ', funcSplit[0]).strip()
         funcSplit[1] = funcSplit[1].strip()
         funcSplit[2] = re.sub(r' *\n *', ' ', funcSplit[2]).strip()

         # Create the return dict and param list, then populate the param list.
         # If the parameter entry is "None", just save it. If there are params,
         # perform the following steps.
         # - Split the param list while using the param name and the follow-up
         #   dash as the key, while saving the param name. The format must be
         #   "paramName - " in order for the code to work properly!!!
         # - Filter out the empty string in the resultant list.
         # - Split the resultant strings in two, with the param name in the
         #   first string and the description in the second string.
         # - For each description, replace newlines & extra space w/ 1 space,
         #   then strip leading & trailing whitespace. (This allows descips to
         #   be written over multiple lines.)
         # - Recreate & append to the param list a string w/ the param name &
         #   param descrip.
         funcDoc = {}
         funcParams = []
         if funcSplit[1] == 'None':
            funcParams.append(funcSplit[1])
         else:
            funcSplit2 = filter(None, (re.split(r'([^\s]+) - ',
                                                 funcSplit[1])))
            for pName, pDescrip in zip(funcSplit2, funcSplit2):
               pDescripClean = re.sub(r' *\n *', ' ', pDescrip).strip()
               pStr = '%s - %s' % (pName, pDescripClean)
               funcParams.append(pStr)

         # Save all the strings & lists in the func's dict. The code is written
         # to prevent numerical confusion that can occur from pops.
         funcDoc['Parameters'] = funcParams
         funcDoc['Return Value'] = funcSplit.pop(2)
         funcDoc['Description'] = funcSplit.pop(0)

         # Save the func's dict in the master dict to be returned to the user.
         jsonFuncDict[funcName] = funcDoc


################################################################################
# Utility function that takes a list of wallet paths, gets the paths and adds
# the wallets to a wallet set (actually a dictionary, with the wallet ID as the
# key and the wallet as the value), along with adding the wallet ID to a
# separate set.
def addMultWallets(inWltPaths):
   '''Function that adds multiple wallets to an armoryd server.'''
   ret = {}

   for aWlt in inWltPaths:
      # Logic basically taken from loadWalletsAndSettings()
      try:
         wltLoad = ArmoryWalletFile.ReadWalletFile(aWlt)
         for wlt in wltLoad.topLevelRoots:
            if isinstance(wlt, ABEK_BIP44Seed):
               for wallet in wlt.getAllWallets():
                  wltID = wallet.uniqueIDB58
                  LOGINFO("loading %s" % wltID)
                  existingWlt = ret.get(wltID)
                  if existingWlt:
                     if existingWlt.isWatchOnly and not wallet.isWatchOnly:
                        LOGINFO("found a better version of %s" % wltID)
                        ret[wltID] = wallet
                  else:
                     ret[wltID] = wallet
            elif isinstance(wlt, ABEK_StdWallet):
               wltID = wlt.uniqueIDB58
               LOGINFO("loading %s" % wltID)
               existingWlt = ret.get(wltID)
               if existingWlt:
                  if existingWlt.isWatchOnly and not wlt.isWatchOnly:
                     LOGINFO("found a better version of %s" % wltID)
                     ret[wltID] = wlt
               else:
                  ret[wltID] = wlt
            else:
               # TODO handle Armory135 types
               continue

      except:
         LOGEXCEPT('Unable to load wallet file %s. Skipping.' % aWlt)
         raise

   return ret


################################################################################
# Utility function that takes a list of lockbox paths, gets the paths and adds
# the lockboxes to a lockbox set (actually a dictionary, with the lockbox ID as
# the key and the lockbox as the value), along with adding the lockboxy ID to a
# separate set.
def addMultLockboxes(inLBPaths):
   '''Function that adds multiple lockboxes to an armoryd server.'''
   ret = {}
   for curLBFile in inLBPaths:
      try:
         curLBList = readLockboxesFile(curLBFile)
         for curLB in curLBList:
            lbID = curLB.uniqueIDB58
            if lbID in ret.keys():
               LOGINFO('Duplicate lockbox (%s) detected' % lbID)
            else:
               ret[lbID] = curLB
      except:
         LOGEXCEPT('Unable to load lockbox file %s. Skipping.' % curLBFile)
         raise

   return ret


def logUsageWarning():
   LOGWARN('*'*80)
   LOGWARN('* Please note that armoryd v%s is beta software and is still in '
           % getVersionString(BTCARMORY_VERSION))
   LOGWARN('* development. Whenever applicable, the interface is '
           'designed to match ')
   LOGWARN('* that of bitcoind, with function parameters and return '
           'values closely ')
   LOGWARN('* matching those of bitcoind. Despite this, the function '
           'parameters and ')
   LOGWARN('* return values may change, both for ported bitcoind '
           'function and ')
   LOGWARN('* Armory-specific functions.')
   LOGWARN('*'*80)
   LOGWARN('')
   LOGWARN('*'*80)
   LOGWARN('* WARNING!  WALLET FILE ACCESS IS NOT INTERPROCESS-SAFE!')
   LOGWARN('*           DO NOT run armoryd at the same time as '
           'ArmoryQt if ')
   LOGWARN('*           they are managing the same wallet file.  '
           'If you want ')
   LOGWARN('*           to manage the same wallet with both '
           'applications ')
   LOGWARN('*           you must make a digital copy/backup of the '
           'wallet file ')
   LOGWARN('*           into another directory and point armoryd at '
           'that one.  ')
   LOGWARN('*           ')
   LOGWARN('*           As long as the two processes do not share '
           'the same ')
   LOGWARN('*           actual file, there is no risk of wallet '
           'corruption. ')
   LOGWARN('*           Just be aware that addresses may end up '
           'being reused ')
   LOGWARN('*           if you execute transactions at approximately '
           'the same ')
   LOGWARN('*           time with both apps. ')
   LOGWARN('*')
   LOGWARN('*'*80)
   LOGWARN('')


################################################################################
class ArmoryDaemon(object):


   def __init__(self, wlt=None, lb=None):

      # NB: These objects contain ONLY wallet/lockbox data loaded at startup.
      # ArmoryRPC will contain the active wallet/LB lists.

      # WltMap:   wltID --> ArmoryWallet
      self.WltMap = {}

      # lboxMap:           lboxID --> MultiSigLockbox
      # lboxCppWalletMap:  lboxID --> Cpp.BtcWallet
      self.lboxMap = {}
      self.lboxCppWalletMap = {}

      self.curWlt = None
      self.curLB = None

      # Check if armoryd is already running. If so, just execute the command,
      # otherwise prepare to act as the server.
      armorydIsRunning = self.checkForAlreadyRunning()
      if armorydIsRunning == True:
         LOGERROR("It looks like armoryd is already running.\n"
                  "Please use armory-cli.py to query armoryd.\n")
         sys.exit()
      else:
         # Make sure we're actually able to do something before proceeding.
         if onlineModeIsPossible(getBDM().btcdir):
            self.lock = threading.Lock()
            self.lastChecked = None

            #check wallet consistency every hour
            self.checkStep = 3600

            ###################################################################
            # armoryd is still somewhat immature. We'll print a warning to let 
            # people know that armoryd is still beta software and that the API 
            # may change.
            logUsageWarning()

            # Otherwise, set up the server. This includes a defaultdict with a
            # list of functs to execute. This is done so that multiple functs
            # can be associated with the same search key.
            self.newTxFunctions = []
            self.heartbeatFunctions = []
            self.newBlockFunctions = defaultdict(list)

            self.settingsPath = getSettingsPath()
            self.settings = SettingsFile(self.settingsPath)

            # armoryd can take a default lockbox. If it's not passed in, load
            # some lockboxes.
            if lb:
               self.curLB = lb
            else:
               # Get the lockboxes in standard Armory LB file and store pointers
               # to them, assuming any exist.
               lbPaths = getLockboxFilePaths()
               self.lboxMap = addMultLockboxes(lbPaths)
               if len(self.lboxMap) > 0:
                  # Set the current LB to the 1st wallet in the set. (The choice
                  # is arbitrary.)
                  self.curLB = self.lboxMap[self.lboxMap.keys()[0]]

                  # Create the CPP wallet map for each lockbox.
                  for lbID,lbox in self.lboxMap.iteritems():
                     scraddrReg = script_to_scrAddr(lbox.binScript)
                     scraddrP2SH = script_to_scrAddr(
                        script_to_p2sh_script(lbox.binScript))
                     lockboxScrAddr = [scraddrReg, scraddrP2SH]

                     LOGWARN('Registering lockbox: %s' % lbID)
                     self.lboxCppWalletMap[lbID] = \
                      getBDM().registerLockbox(lbID, lockboxScrAddr)

               else:
                  LOGWARN('No lockboxes were loaded.')

            # armoryd can take a default wallet. If it's not passed in, load
            # some wallets.
            if wlt:
               self.curWlt = wlt
            else:
               # Get the wallets in the Armory data directory and store pointers
               # to them. Also, set the current wallet to the 1st wallet in the
               # set. (The choice is arbitrary.)
               wltPaths = readWalletFiles()
               self.WltMap = addMultWallets(wltPaths)
               if len(self.WltMap) > 0:
                  self.curWlt = self.WltMap[self.WltMap.keys()[0]]
                  self.WltMap[self.curWlt.uniqueIDB58] = self.curWlt
               else:
                  LOGERROR('No wallets could be loaded! armoryd will exit.')

            # Log info on the wallets we've loaded.
            numWallets = len(self.WltMap)
            LOGINFO('Number of wallets read in: %d', numWallets)
            for wltID, wlt in self.WltMap.iteritems():
               ds  = ('   Wallet (%s):' % wltID).ljust(25)
               ds += '"'+wlt.getLabel().ljust(32)+'"   '
               ds += '(Encrypted)' if wlt.useEncryption() else '(No Encryption)'
               LOGINFO(ds)

            # Log info on the lockboxes we've loaded.
            numLockboxes = len(self.lboxMap)
            LOGINFO('Number of lockboxes read in: %d', numLockboxes)
            for lockboxID, lockbox in self.lboxMap.iteritems():
               dispStr  = ('   Lockbox (%s):' % lockboxID).ljust(25)
               dispStr += '"' + lockbox.shortName.ljust(32) + '"'
               LOGINFO(dispStr)

            # Check and make sure we have at least 1 wallet. If we don't, stop
            # immediately.
            if numWallets > 0:
               LOGWARN('Active wallet is set to %s' % self.curWlt.uniqueIDB58)
            else:
               os._exit(0)

            # Check to see if we have 1+ lockbox. If so, log the active one.
            if numLockboxes > 0:
               LOGWARN('Active lockbox is set to %s' % self.curLB.uniqueIDB58)

            LOGINFO("Initialising RPC server on port %d", getRPCPort())
            self.resource = ArmoryRPC(
               self.curWlt, self.curLB, self.WltMap, self.lboxMap,
               self.lboxCppWalletMap)
            secured_resource = self.set_auth(self.resource)

            # This is LISTEN call for armory RPC server
            reactor.listenTCP(getRPCPort(),
                              server.Site(secured_resource),
                              interface="127.0.0.1")

            # Setup the heartbeat function to run every
            reactor.callLater(3, self.Heartbeat)
         else:
            errStr = 'armoryd is not ready to run! Please check to see if ' \
                     'bitcoind is running and the Blockchain files ' \
                     '(blk*.dat) are available.'
            LOGERROR(errStr)
            os._exit(0)

   #############################################################################
   def handleCppNotification(self, action, args):

      if action == FINISH_LOAD_BLOCKCHAIN_ACTION:
         #Blockchain just finished loading, finish initializing UI and render the
         #ledgers

         self.timeReceived = getBDM().bdv().blockchain().top().getTimestamp()
         self.latestBlockNum = getBDM().bdv().blockchain().top().getBlockHeight()
         LOGINFO('Blockchain loaded. Wallets synced!')
         LOGINFO('Current block number: %d', self.latestBlockNum)
         LOGINFO('Current block received at: %d', self.timeReceived)
         LOGINFO('Wallet balance: %s' %
                 coin2str(self.curWlt.getBalance('Spendable')))

         # This is CONNECT call for armoryd to talk to bitcoind
         LOGINFO('Set up connection to bitcoind')
         self.NetworkingFactory = ArmoryClientFactory(
            getBDM(),
            func_loseConnect = self.showOfflineMsg,
            func_madeConnect = self.showOnlineMsg,
            func_newTx       = self.execOnNewTx,
            func_newBlock    = self.execOnNewBlock)

         reactor.connectTCP('127.0.0.1', getBitcoinPort(), self.NetworkingFactory)
         # give access to the networking factory from json-rpc listener
         self.resource.NetworkingFactory = self.NetworkingFactory

      elif action == NEW_ZC_ACTION:
         # for zero-confirmation transcations, do nothing for now.
         print 'New ZC'
         for le in args:
            wltID = le.getWalletID()
            if wltID in self.WltMap:
               print '   Wallet: %s, amount: %d' % (wltID, le.getValue())
            elif wltID in self.lboxMap:
               print '   Lockbox: %s, amount: %d' % (wltID, le.getValue())

      elif action == NEW_BLOCK_ACTION:
         # A new block has appeared, pull updated ledgers from the BDM, display
         # the new block height in the status bar and note the block received
         # time

         newBlocks = args[0]
         if newBlocks>0:
            highest = getBDM().getTopBlockHeight()
            LOGINFO('New Block! : %d', highest)

            self.blkReceived  = time.time()
            self.writeSetting('LastBlkRecvTime', self.blkReceived)
            self.writeSetting('LastBlkRecv',     getBDM().getTopBlockHeight())

            # If there are no new block functions to run, just skip all this.
            if len(self.newBlockFunctions) > 0:
               # Here's where we actually execute the new-block calls, because
               # this code is guaranteed to execute AFTER the getBDM() has 
               # processed the new block data.
               # We walk through headers by block height in case the new block
               # didn't extend the main chain (this won't run), or there was a
               # reorg with multiple blocks and we only want to process the new
               # blocks on the main chain, not the invalid ones
               prevTopBlock = highest - newBlocks
               for blknum in range(newBlocks):
                  cur = prevTopBlock + blknum + 1
                  cppHeader = getBDM().bdv().blockchain().getHeaderByHeight(cur)
                  pyHeader = PyBlockHeader().unserialize(cppHeader.serialize())

                  cppBlock = getBDM().bdv().getMainBlockFromDB(cur)
                  pyTxList = [
                     PyTx().unserialize(getBDM().getTxByHash(
                        hex_to_binary(txhash, BIGENDIAN)).serialize())
                     for txhash in cppBlock['txHashList']]
                  for funcKey in self.newBlockFunctions:
                     for blockFunc in self.newBlockFunctions[funcKey]:
                        blockFunc(pyHeader, pyTxList)

      elif action == REFRESH_ACTION:
         #The wallet ledgers have been updated from an event outside of new ZC
         #or new blocks (usually a wallet or address was imported, or the
         #wallet filter was modified
         for wltID in args:
            if len(wltID) > 0:
               if wltID in self.WltMap:
                  self.WltMap[wltID].doAfterScan()
                  self.WltMap[wltID].isDisabled = False
               else:
                  if wltID not in self.lboxMap:
                     raise RuntimeError(
                        "cpp says %s exists, but armoryd can't find it" % wltID)
                  self.lboxMap[wltID].isDisabled = False

               #no progress repoting in armoryd yet
               #del self.walletSideScanProgress[wltID]

      elif action == 'progress':
         #Received progress data for a wallet side scan
         wltID = args[0]
         prog = args[1]

      elif action == WARNING_ACTION:
         #something went wrong on the C++ side, create a message box to report
         #it to the user
         LOGWARN("BlockDataManager Warning: ")
         LOGWARN(args[0])


   #############################################################################
   def writeSetting(self, settingName, val):
      self.settings.set(settingName, val)

   #############################################################################
   def set_auth(self, resource):
      passwordfile = getArmoryDConfFile()
      # Create User Name & Password file to use locally
      if not os.path.exists(passwordfile):
         with open(passwordfile,'a') as f:
            # Don't wait for Python or the OS to write the file. Flush buffers.
            try:
               genVal = SecureBinaryData().GenerateRandom(32)
               f.write('generated_by_armory:%s'
                       % binary_to_base58(genVal.toBinStr()))
               f.flush()
               os.fsync(f.fileno())
            finally:
               genVal.destroy()

      checker = FilePasswordDB(passwordfile)
      realmName = "Armory JSON-RPC App"
      wrapper = wrapResource(resource, [checker], realmName=realmName)
      return wrapper

   def start(self):
      #run a wallet consistency check before starting the BDM
      self.checkWallet()

      #try to grab checkWallet lock to block start() until the check is over
      self.lock.acquire()
      self.lock.release()

      #register callback
      getBDM().registerCppNotification(self.handleCppNotification)

      # This is not a UI so no need to worry about the main thread being
      # blocked. Any UI that uses this Daemon can put the call to the Daemon on
      # its own thread.
      LOGWARN('Server started...')

      # Put the BDM in online mode only after registering all Python wallets.
      for wltID, wlt in self.WltMap.iteritems():
         LOGWARN('Registering wallet: %s' % wltID)
         wlt.registerWallet()
      getBDM().goOnline()
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
         sock = socket.create_connection(('127.0.0.1', getRPCPort()), 0.1);
      except socket.error:
         LOGINFO("No other armoryd.py instance is running.  We're the first. %d"
                 % getRPCPort())
         retVal = False

      # Clean up the socket and return the result.
      sock.close()
      return retVal


   #############################################################################
   def execOnNewTx(self, pytxObj):
      # Execute on every new Tx.
      getBDM().bdv().addNewZeroConfTx(pytxObj.serialize(), long(time.time()), True)

      # Add anything else you'd like to do on a new transaction.
      for txFunc in self.newTxFunctions:
         txFunc(pytxObj)


   #############################################################################
   def execOnNewBlock(self, pyHeader, pyTxList):
      # DO NOT PUT ANY FUNCTION HERE THAT EXPECT getBDM() TO BE UP TO DATE
      # WITH THE NEW BLOCK!  ONLY CALL FUNCTIONS THAT OPERATE PURELY ON
      # THE NEW HEADER AND TXLIST WITHOUT getBDM().

      # Any functions that you want to execute on new blocks should go in
      # the "if newBlocks>0: ... " clause in the Heartbeat function, below

      # Armory executes newBlock functions in the readBlkFileUpdate()
      # which occurs in the heartbeat function.  execOnNewBlock() may be
      # called before readBlkFileUpdate() has run, and thus getBDM() may
      # not have the new block data yet. (There's a variety of reason for
      # this design decision, I can enumerate them for you in an email....)
      # If you need to execute anything, execute after readBlkFileUpdate().

      # Therefore, if you put anything here, it should operate on the header
      # or tx data in a vacuum (without any reliance on getBDM())
      pass


   #############################################################################
   def showOfflineMsg(self):
      LOGINFO('Offline - not tracking blockchain')


   #############################################################################
   def showOnlineMsg(self):
      LOGINFO('Online - tracking blockchain')

   #############################################################################
   @AllowAsync
   def checkWallet(self):

      if isinstance(self.curWlt, WalletEntry):
         self.lastChecked = time.time()
         return
      if self.lock.acquire(False):
         self.lastChecked = time.time()

      self.lock.release()


   #############################################################################
   def Heartbeat(self, nextBeatSec=1):
      """
      This method is invoked when the app is initialized, and will
      run every 2 seconds, or whatever is specified in the nextBeatSec
      argument.
      """

      try:

         for wltID,wlt in self.WltMap.iteritems():
            wlt.checkLockTimeout()

         # Check for new blocks in the latest blk0XXXX.dat file.
         if getBDM().getState() == BDM_BLOCKCHAIN_READY:
            #check wallet every checkStep seconds
            nextCheck = self.lastChecked + self.checkStep
            if time.time() >= nextCheck:
               self.checkWallet()

      except:
         # When getting the error info, don't collect the traceback in order to
         # avoid circular references. https://docs.python.org/2/library/sys.html
         # has more info.
         LOGEXCEPT('Error in heartbeat function')
         (errType, errVal) = sys.exc_info()[:2]
         LOGERROR('Error Type: %s' % errType)
         LOGERROR('Error Value: %s' % errVal)
      finally:
         reactor.callLater(nextBeatSec, self.Heartbeat)


if __name__ == "__main__":
   initializeArmory()
   createFuncDict()
   rpc_server = ArmoryDaemon()
   rpc_server.start()
