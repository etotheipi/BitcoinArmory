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

import decimal
import base64
import json

from twisted.cred.checkers import FilePasswordDB
from twisted.internet import reactor
from twisted.web import server
from twisted.internet.protocol import ClientFactory # REMOVE IN 0.93
from txjsonrpc.auth import wrapResource
from txjsonrpc.web import jsonrpc

from armoryengine.ALL import *
from collections import defaultdict
from itertools import islice
from armoryengine.Decorators import EmailOutput, catchErrsForJSON
from armoryengine.PyBtcWalletRecovery import *
from inspect import *
from jasvet import readSigBlock, verifySignature
from CppBlockUtils import BtcWallet

# Some non-twisted json imports from jgarzik's code and his UniversalEncoder
class UniversalEncoder(json.JSONEncoder):
   def default(self, obj):
      if isinstance(obj, decimal.Decimal):
         return float(obj)
      return json.JSONEncoder.default(self, obj)

ARMORYD_CONF_FILE = os.path.join(ARMORY_HOME_DIR, 'armoryd.conf')


# Define some specific errors that can be thrown and caught
class UnrecognizedCommand(Exception): pass
class NotEnoughCoinsError(Exception): pass
class CoinSelectError(Exception): pass
class WalletUnlockNeeded(Exception): pass
class InvalidBitcoinAddress(Exception): pass
class PrivateKeyNotFound(Exception): pass
class WalletDoesNotExist(Exception): pass
class LockboxDoesNotExist(Exception): pass
class AddressNotInWallet(Exception): pass

# A dictionary that includes the names of all functions an armoryd user can
# call from the armoryd server. Implemented on the server side so that a client
# can know what exactly the server can run. See the note above regarding the
# docstring format.
jsonFunctDict = {}

NOT_IMPLEMENTED = '--Not Implemented--'

############################################
# Copied from ArmoryQt. Remove in 0.93.
class armorydInstanceListener(Protocol):
   def connectionMade(self):
      LOGINFO('Another armoryd instance just tried to open.')
      self.factory.func_conn_made()

   def dataReceived(self, data):
      LOGINFO('Received data from alternate armoryd instance')
      self.factory.func_recv_data(data)
      self.transport.loseConnection()


############################################
# Copied from ArmoryQt. Remove in 0.93.
class armorydListenerFactory(ClientFactory):
   protocol = armorydInstanceListener
   def __init__(self, fn_conn_made, fn_recv_data):
      self.func_conn_made = fn_conn_made
      self.func_recv_data = fn_recv_data


#############################################################################
# Helper function from ArmoryQt. Check to see if we can go online.
# (NB: Should be removed in 0.93 and combined w/ ArmoryQt code.)
def onlineModeIsPossible(internetAvail, forceOnline):
   canGoOnline = True
   if not forceOnline:
      satoshiIsAvailableResult = satoshiIsAvailable()
      hasBlockFiles = checkHaveBlockfiles()
      canGoOnline = internetAvail and satoshiIsAvailableResult and hasBlockFiles
      
      LOGINFO('Internet connection is Available: %s', str(internetAvail))
      LOGINFO('Bitcoin-Qt/bitcoind is Available: %s', satoshiIsAvailableResult)
      LOGINFO('The first blk*.dat was Available: %s', str(hasBlockFiles))
      LOGINFO('Online mode currently possible:   %s', canGoOnline)
   return canGoOnline


#############################################################################
# Helper function from ArmoryQt. Check to see if we have the blk*.dat files.
# (NB: Should be removed in 0.93 and combined w/ ArmoryQt code.)
def checkHaveBlockfiles():
   return os.path.exists(os.path.join(TheBDM.btcdir, 'blocks'))


#############################################################################
# Check to see if an Internet connection is available. Code lifted from
# ArmoryQt. (NB: Should be removed in 0.93 and combined w/ ArmoryQt code.)
# (AO: There are many lines from the original code in ArmoryQt including 
# some that i have just removed. I have removed them rather than comment them
# out to reduce the amount of commented code in the repo. If you want to see
# what I removed compare the revisions and/or refer to ArmoryQt.)
def setupNetworking():
   LOGINFO('Setting up networking...')
   forceOnline = CLI_OPTIONS.forceOnline
   if forceOnline:
      LOGINFO('Forced online mode: True')

   # Check general internet connection
   internetAvail = False
   if not forceOnline:
      try:
         import urllib2
         response=urllib2.urlopen('http://google.com', \
                                  timeout=CLI_OPTIONS.nettimeout)
         internetAvail = True
      except ImportError:
         LOGERROR('No module urllib2 -- cannot determine if internet is ' \
                  'available')
      except urllib2.URLError:
         # In the extremely rare case that google might be down (or just to try
         # again...)
         try:
            response=urllib2.urlopen('http://microsoft.com', \
                                     timeout=CLI_OPTIONS.nettimeout)
         except:
            LOGEXCEPT('Error checking for internet connection')
            LOGERROR('Run --skip-online-check if you think this is an error')
            internetAvail = False
      except:
         LOGEXCEPT('Error checking for internet connection')
         LOGERROR('Run --skip-online-check if you think this is an error')
         internetAvail = False

   return onlineModeIsPossible(internetAvail, forceOnline)


################################################################################
# Utility function that takes a list of wallet paths, gets the paths and adds
# the wallets to a wallet set (actually a dictionary, with the wallet ID as the
# key and the wallet as the value), along with adding the wallet ID to a
# separate set.
def addMultWallets(inWltPaths, inWltMap, inWltIDSet):
   '''Function that adds multiple wallets to an armoryd server.'''
   newWltList = []

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
            wo1 = inWltMap[wltID].watchingOnly
            wo2 = wltLoad.watchingOnly
            if wo1 and not wo2:
               prevWltPath = inWltMap[wltID].walletPath
               inWltMap[wltID] = wltLoad
               LOGWARN('First wallet is more useful than the second one...')
               LOGWARN('     Wallet 1 (loaded):  %s', aWlt)
               LOGWARN('     Wallet 2 (skipped): %s', prevWltPath)
            else:
               LOGWARN('Second wallet is more useful than the first one...')
               LOGWARN('     Wallet 1 (skipped): %s', aWlt)
               LOGWARN('     Wallet 2 (loaded):  %s', \
                       inWltMap[wltID].walletPath)
         else:
            # Update the wallet structs.
            inWltMap[wltID] = wltLoad
            inWltIDSet.add(wltID)
            newWltList.append(wltID)
      except:
         LOGEXCEPT('***WARNING: Unable to load wallet %s. Skipping.', aWlt)
         raise

   return newWltList


################################################################################
# Utility function that takes a list of lockbox paths, gets the paths and adds
# the lockboxes to a lockbox set (actually a dictionary, with the lockbox ID as
# the key and the lockbox as the value), along with adding the lockboxy ID to a
# separate set.
def addMultLockboxes(inLBPaths, inLboxMap, inLBIDSet):
   '''Function that adds multiple lockboxes to an armoryd server.'''
   newLBList = []

   for curLBFile in inLBPaths:
      try:
         curLBList = readLockboxesFile(curLBFile)
         for curLB in curLBList:
            lbID = curLB.uniqueIDB58
            if lbID in inLBIDSet:
               LOGINFO('***WARNING: Duplicate lockbox (%s) detected' % lbID)
            else:
               inLboxMap[lbID] = curLB
               inLBIDSet.add(lbID)
               newLBList.append(lbID)
      except:
         LOGEXCEPT('***WARNING: Unable to load lockbox file %s. Skipping.', \
                   curLBFile)
         raise

   return newLBList


class Armory_Json_Rpc_Server(jsonrpc.JSONRPC):
   #############################################################################
   def __init__(self, wallet, lockbox=None, inWltMap=None, inLBMap=None, \
                inWltIDSet=None, inLBIDSet=None, inLBCppWalletMap=None, \
                armoryHomeDir=ARMORY_HOME_DIR, addrByte=ADDRBYTE):
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
      if inWltIDSet == None:
         inWltIDSet = set()
      if inLBMap == None:
         inLBMap = {}
      if inLBIDSet == None:
         inLBIDSet = set()
      if inLBCppWalletMap == None:
         inLBCppWalletMap = {}
      self.serverWltMap = inWltMap                 # Dict
      self.serverWltIDSet = inWltIDSet             # set()
      self.serverLBMap = inLBMap                   # Dict
      self.serverLBIDSet = inLBIDSet               # set()
      self.serverLBCppWalletMap = inLBCppWalletMap # Dict

      self.armoryHomeDir = armoryHomeDir
      if wallet != None:
         wltID = wallet.uniqueIDB58
         if self.serverWltMap.get(wltID) == None:
            self.serverWltMap[wltID] = wallet

      # If any variables rely on whether or not Testnet in a Box is running,
      # we'll set everything up here.
      self.addrByte = addrByte


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_receivedfromsigner(self, *sigBlock):
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

      verification = self.jsonrpc_verifysignature(signedMsg)
      retDict['message'] = verification['message']
      retDict['amount'] = self.jsonrpc_receivedfromaddress(verification['address'])

      return retDict


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
      sig, msg = readSigBlock(signedMsg)
      retDict['message'] = msg
      addrB58 = verifySignature(sig, msg, 'v1', ord(self.addrByte) )
      retDict['address'] = addrB58

      return retDict


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_receivedfromaddress(self, sender):
      """
      DESCRIPTION:
      Return the number of coins received from a particular sender.
      PARAMETERS:
      sender - Base58 address of the sender to the current wallet.
      RETURN:
      Number of Bitcoins sent by the sender to the current wallet.
      """
      totalReceived = 0.0
      ledgerEntries = self.curWlt.getTxLedger('blk')

      for entry in ledgerEntries:
         cppTx = TheBDM.getTxByHash(entry.getTxHash())
         if cppTx.isInitialized():
            # Only consider the first for determining received from address
            # This function should assume it is online, and actually request the previous
            # TxOut script from the BDM -- which guarantees we know the sender.  
            # Use TheBDM.getSenderScrAddr(txin).  This takes a C++ txin (which we have)
            # and it will grab the TxOut being spent by that TxIn and return the
            # scraddr of it.  This will succeed 100% of the time.
            cppTxin = cppTx.getTxInCopy(0)
            txInAddr = scrAddr_to_addrStr(TheBDM.getSenderScrAddr(cppTxin))
            fromSender =  sender == txInAddr

            if fromSender:
               txBinary = cppTx.serialize()
               pyTx = PyTx().unserialize(txBinary)
               for txout in pyTx.outputs:
                  if self.curWlt.hasAddr(script_to_addrStr(txout.getScript())):
                     totalReceived += txout.value

      return AmountToJSON(totalReceived)


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
          retVal = {}
          retVal['Error'] = 'File %s already exists. Will not overwrite.' % \
                            backupFilePath
      else:
          if not self.curWlt.backupWalletFile(backupFilePath):
             # If we have a failure here, we probably won't know why. Not much
             # to do other than ask the user to check the armoryd server.
             retVal['Error'] = "Backup failed. Check the armoryd server logs."
          else:
             retVal['Result'] = "Backup succeeded."

      return retVal


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

      # Return a dictionary with a string as the key and a wallet B58 value as
      # the value.
      utxoList = self.curWlt.getTxOutList('unspent')
      utxoOutList = {}
      curTxOut = 0
      totBal = 0
      utxoOutList = []

      if TheBDM.getBDMState()=='BlockchainReady':
         for u in utxoList:
            curUTXODict = {}
            curTxOut += 1

            curTxOutStr = 'utxo%05d' % curTxOut
            utxoVal = AmountToJSON(u.getValue())
            curUTXODict['txid'] = binary_to_hex(u.getOutPoint().getTxHash(), \
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

            utxoOutList.append(curUTXODict)
            totBal += utxoVal
      else:
         LOGERROR('Blockchain not ready. Values will not be reported.')

      # Maybe we'll add more later, but for now, return what we have.
      return utxoOutList


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
      topBlk = TheBDM.getTopBlockHeight()
      addrBalanceMap = {}
      utxoEntries = []
      for addrStr in addrList:

         # For now, prevent the caller from accidentally inducing a 20 min rescan
         # If they want the unspent list for a non-registered addr, they can
         # explicitly register it and rescan before calling this method.
         if not TheBDM.scrAddrIsRegistered(addrStr_to_scrAddr(addrStr)):
            raise BitcoindError('Address is not registered, requires rescan')

         atype,a160 = addrStr_to_hash160(addrStr)
         if atype==ADDRBYTE:
            # Already checked it's registered, regardless if in a loaded wallet
            utxoList = getUnspentTxOutsForAddr160List([a160], 'spendable', 0)
         elif atype==P2SHBYTE:
            # For P2SH, we'll require we have a loaded lockbox
            lbox = self.getLockboxByP2SHAddrStr(addrStr)
            if not lbox:
               raise BitcoindError('Import lockbox before getting P2SH unspent')

            # We simply grab the UTXO list for the lbox, both p2sh and multisig
            cppWallet = self.serverLBCppWalletMap[lbox.uniqueIDB58]
            utxoList = cppWallet.getSpendableTxOutList(topBlk, IGNOREZC)
         else:
            raise NetworkIDError('Addr for the wrong network!')

         # Place each UTXO in the return dict. Each entry should specify which
         # address is associated with which UTXO.
         # (DR: For 0.93, this ought to be merged with the listunspent code, and
         # maybe moved around a bit to make the info easier to process.)
         utxoListBal = 0
         for u in utxoList:
            curTxOut += 1
            curUTXODict = {}

            # Get the UTXO info.
            curTxOutStr = 'utxo%05d' % curTxOut
            utxoVal = AmountToJSON(u.getValue())
            curUTXODict['txid'] = binary_to_hex(u.getOutPoint().getTxHash(), \
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

            utxoEntries.append(curUTXODict)
            totalTxOuts += 1
            utxoListBal += u.getValue()
            totalBal    += u.getValue()

         # Add up the UTXO balances for each address and add it to the UTXO
         # entry dict, then add the UTXO entry dict to the master dict.
         addrBalanceMap[addrStr] = AmountToJSON(utxoListBal)

      # Let's round out the master dict with more info.
      utxoDict['utxolist']     = utxoEntries
      utxoDict['numutxo']      = totalTxOuts
      utxoDict['addrbalance']  = addrBalanceMap
      utxoDict['totalbalance'] = AmountToJSON(totalBal)

      return utxoDict


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

      # Convert string to binary
      retDict = {}
      privKey = str(privKey)
      privKeyValid = True
      if self.curWlt.useEncryption and self.curWlt.isLocked:
         raise WalletUnlockNeeded

      # Make sure the key is one we can support
      try:
         self.binPrivKey, self.privKeyType = parsePrivateKeyData(privKey)
      except:
         (errType, errVal) = sys.exc_info()[:2]
         LOGEXCEPT('Error parsing incoming private key.')
         LOGERROR('Error Type: %s' % errType)
         LOGERROR('Error Value: %s' % errVal)
         retDict['Error'] = 'Error type %s while parsing incoming private ' \
                            'key.' % errType
         privKeyValid = False

      if privKeyValid:
         self.thePubKey = self.curWlt.importExternalAddressData(self.binPrivKey)
         if self.thePubKey != None:
            retDict['PubKey'] = binary_to_hex(self.thePubKey)
         else:
            LOGERROR('Attempt to import a private key failed.')
            retDict['Error'] = 'Attempt to import your private key failed. ' \
                               'Check if the key is already in your wallet.'
      return retDict


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
   @catchErrsForJSON
   def jsonrpc_gettxout(self, txHash, n, binary=0):
      """
      DESCRIPTION:
      Get the TxOut entries for a given transaction hash.
      PARAMETERS:
      txHash - A string representing the hex value of a transaction ID.
      n - The TxOut index to obtain.
      binary - (Default=0) Indicates whether or not the resultant binary script
               should be in binary form or converted to a hex string.
      RETURN:
      A dictionary with the Bitcoin amount for the TxOut and the TxOut script in
      hex string form (default) or binary form.
      """

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
   @catchErrsForJSON
   def jsonrpc_encryptwallet(self, passphrase):
      """
      DESCRIPTION:
      Encrypt a wallet with a given passphrase.
      PARAMETERS:
      passphrase - The wallet's new passphrase.
      RETURN:
      A string indicating that the encryption was successful.
      """

      retStr = 'Wallet %s has been encrypted.' % self.curWlt.uniqueIDB58

      if self.curWlt.isLocked:
         raise WalletUnlockNeeded
      else:
         try:
            self.sbdPassphrase = SecureBinaryData(str(passphrase))
            self.curWlt.changeWalletEncryption(securePassphrase=self.sbdPassphrase)
            self.curWlt.lock()
         finally:
            self.sbdPassphrase.destroy() # Ensure SBD is destroyed.

      return retStr


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_unlockwallet(self, passphrase, timeout=10):
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

      retStr = 'Wallet %s is already unlocked.' % self.curWlt

      if self.curWlt.isLocked:
         try:
            self.sbdPassphrase = SecureBinaryData(str(passphrase))
            self.curWlt.unlock(securePassphrase=self.sbdPassphrase,
                               tempKeyLifetime=int(timeout))
            retStr = 'Wallet %s has been unlocked.' % self.curWlt.uniqueIDB58
         finally:
            self.sbdPassphrase.destroy() # Ensure SBD is destroyed.

      return retStr


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_relockwallet(self):
      """
      DESCRIPTION:
      Re-lock a wallet.
      PARAMETERS:
      None
      RETURN:
      A string indicating whether or not the wallet is locked.
      """

      # Lock the wallet. It should lock but we'll check to be safe.
      self.curWlt.lock()
      retStr = 'Wallet is %slocked.' % '' if self.curWlt.isLocked else 'not '
      return retStr


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
                            'scriptAddrStrs' : self.getScriptAddrStrs(txout) } )


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
   def jsonrpc_getnewaddress(self):
      """
      DESCRIPTION:
      Get a new Base58 address from the currently loaded wallet.
      PARAMETERS:
      None
      RETURN:
      The wallet's next unused public address in Base58 form.
      """

      addr = self.curWlt.getNextUnusedAddress()
      return addr.getAddrStr()


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_dumpprivkey(self, addr58):
      """
      DESCRIPTION:
      Dump the private key for a given Base58 address associated with the
      currently loaded wallet.
      PARAMETERS:
      addr58 - A Base58 public address associated with the current wallet.
      RETURN:
      The 32 byte binary private key.
      """

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

      return binary_to_hex(pyBtcAddress.serializePlainPrivateKey())


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
      self.isReady = TheBDM.getBDMState() == 'BlockchainReady'
      self.wltToUse = self.curWlt

      # If we're not getting info on the currently loaded wallet, check to make
      # sure the incoming wallet ID points to an actual wallet.
      if inWltID:
         if self.serverWltIDSet[inWltID] != None:
            self.wltToUse = self.serverWltMap[inWltID]
         else:
            raise WalletDoesNotExist

      return self.wltToUse.toJSONMap()


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getbalance(self, baltype='spendable'):
      """
      DESCRIPTION:
      Get the balance of the currently loaded wallet.
      PARAMETERS:
      baltype - (Default=spendable) A string indicating the balance type to
                retrieve from the current wallet.
      RETURN:
      The current wallet balance (BTC), or -1 if an error occurred.
      """

      retVal = -1

      # Proceed only if the blockchain's good. Wallet value could be unreliable
      # otherwise.
      if TheBDM.getBDMState()=='BlockchainReady':
         if not baltype in ['spendable', 'spend', 'unconf', 'unconfirmed', \
                            'total', 'ultimate', 'unspent', 'full']:
            LOGERROR('Unrecognized getbalance string: "%s"', baltype)
         else:
            retVal = AmountToJSON(self.curWlt.getBalance(baltype))
      else:
         LOGERROR('Blockchain not ready. Values will not be reported.')

      return retVal


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

      retVal = -1

      if not baltype in ['spendable','spend', 'unconf', 'unconfirmed', \
                         'ultimate','unspent', 'full']:
         raise BadInputError('Unrecognized getaddrbalance type: %s' % baltype) 


      topBlk = TheBDM.getTopBlockHeight()
      addrList = [a.strip() for a in inB58.split(",")] 
      retBalance = 0
      for addrStr in addrList:
      
         if not TheBDM.scrAddrIsRegistered(addrStr_to_scrAddr(addrStr)):
            raise BitcoindError('Address is not registered, requires rescan')

         atype,a160 = addrStr_to_hash160(addrStr)
         if atype==ADDRBYTE:
            # Already checked it's registered, regardless if in a loaded wallet
            utxoList = getUnspentTxOutsForAddr160List([a160], baltype, 0)
         elif atype==P2SHBYTE:
            # For P2SH, we'll require we have a loaded lockbox
            lbox = self.getLockboxByP2SHAddrStr(addrStr)
            if not lbox:
               raise BitcoindError('Import lockbox before getting P2SH unspent')

            # We simply grab the UTXO list for the lbox, both p2sh and multisig
            cppWallet = self.serverLBCppWalletMap[lbox.uniqueIDB58]
            utxoList = cppWallet.getSpendableTxOutList(topBlk, IGNOREZC)
         else:
            raise NetworkIDError('Addr for the wrong network!')

         retBalance += sumTxOutList(utxoList)

      return AmountToJSON(retBalance)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getreceivedbyaddress(self, address):
      """
      DESCRIPTION:
      Get the number of coins received by a Base58 address associated with
      the currently loaded wallet.
      PARAMETERS:
      address - The Base58 address associated with the current wallet.
      RETURN:
      The balance received from the incoming address (BTC).
      """

      if CLI_OPTIONS.offline:
         raise ValueError('Cannot get received amount when offline')
      # Only gets correct amount for addresses in the wallet, otherwise 0
      addr160 = addrStr_to_hash160(address, False)[1]

      txs = self.curWlt.getAddrTxLedger(addr160)
      balance = sum([x.getValue() for x in txs if x.getValue() > 0])
      return AmountToJSON(balance)


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_createustxtoaddress(self, recAddr, amount):
      """
      DESCRIPTION:
      Create an unsigned transaction to be sent to one recipient from the
      currently loaded wallet.
      PARAMETERS:
      recAddr - The recipient. This can be an address, a P2SH script address, a
                lockbox (e.g., "Lockbox[83jcAqz9]" or "Lockbox[Bare:83jcAqz9]"),
                or a public key (compressed or uncompressed) string.
      amount - The number of Bitcoins to send to the recipient.
      RETURN:
      An ASCII-formatted unsigned transaction, similar to the one output by
      Armory for offline signing.
      """

      if CLI_OPTIONS.offline:
         raise ValueError('Cannot create transactions when offline')
      ustxScr = getScriptForUserString(recAddr, self.serverWltMap, \
                                       self.convLBDictToList())
      amtCoin = JSONtoAmount(amount)
      return self.create_unsigned_transaction([[str(ustxScr['Script']), \
                                                amtCoin]])


   #############################################################################
   # Create an unsigned Tx to be sent from the currently loaded wallet.
   #
   # Example: We wish to send 1 BTC to a lockbox and 0.12 BTC to a standard
   # Bitcoin address. (Publick keys and P2SH scripts can also be specified as
   # recipients but we don't use either one in this example.)
   # armoryd createustxformany Lockbox[83jcAqz9],1.0 mwpw68XWmvQKfsCJXETkDX2CWHPdchY6fi,0.12
   @catchErrsForJSON
   def jsonrpc_createustxformany(self, *args):
      """
      DESCRIPTION:
      Create an unsigned transaction to be sent to multiple recipients from
      the currently loaded wallet.
      PARAMETERS:
      args - An indefinite number of comma-separated sets of recipients and the
             number of Bitcoins to send to the recipients. The recipients can be
             an address, a P2SH script address, a lockbox (e.g.,
             "Lockbox[83jcAqz9]" or "Lockbox[Bare:83jcAqz9]"), or a public key
             (compressed or uncompressed) string.
      RETURN:
      An ASCII-formatted unsigned transaction, similar to the one output by
      Armory for offline signing.
      """

      if CLI_OPTIONS.offline:
         raise ValueError('Cannot create transactions when offline')

      scriptValuePairs = []
      for a in args:
         r,v = a.split(',')
         ustxScr = getScriptForUserString(r, self.serverWltMap, \
                                          self.convLBDictToList())
         scriptValuePairs.append([ustxScr['Script'], JSONtoAmount(v)])

      return self.create_unsigned_transaction(scriptValuePairs)


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
   def jsonrpc_getledger(self, inB58ID, tx_count=10, from_tx=0, simple=False):
      """
      DESCRIPTION:
      Get a wallet or lockbox ledger.
      inB58ID - The Base58 ID of the wallet or lockbox from which to obtain the
                ledger. The wallet or lockbox must already be loaded.
      tx_count - (Default=10) The number of entries to get.
      from_tx - (Default=0) The first entry to get.
      simple - (Default=False) Flag indicating if the returned ledger should be
               simple in format.
      RETURN:
      A ledger list with dictionary entries for each transaction.
      """

      final_le_list = []
      b58Type = 'wallet'
      self.b58ID = str(inB58ID)
      
      # Get the wallet.
      (ledgerWlt, wltIsCPP) = getWltFromB58ID(self.b58ID, self.serverWltMap, \
                                              self.serverLBMap, \
                                              self.serverLBCppWalletMap)

      # Proceed only if the incoming ID (and, hence, the wallet) is valid.
      if ledgerWlt == None:
         errMsg = 'Error: Base58 ID %s does not represent a valid wallet or ' \
                  'lockbox.' % self.b58ID
         LOGERROR(errMsg)
         final_le_list.append(errMsg)
      else:
         # For now, lockboxes can only use C++ wallets, which use a different
         # set of calls and such. If we got back a Python wallet, convert it.
         if not wltIsCPP:
            ledgerWlt = ledgerWlt.cppWallet
         else:
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

         # Loop through all the potential ledger entries and create what we can.
         for i in range(lower,upper):
            # Get the exact Tx we're looking for.
            le = ledgerEntries[i]
            txHashBin = le.getTxHash()
            txHashHex = binary_to_hex(txHashBin, BIGENDIAN)

            # If the BDM doesn't have the C++ Tx & header, log errors.
            cppTx = TheBDM.getTxByHash(txHashBin)
            if not cppTx.isInitialized():
               LOGERROR('Tx hash not recognized by TheBDM: %s' % txHashHex)

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

            # Get some more data.
            # amtCoins: amt of BTC transacted, always positive (how big are
            #           outputs minus change?)
            # netCoins: net effect on wallet (positive or negative)
            # feeCoins: how much fee was paid for this tx 
            nconf = (TheBDM.getTopBlockHeader().getBlockHeight() - \
                     le.getBlockNum()) + 1
            isToSelf = le.isSentToSelf()
            amtCoins = 0.0
            netCoins = le.getValue()
            feeCoins = getFeeForTx(txHashBin)
            scrAddrs = [cppTx.getTxOutCopy(i).getScrAddressStr() for i in \
                       range(cppTx.getNumTxOut())]

            # Find the first recipient and the change recipient.
            firstScrAddr = ''
            changeScrAddr = ''
            if cppTx.getNumTxOut()==1:
               firstScrAddr = scrAddrs[0]
            elif isToSelf:
               # Sent-to-Self tx
               amtCoins,changeIdx = determineSentToSelfAmt(le, ledgerWlt)
               changeScrAddr = scrAddrs[changeIdx]
               for iout,recipScrAddr in enumerate(scrAddrs):
                  if not iout==changeIdx:
                     firstScrAddr = recipScrAddr
                     break
            elif netCoins<0:
               # Outgoing transaction (process in reverse order so get first)
               amtCoins = -1*(netCoins+feeCoins)
               for recipScrAddr in scrAddrs[::-1]:
                  if ledgerWlt.hasScrAddress(recipScrAddr):
                     changeScrAddr = recipScrAddr
                  else:
                     firstScrAddr = recipScrAddr
            else:
               # Incoming transaction (process in reverse order so get first)
               amtCoins = netCoins
               for recipScrAddr in scrAddrs[::-1]:
                  if ledgerWlt.hasScrAddress(recipScrAddr):
                     firstScrAddr = recipScrAddr
                  else:
                     changeScrAddr = recipScrAddr

            # Determine the direction of the Tx based on the coin setup.
            if netCoins < -feeCoins:
               txDir = 'send'
            elif netCoins > -feeCoins:
               txDir = 'receive'
            else:
               txDir = 'toself'

            # Convert the scrAddrs to display strings.
            firstAddr = scrAddr_to_displayStr(firstScrAddr, self.serverWltMap, \
                                              self.serverLBMap.values())
            changeAddr = '' if len(changeScrAddr)==0 else \
                         scrAddr_to_displayStr(changeScrAddr, \
                                               self.serverWltMap, \
                                               self.serverLBMap.values())

            # Get the address & amount from each TxIn.
            myinputs, otherinputs = [], []
            for iin in range(cppTx.getNumTxIn()):
               sender = TheBDM.getSenderScrAddr(cppTx.getTxInCopy(iin))
               val    = TheBDM.getSentValue(cppTx.getTxInCopy(iin))
               addTo  = (myinputs if ledgerWlt.hasScrAddress(sender) else \
                         otherinputs)
               addTo.append( {'address': scrAddr_to_displayStr(sender, \
                                                            self.serverWltMap, \
                                                   self.serverLBMap.values()), \
                              'amount':  AmountToJSON(val)} )

            # Get the address & amount from each TxOut.
            myoutputs, otheroutputs = [], []
            for iout in range(cppTx.getNumTxOut()):
               recip = cppTx.getTxOutCopy(iout).getScrAddressStr()
               val   = cppTx.getTxOutCopy(iout).getValue();
               addTo = (myoutputs if ledgerWlt.hasScrAddress(recip) else \
                        otheroutputs)
               addTo.append( {'address': scrAddr_to_displayStr(recip, \
                                                            self.serverWltMap, \
                                                   self.serverLBMap.values()), \
                              'amount':  AmountToJSON(val)} )

            # Create the ledger entry. (NB: "comment" isn't doable with C++
            # wallets. Once the 2.0 wallets are ready, it should be restored.)
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
                        #'comment' :      ledgerWlt.getComment(txHashBin),
                        'firstrecip':    firstAddr,
                        'changerecip':   changeAddr
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
   # NB: For now, this is incompatible with lockboxes.
   @catchErrsForJSON
   def jsonrpc_listtransactions(self, tx_count=10, from_tx=0):
      """
      DESCRIPTION:
      List the transactions associated with the currently loaded wallet.
      PARAMETERS:
      tx_count - (Default=10) The number of entries to get. 
      from_tx - (Default=0) The first entry to get.
      RETURN:
      A dictionary with information on the retrieved transactions.
      """

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

      isReady = TheBDM.getBDMState() == 'BlockchainReady'

      info = { \
               'versionstr':        getVersionString(BTCARMORY_VERSION),
               'version':           getVersionInt(BTCARMORY_VERSION),
               #'protocolversion':   0,
               'walletversionstr':  getVersionString(PYBTCWALLET_VERSION),
               'walletversion':     getVersionInt(PYBTCWALLET_VERSION),
               'bdmstate':          TheBDM.getBDMState(),
               'balance':           AmountToJSON(self.curWlt.getBalance()) \
                                    if isReady else -1,
               'blocks':            TheBDM.getTopBlockHeight(),
               #'connections':       (0 if isReady else 1),
               #'proxy':             '',
               'difficulty':        TheBDM.getTopBlockHeader().getDifficulty() \
                                    if isReady else -1,
               'testnet':           USE_TESTNET,
               'keypoolsize':       self.curWlt.addrPoolSize
             }

      return info


   #############################################################################
   @catchErrsForJSON
   def jsonrpc_getblock(self, blkhash):
      """
      DESCRIPTION:
      Get the block associated with a given block hash.
      PARAMETERS:
      blkhash - A hex string representing the block to obtain.
      RETURN:
      A dictionary listing information on the desired block, or empty if the
      block wasn't found.
      """

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
   @catchErrsForJSON
   def jsonrpc_gettransaction(self, txHash):
      """
      DESCRIPTION:
      Get the transaction associated with a given transaction hash.
      PARAMETERS:
      txHash - A hex string representing the block to obtain.
      RETURN:
      A dictionary listing information on the desired transaction, or empty if
      the transaction wasn't found.
      """

      if TheBDM.getBDMState() in ['Uninitialized', 'Offline']:
         return {'Error': 'armoryd is offline'}

      binhash = hex_to_binary(txHash, BIGENDIAN)
      tx = TheBDM.getTxByHash(binhash)
      if not tx.isInitialized():
         return {'Error': 'transaction not found'}

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
   # Function that takes a paired list of recipients and the amount to be sent
   # to them, and creates an unsigned transaction based on the current wallet.
   # The ASCII version of the transaction is sent back.
   # https://bitcointalk.org/index.php?topic=92496.msg1126310#msg1126310
   # contains out-of-date notes regarding how the code works. A slightly more
   # up-to-date comparison can be made against the code in
   # SendBitcoinsFrame::validateInputsGetUSTX() (ui/TxFrames.py).
   def create_unsigned_transaction(self, scriptValuePairs, spendFromLboxID=None):
      # Do initial setup, including choosing the coins you'll use.
      totalSend = long( sum([rv[1] for rv in scriptValuePairs]) )
      fee = 0

      lbox = None
      if spendFromLboxID is None:
         spendBal = self.curWlt.getBalance('Spendable')
         utxoList = self.curWlt.getTxOutList('Spendable')
      else:
         lbox = self.serverLBMap[spendFromLboxID]
         cppWlt = self.serverLBCppWalletMap[spendFromLboxID]
         topBlk = TheBDM.getTopBlockHeight()
         spendBal = cppWlt.getSpendableBalance(topBlk, IGNOREZC)
         utxoList = cppWlt.getSpendableTxOutList(topBlk, IGNOREZC)

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
         if (totalSend + minFeeRec) > spendBal:
            raise NotEnoughCoinsError, "You can't afford the fee!"
         utxoSelect = PySelectCoins(utxoList, totalSend, minFeeRec)
         fee = minFeeRec

      # If we have no coins, bail out.
      if len(utxoSelect)==0:
         raise CoinSelectError, "Coin selection failed. This shouldn't happen."

      # Calculate the change.
      totalSelected = sum([u.getValue() for u in utxoSelect])
      totalChange = totalSelected - (totalSend  + fee)

      # Generate and shuffle the recipient list.
      outputPairs = scriptValuePairs[:]
      if totalChange > 0:
         if spendFromLboxID is None:
            nextAddr = self.curWlt.getNextUnusedAddress().getAddrStr()
            ustxScr = getScriptForUserString(nextAddr, self.serverWltMap, \
                                             self.convLBDictToList())
            outputPairs.append( [ustxScr['Script'], totalChange] )
         else:
            ustxScr = getScriptForUserString(lbox.binScript, self.serverWltMap, \
                                             self.convLBDictToList())
            outputPairs.append( [ustxScr['Script'], totalChange] )
      random.shuffle(outputPairs)

      # If this has nothing to do with lockboxes, we need to make sure
      # we're providing a key map for the inputs.
      pubKeyMap = {}
      for utxo in utxoSelect:
         scrType = getTxOutScriptType(utxo.getScript())
         if scrType in CPP_TXOUT_STDSINGLESIG:
            scrAddr = utxo.getRecipientScrAddr()
            a160 = scrAddr_to_hash160(scrAddr)[1]
            addrObj = self.curWlt.getAddrByHash160(a160)
            if addrObj:
               pubKeyMap[scrAddr] = addrObj.binPublicKey65.toBinStr()

      # Create an unsigned transaction and return the ASCII version.
      usTx = UnsignedTransaction().createFromTxOutSelection(utxoSelect, \
                                                            outputPairs, \
                                                            pubKeyMap)
      return usTx.serializeAscii()


   #############################################################################
   # Helper function that gets an uncompressed public key from a wallet, based
   # on an index value.
   def getPKFromWallet(self, inWlt, inIdx):
      retStr = ''
      try:
         addr160 = inWlt.getAddress160ByChainIndex(inIdx)
         retStr = inWlt.addrMap[addr160].getPubKey().toHexStr()
      except:
         LOGEXCEPT('Error fetching public key in wlt %s for chain index: %d' % \
                                             (inWlt.uniqueIDB58, inIdx))
      return retStr


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
         result['Error'] = errStr
      elif m > LB_MAXM:
         errStr = 'The number of signatures required to unlock a lockbox ' \
                  '(%d) exceeds the maximum allowed (%d)' % (m, LB_MAXM)
         LOGERROR(errStr)
         result['Error'] = errStr
      elif n > LB_MAXN:
         errStr = 'The number of keys or wallets required to create a ' \
                  'lockbox (%d) exceeds the maximum allowed (%d)' % (n, LB_MAXN)
         LOGERROR(errStr)
         result['Error'] = errStr
      elif not args:
         errStr = 'No keys or wallets were specified. %d wallets or keys are ' \
                  'required to create the lockbox.' % n
         LOGERROR(errStr)
         result['Error'] = errStr
      elif len(args) > n:
         errStr = 'The number of supplied keys or wallets (%d) exceeds the ' \
                  'number required to create the lockbox (%d)' % (len(args), n)
         LOGERROR(errStr)
         result['Error'] = errStr
      elif len(args) < n:
         errStr = 'The number of supplied keys or wallets (%d) is less than ' \
                  'the number of required to create the lockbox (%d)' % \
                  (len(args), n)
         LOGERROR(errStr)
         result['Error'] = errStr
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
               lbWltHighestIdx = lbWlt.getHighestUsedIndex()
               lbWltPK = self.getPKFromWallet(lbWlt, lbWltHighestIdx)
               addrList.append(lbWltPK)
               addrName = 'Public key %d from wallet %s' % (lbWltHighestIdx, \
                                                            lockboxItem)
               addrNameList.append(addrName)

            except KeyError:
               # A screwy wallet ID will cause a TypeError if we check to see if
               # it's a pub key. Let's catch it.
               try:
                  # A pub key could be fake but in the proper form, so we
                  # have a second place where a value can fail. Catch it.
                  if isValidPK(lockboxItem, True):
                     # Make sure we're using an uncompressed key before
                     # processing it.
                     if len(lockboxItem) != 130:
                        badArg = lockboxItem
                        allArgsValid = False
                     else:
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
            result['Error'] = errStr
         else:
            # We must sort the addresses and comments together. It's important
            # to keep this code in sync with any other code creating lockboxes.
            # Also, convert the key list from hex to binary to support multisig
            # conversion while also minimizing coding.
            decorated  = [[pk,comm] for pk,comm in zip(addrList, \
                                                       addrNameList)]
            decorSort  = sorted(decorated, key=lambda pair: pair[0])
            for i, pair in enumerate(decorSort):
               lockboxPubKeyList.append(DecoratedPublicKey(hex_to_binary(pair[0])))
               addrList[i]     = hex_to_binary(pair[0])
               addrNameList[i] = pair[1]

            # Let the lockbox creation begin! We'll write it to a file and
            # return the hex representation via JSON.
            pkListScript = pubkeylist_to_multisig_script(addrList, m)
            lbID = calcLockboxID(pkListScript)
            lbCreateDate = long(RightNow())
            lbName = 'Lockbox %s' % lbID
            lbDescrip = '%s - %d-of-%d - Created by armoryd' % (lbID, m, n)
            lockbox = MultiSigLockbox(lbName, lbDescrip, m, n,
                                      lockboxPubKeyList, lbCreateDate)

            # To be safe, we'll write the LB only if Armory doesn't already have
            # a copy.
            if lbID in self.serverLBMap.keys():
               errStr = 'Lockbox %s already exists.' % lbID
               LOGERROR(errStr)
               result['Error'] = errStr
            else:
               # Write to the "master" LB list used by Armory and an individual
               # file, and load the LB into our LB set.
               lbFileName = 'Multisig_%s.lockbox.txt' % lbID
               lbFilePath = os.path.join(self.armoryHomeDir, lbFileName)
               writeLockboxesFile([lockbox], 
                                  os.path.join(self.armoryHomeDir, \
                                               MULTISIG_FILE_NAME), True)
               writeLockboxesFile([lockbox], lbFilePath, False)
               self.serverLBMap[lbID] = lockbox

               result = lockbox.toJSONMap()

      return result


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
      lbFound = True
      retDict = {}

      # We'll return info on the currently loaded LB if no LB ID has been
      # specified. If an LB ID has been specified, we'll get info on it if the
      # specified LB has been loaded.
      if inLBID in self.serverLBIDSet:
         self.lbToUse = self.serverLBMap[inLBID]
      else:
         # Unlike wallets, LBs are optional in armoryd, so we need to make sure
         # the currently loaded LB actually exists.
         if inLBID != None:
            retDict['Error'] = 'Lockbox %s does not exist.' % inLBID
            lbFound = False
         else:
            if self.lbToUse == None:
               retDict['Error'] = 'There are no lockboxes on the server.'
               lbFound = False

      # Get info on the lockbox.
      if lbFound:
         self.outForm = outForm.lower()
         if self.outForm == 'json':
            retDict['JSON'] = self.lbToUse.toJSONMap()
         elif self.outForm == 'hex':
            retDict['Hex'] = binary_to_hex(self.lbToUse.serialize())
         elif self.outForm == 'base64':
            retDict['Base64'] = base64.b64encode(binary_to_hex(self.lbToUse.serialize()))
         else:
            retDict['Error'] = '%s is an invalid output type.' % self.outForm

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
   @catchErrsForJSON
   def jsonrpc_watchwallet(self, send_from, smtpServer=None, password=None,
                           send_to=None, subject=None, watchCmd='add'):
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
   @catchErrsForJSON
   def jsonrpc_sendlockbox(self, lbIDs, sender, server, pwd, recips,
                           msgSubj='Armory Lockbox'):
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
      @EmailOutput(sender, server, pwd, recips, msgSubj)
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
   # Associate meta data to an address or addresses
   # Example input:  "{\"mzAtXhy3Z6SLd7rAwNJrL17e8mQkjDVDXh\": {\"chain\": 5,
   # \"index\": 2}, \"mkF5L93F5HLhLmQagX26TdXcvPGHvfjoTM\": {\"CrazyField\": \"what\",
   # \"1\": 1, \"2\": 2}}"
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
         if not self.curWlt.addrMap.has_key(addrStr_to_hash160(addr, False)[1]):
            raise AddressNotInWallet
      self.addressMetaData.update(newAddressMetaData)


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
         self.curWlt.syncWithBlockchain() # Call after each BDM operation.
         retStr = 'Wallet %s is now active.' % newIDB58
      except:
         LOGERROR('setactivewallet - Wallet %s does not exist.' % newIDB58)
         retStr = 'Wallet %s does not exist.' % newIDB58
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
      for k in self.serverWltMap.keys():
         curWltStr = 'Wallet %04d' % curKey
         walletList[curWltStr] = k
         curKey += 1
      return walletList


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
   # Pull in a signed Tx and get the raw Tx hex data to broadcast. This call
   # works with a regular signed Tx and a signed lockbox Tx if there are already
   # enough signatures.
   @catchErrsForJSON
   def jsonrpc_gethextxtobroadcast(self, txASCIIFile):
      """
      DESCRIPTION:
      Get a signed Tx from a file and get the raw hex data to broadcast.
      PARAMETERS:
      txASCIIFile - The path to a file with an signed transacion.
      RETURN:
      A hex string of the raw transaction data to be transmitted.
      """

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
                       (binary_to_hex(newTxHash), \
                        binary_to_hex(finalTx.serialize())))
               self.retStr = binary_to_hex(finalTx.serialize())
            else:
               LOGERROR('The Tx data isn\'t ready to be broadcast')

      return self.retStr


   ##################################
   # Take the ASCII representation of an unsigned Tx (i.e., the data that is
   # signed by Armory's offline Tx functionality) and returns an ASCII
   # representation of the signed Tx, with the current wallet signing the Tx.
   # See SignBroadcastOfflineTxFrame::signTx() (ui/TxFrames.py) for the GUI's
   # analog.
   @catchErrsForJSON
   def jsonrpc_signasciitransaction(self, unsignedTxASCII, wltPasswd=None):
      """
      DESCRIPTION:
      Sign an unsigned transaction and get the signed ASCII data.
      PARAMETERS:
      unsignedTxASCII - An ASCII-formatted unsigned transaction, like the one
                        used by Armory for offline transactions.
      wltPasswd - (Default=None) If needed, the current wallet's password.
      RETURN:
      A dictionary containing a string with the ASCII-formatted signed
      transaction or, if the signing failed, a string indicating failure.
      """

      retDict = {}

      # As a courtesy to people who use them, we'll strip quotation marks
      # from the beginning and/or end of the string.
      unsignedTxASCII = str(unsignedTxASCII)
      if unsignedTxASCII[0] == '\"':
         unsignedTxASCII = unsignedTxASCII[1:]
      if unsignedTxASCII[-1] == '\"':
         unsignedTxASCII = unsignedTxASCII[:-1]

      unsignedTx = UnsignedTransaction().unserializeAscii(unsignedTxASCII)

      # If the wallet is encrypted, attempt to decrypt it.
      decrypted = False
      if self.curWlt.useEncryption:
         try:
            passwd = SecureBinaryData(str(wltPasswd))
            if not self.curWlt.verifyPassphrase(passwd):
               LOGERROR('Passphrase was incorrect! Wallet could not be ' \
                        'unlocked. Signed transaction will not be created.')
               retDict['Error'] = 'Passphrase was incorrect! Wallet could ' \
                                  'not be unlocked. Signed transaction will ' \
                                  'not be created.'
            else:
               self.curWlt.unlock(securePassphrase=passwd)
               decrypted = True
         finally:
            passwd.destroy()

      # If the wallet's unencrypted, we want to continue.
      else:
         decrypted = True

      # Create the signed transaction and verify it.
      if decrypted:
         unsignedTx = self.curWlt.signUnsignedTx(unsignedTx)
         self.curWlt.advanceHighestIndex()
         if not unsignedTx.verifySigsAllInputs():
            LOGERROR('Error signing transaction. The correct wallet was ' \
                     'probably not used.')
            retDict['Error'] = 'Error signing transaction. The correct ' \
                               'wallet was probably not used.'
         else:
            # The signed Tx is valid.
            retDict['SignedTx'] = unsignedTx.serializeAscii()

      return retDict


   #############################################################################
   # Register some code to be run when we encounter a zero-conf Tx or a
   # "surprise" Tx. The definitions are as follows.
   #
   # Zero-conf Tx: A Tx seen by itelf on the network. (This is virtually every
   #               Tx on the network.)
   # Surprise Tx: On rare occasions, a transaction will be seen for the first
   #              time when it appears in a block.
   #
   # NB: This code is NOT ready for everyday use and is here primarily to
   # establish some hooks to support future work. It's also blatantly wrong, as
   # the code doesn't match the newBlockFunctions code. Hack at your own risk!
   #@catchErrsForJSON
   #def jsonrpc_registertxscript(self, scrPath):
   #   """
   #   DESCRIPTION:
   #   Add wallets onto the armoryd server.
   #   PARAMETERS:
   #   None
   #   RETURN:
   #   None
   #   """
   #
   #   rpc_server.newTxFunctions[curWlt].append(scrPath)


   #############################################################################
   # Helper funct that converts the lockbox dict into a list.
   def convLBDictToList(self):
      retList = []

      for lb in self.serverLBMap.values():
         retList.append(lb)

      return retList


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

      return jsonFunctDict


   #############################################################################
   def getWalletForAddr160(self, addr160):
      for wltID,wlt in self.serverWltMap.iteritems():
         if wlt.hasAddr(addr160):
            return wltID
      return ''

   #############################################################################
   def getWalletForScrAddr(self, scrAddr):
      for wltID, wlt in self.serverWltMap.iteritems():
         if wlt.hasScrAddr(scrAddr):
            return wltID
      return ''

   ################################################################################
   # Get  the lock box ID if the p2shAddrString is found in one of the lockboxes
   # otherwise it returns None
   def getLockboxByP2SHAddrStr(self, p2shAddrStr):
      for lboxId,lbox in self.serverLBMap.iteritems():
         if p2shAddrStr == binScript_to_p2shAddrStr(lbox.binScript):
            return lbox
      return None



# Now that we have completed the armoryd server class, let's build the
# dict that includes the functions clients can call, along with documentation.
# Be sure to use only functs with "jsonrpc_" at the start of the funct name (and
# also strip "jsonrpc_") and get the funct's docstring ("""Funct descrip"""),
# which will be extensively parsed to create the dict.
jFunctPrefix = "jsonrpc_"
jFuncts = inspect.getmembers(Armory_Json_Rpc_Server, predicate=inspect.ismethod)

# Check only the applicable functs.
for curJFunct in jFuncts:
   if curJFunct[0].startswith(jFunctPrefix):
      # Remember to strip the prefix before using the funct name.
      functDoc = {}
      functName = curJFunct[0][len(jFunctPrefix):]

      # Save the descrip/param/return data while stripping out the targeted
      # strings (e.g., "PARAMETERS:"). Also, filter out the empty string in
      # the resultant list, which should have three entries in the end.
      m = '[ \n]*DESCRIPTION:[ \n]*|[ \n]*PARAMETERS:[ \n]*|[ \n]*RETURN:[ \n]*'
      functSplit = filter(None, re.split(m, str(curJFunct[1].__doc__)))

      if(len(functSplit) != 3):
         functDoc['Error'] = 'The function description is malformed.'
      else:
         # While the help text is still together, perform the following steps.
         # Description:  Replace newlines & extra space w/ 1 space, then strip
         #               leading & trailing whitespace. (This allows params to
         #               be described over multiple lines.)
         # Parameters:   Strip extra whitespace.
         # Return Value: Replace newlines & extra space w/ 1 space, then strip
         #               leading & trailing whitespace. (This allows vals to be
         #               described over multiple lines.)
         functSplit[0] = re.sub(r' *\n *', ' ', functSplit[0]).strip()
         functSplit[1] = functSplit[1].strip()
         functSplit[2] = re.sub(r' *\n *', ' ', functSplit[2]).strip()

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
         functDoc = {}
         functParams = []
         if functSplit[1] == 'None':
            functParams.append(functSplit[1])
         else:
            functSplit2 = filter(None, (re.split(r'([^\s]+) - ', \
                                                 functSplit[1])))
            functSplit3 = getDualIterable(functSplit2)
            for pName, pDescrip in functSplit3:
               pDescripClean = re.sub(r' *\n *', ' ', pDescrip).strip()
               pStr = '%s - %s' % (pName, pDescripClean)
               functParams.append(pStr)

         # Save all the strings & lists in the funct's dict. The code is written
         # to prevent numerical confusion that can occur from pops.
         functDoc['Parameters'] = functParams
         functDoc['Return Value'] = functSplit.pop(2)
         functDoc['Description'] = functSplit.pop(0)

      # Save the funct's dict in the master dict to be returned to the user.
      jsonFunctDict[functName] = functDoc


################################################################################
class Armory_Daemon(object):
   def __init__(self, wlt=None, lb=None):

      # NB: These objects contain ONLY wallet/lockbox data loaded at startup.
      # Armory_Json_Rpc_Server will contain the active wallet/LB lists.

      # WltMap:   wltID --> PyBtcWallet
      self.WltMap = {}
      self.wltIDSet = set()

      # lboxMap:           lboxID --> MultiSigLockbox
      # lboxCppWalletMap:  lboxID --> Cpp.BtcWallet
      self.lboxMap = {}   
      self.lboxCppWalletMap = {}
      self.lbIDSet = set()

      self.curWlt = None
      self.curLB = None

      self.newZeroConfSinceLastUpdate = []

      # Check if armoryd is already running. If so, just execute the command,
      # otherwise prepare to act as the server.
      armorydIsRunning = self.checkForAlreadyRunning()
      if armorydIsRunning == True:
         # Execute the command and return to the command line.
         self.executeCommand()
         os._exit(0)
      else:
         # Make sure we're actually able to do something before proceeding.
         if setupNetworking():
            self.lock = threading.Lock()
            self.lastChecked = None

            #check wallet consistency every hour
            self.checkStep = 3600
                        
            ################################################################################
            # armoryd is still somewhat immature. We'll print a warning to let people know
            # that armoryd is still beta software and that the API may change.
            LOGWARN('************************************************************************')
            LOGWARN('* Please note that armoryd v%s is beta software and is still in ' % \
                  getVersionString(BTCARMORY_VERSION))
            LOGWARN('* development. Whenever applicable, the interface is designed to match ')
            LOGWARN('* that of bitcoind, with function parameters and return values closely ')
            LOGWARN('* matching those of bitcoind. Despite this, the function parameters and ')
            LOGWARN('* return values may change, both for ported bitcoind function and ')
            LOGWARN('* Armory-specific functions.')
            LOGWARN('************************************************************************')
            LOGWARN('')
            LOGWARN('*'*80)

            LOGWARN('* WARNING!  WALLET FILE ACCESS IS NOT INTERPROCESS-SAFE!')
            LOGWARN('*           DO NOT run armoryd at the same time as ArmoryQt if ')
            LOGWARN('*           they are managing the same wallet file.  If you want ')
            LOGWARN('*           to manage the same wallet with both applications ')
            LOGWARN('*           you must make a digital copy/backup of the wallet file ')
            LOGWARN('*           into another directory and point armoryd at that one.  ')
            LOGWARN('*           ')
            LOGWARN('*           As long as the two processes do not share the same ')
            LOGWARN('*           actual file, there is no risk of wallet corruption. ')
            LOGWARN('*           Just be aware that addresses may end up being reused ')
            LOGWARN('*           if you execute transactions at approximately the same ')
            LOGWARN('*           time with both apps. ')
            LOGWARN('*')
            LOGWARN('*'*80)
            LOGWARN('')

            # Otherwise, set up the server. This includes a defaultdict with a
            # list of functs to execute. This is done so that multiple functs
            # can be associated with the same search key.
            self.newTxFunctions = []
            self.heartbeatFunctions = []
            self.newBlockFunctions = defaultdict(list)

            # armoryd can take a default lockbox. If it's not passed in, load
            # some lockboxes.
            if lb:
               self.curLB = lb
            else:
               # Get the lockboxes in standard Armory LB file and store pointers
               # to them, assuming any exist.
               lbPaths = getLockboxFilePaths()
               addMultLockboxes(lbPaths, self.lboxMap, self.lbIDSet)
               if len(self.lboxMap) > 0:
                  # Set the current LB to the 1st wallet in the set. (The choice
                  # is arbitrary.)
                  self.curLB = self.lboxMap[self.lboxMap.keys()[0]]

                  # Create the CPP wallet map for each lockbox.
                  for lbID,lbox in self.lboxMap.iteritems():
                     self.lboxCppWalletMap[lbID] = BtcWallet()
                     scraddrReg = script_to_scrAddr(lbox.binScript)
                     scraddrP2SH = script_to_scrAddr(script_to_p2sh_script(lbox.binScript))
                     self.lboxCppWalletMap[lbID].addScrAddress_1_(scraddrReg)
                     self.lboxCppWalletMap[lbID].addScrAddress_1_(scraddrP2SH)
                     LOGWARN('Registering lockbox: %s' % lbID)
                     TheBDM.registerWallet(self.lboxCppWalletMap[lbID])

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
               addMultWallets(wltPaths, self.WltMap, self.wltIDSet)
               if len(self.WltMap) > 0:
                  self.curWlt = self.WltMap[self.WltMap.keys()[0]]
                  self.WltMap[self.curWlt.uniqueIDB58] = self.curWlt
                  self.wltIDSet.add(self.curWlt.uniqueIDB58)
               else:
                  LOGERROR('No wallets could be loaded! armoryd will exit.')

            # Log info on the wallets we've loaded.
            numWallets = len(self.WltMap)
            LOGINFO('Number of wallets read in: %d', numWallets)
            for wltID, wlt in self.WltMap.iteritems():
               dispStr  = ('   Wallet (%s):' % wltID).ljust(25)
               dispStr +=  '"'+wlt.labelName.ljust(32)+'"   '
               dispStr +=  '(Encrypted)' if wlt.useEncryption else '(No Encryption)'
               LOGINFO(dispStr)

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

            LOGINFO("Initialising RPC server on port %d", ARMORY_RPC_PORT)
            resource = Armory_Json_Rpc_Server(self.curWlt, self.curLB, \
                                              self.WltMap, self.lboxMap, \
                                              self.wltIDSet, self.lbIDSet, \
                                              self.lboxCppWalletMap)
            secured_resource = self.set_auth(resource)

            # This is LISTEN call for armory RPC server
            reactor.listenTCP(ARMORY_RPC_PORT, \
                              server.Site(secured_resource), \
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
   def set_auth(self, resource):
      passwordfile = ARMORYD_CONF_FILE
      # Create User Name & Password file to use locally
      if not os.path.exists(passwordfile):
         with open(passwordfile,'a') as f:
            # Don't wait for Python or the OS to write the file. Flush buffers.
            try:
               genVal = SecureBinaryData().GenerateRandom(32)
               f.write('generated_by_armory:%s' % binary_to_base58(genVal.toBinStr()))
               f.flush()
               os.fsync(f.fileno())
            finally:
               genVal.destroy()

      checker = FilePasswordDB(passwordfile)
      realmName = "Armory JSON-RPC App"
      wrapper = wrapResource(resource, [checker], realmName=realmName)
      return wrapper


   #############################################################################
   # NB: ArmoryQt has a similar function (finishLoadBlockchainGUI) that shares
   # common functionality via the BDM (finishLoadBlockchainCommon). If you mod
   # this function, please be mindful of what goes where, and make sure any
   # critical functionality makes it into ArmoryQt.
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
         # Put the BDM in online mode only after registering all Python wallets.
         for wltID, wlt in self.WltMap.iteritems():
            LOGWARN('Registering wallet: %s' % wltID)
            TheBDM.registerWallet(wlt)
         TheBDM.setOnlineMode(True)

         # Initialize the mem pool and sync the wallets.
         self.latestBlockNum = TheBDM.finishLoadBlockchainCommon(self.WltMap, \
                                                          self.lboxCppWalletMap, \
                                                          False)[0]

         self.timeReceived = TheBDM.getTopBlockHeader().getTimestamp()
         LOGINFO('Blockchain loaded. Wallets synced!')
         LOGINFO('Current block number: %d', self.latestBlockNum)
         LOGINFO('Current block received at: %d', self.timeReceived)

         vectMissingBlks = TheBDM.missingBlockHashes()
         LOGINFO('Blockfile corruption check: Missing blocks: %d', \
                 len(vectMissingBlks))
         if len(vectMissingBlks) > 0:
            LOGERROR('Armory has detected an error in the blockchain ' \
                     'database maintained by the third-party Bitcoin ' \
                     'software (Bitcoin-Qt or bitcoind). This error is not ' \
                     'fatal, but may lead to incorrect balances, inability ' \
                     'to send coins, or application instability. It is ' \
                     'unlikely that the error affects your wallets, but it ' \
                     'is possible.  If you experience crashing, or see ' \
                     'incorrect balances on any wallets, it is strongly ' \
                     'recommended you re-download the blockchain via the ' \
                     '"Factory Reset" option in ArmoryQt.')

         LOGINFO('Wallet balance: %s' % \
                 coin2str(self.curWlt.getBalance('Spendable')))

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
         LOGINFO('No other armoryd.py instance is running.  We\'re the first. %d' % ARMORY_RPC_PORT)
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

            # Call the user's command (e.g., "getbalance full" ->
            # jsonrpc_getbalance(full)) and print results.
            result = proxyobj.__getattr__(CLI_ARGS[0])(*extraArgs)
            print json.dumps(result, indent=4, sort_keys=True, \
                             cls=UniversalEncoder)

            # If there are any special cases where we wish to do some
            # post-processing on the client side, do it here.
            # For now, no such post-processing is required.

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
      # Execute on every new Tx.
      TheBDM.addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True)
      self.newZeroConfSinceLastUpdate.append(pytxObj.serialize())
      #TheBDM.rescanWalletZeroConf(self.curWlt.cppWallet)

      # Add anything else you'd like to do on a new transaction.
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
      # not have the new block data yet. (There's a variety of reason for
      # this design decision, I can enumerate them for you in an email....)
      # If you need to execute anything, execute after readBlkFileUpdate().

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

      try:

         for wltID,wlt in self.WltMap.iteritems():
            wlt.checkWalletLockTimeout()

         # Check for new blocks in the latest blk0XXXX.dat file.
         if TheBDM.getBDMState()=='BlockchainReady':
            #check wallet every checkStep seconds
            nextCheck = self.lastChecked + self.checkStep
            if RightNow() >= nextCheck:
               self.checkWallet()
   
            # If there's a new block, use this to determine it affected our wallets.
            # NB: We may wish to alter this to reflect only the active wallet.
            #prevLedgSize = dict([(wltID, len(self.walletMap[wltID].getTxLedger())) \
            #                                    for wltID in WltMap.keys()])
   
   
            # Check for new blocks in the blk000X.dat file
            prevTopBlock = TheBDM.getTopBlockHeight()
            newBlks = TheBDM.readBlkFileUpdate(wait=True)
   
            # If we have new zero-conf transactions, scan them and update ledger
            if len(self.newZeroConfSinceLastUpdate)>0:
               self.newZeroConfSinceLastUpdate.reverse()
               for wltID in self.WltMap.keys():
                  wlt = self.WltMap[wltID]
                  TheBDM.rescanWalletZeroConf(wlt.cppWallet, wait=True)
   
               for lbID,cppWlt in self.lboxCppWalletMap.iteritems():
                  TheBDM.rescanWalletZeroConf(cppWlt, wait=True)
                     
            # We had a notification thing going in ArmoryQt using checkNewZeroConf()
            # but we didn't need it here (yet), so I simply remove it and clear the
            # ZC list as if we called it
            #self.checkNewZeroConf()
            #del self.newZeroConfSinceLastUpdate[:]
            self.newZeroConfSinceLastUpdate = []
   
            if newBlks>0:
               self.latestBlockNum = TheBDM.getTopBlockHeight()
               self.topTimestamp   = TheBDM.getTopBlockHeader().getTimestamp()
   
         
               # This tracks every wallet and lockbox registered, runs standard
               # update functions after new blocks come in.  "After scan" also
               # means after we've updated the blockchain with a new block.
               TheBDM.updateWalletsAfterScan(wait=True)
   
               # On very rare occasions, we could come across a new Tx in a block
               # instead of seeing it on the network first. Let's check for this
               # case and, if desired, execute NewTx user functs.
               # NB: As written, this code is probably wrong! We only care about
               # the active wallet, but we're passing in the entire wallet set.
               # We probably ought to add awareness of the current wallet in the
               # daemon. Be sure to get the initial wallet and do post-processing
               # when a user wants to change the active wallet. (For that matter,
               # we should probably add post-processing when adding wallets so
               # that we can track what we have.)
               #surpriseTx = newBlockSyncRescanZC(TheBDM, WltMap, prevLedgSize)
               #if surpriseTx:
                  #LOGINFO('New Block contained a transaction relevant to us!')
                  # THIS NEEDS TO BE CHECKED! IT STILL USES ARMORYQT VALUES!!!
                  # WltMap SHOULD ALSO PROBABLY BE CHANGED TO THE CURRENT WALLET!
                  #notifyOnSurpriseTx(self.currBlockNum-newBlocks, \
                  #                   self.currBlockNum+1, WltMap, False, TheBDM)
   
                  # If there's user-executed code on a new Tx, execute here before
                  # dealing with any new blocks.
                  # NB: THIS IS PLACEHOLDER CODE THAT MAY BE WRONG!!!
                  #for txFunc in self.newTxFunctions:
                     #txFunc(pytxObj)
   
               # If there are no new block functions to run, just skip all this.
               if len(self.newBlockFunctions) > 0:
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
   rpc_server = Armory_Daemon()
   rpc_server.start()
