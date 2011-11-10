from pybtcengine import *
import CppBlockUtils as Cpp
from datetime import datetime
from os import path
from sys import argv
from swigPbeEngine import *
import random


if len(argv)<3:
   print 'USAGE: ', argv[0], '<recipientAddrStr> <BTC>'
   exit(0)

# Process CLI arguments
recipAddr  = PyBtcAddress().createFromAddrStr(argv[1])
recipValue = long(float(argv[2]) * COIN)
fee        = 0

# Load the blockchain
loadBlockchainFile()

# Create a wallet, which for now will only contain one key
pywlt = PyBtcWallet()

# This private key corresponds to:
#   addrStr = '12HFYcL3Gj8EPhgeXk5689z8Wcc7x7FsNx' 
#   addr160 = '0e0aec36fe2545fb31a41164fb6954adcd96b342'
#   pubKeyHex = ('04' '8d103d81ac9691cf13f3fc94e44968ef67b27f58b27372c13108552d24a6ee04'
#                     '785838f34624b294afee83749b64478bb8480c20b242c376e77eea2b3dc48b4b')
privKeyHex = 'ffffffd8d7103877f577aa176926b18b1e004195644abb7f7dc19e3f267e7aa4'
pywlt.addAddress(hex_to_binary(privKeyHex))
utxoList = pywlt.getUnspentTxOutList()

# Let's display all available TxOuts
pprintUnspentTxOutList(utxoList, 'All unspent coins:')

   
# Figure out a *good* selection of TxOuts to use
prelimSelection = PySelectCoins(utxoList, 4*recipValue, fee)
feeRecommended = calcMinSuggestedFees(prelimSelection, recipValue, fee)
pprintUnspentTxOutList(prelimSelection, 'Selected TxOuts for (tgt,fee)=(%s,%s)' % \
                           (coin2str(recipValue), coin2str(fee)))
print 'Recommended fees:  AbsMin=%s, Suggest=%s' % tuple([coin2str(f) for f in feeRecommended])


# Construct the output addresses, with a random order
recipPairs = []
recipPairs.append(['12irKW1XFSnnu6v5FevcC3wZ6hfvPmaEDQ', recipValue])
recipPairs.append([recipAddr, recipValue])
recipPairs.append(['1PymCiNzubeTtJt47dqFdi31Zy9MAM1YZk', recipValue])
recipPairs.append(['1H3Jbv99F7Ng8oiadCovvda17CGZ9EFkPM', recipValue])
recipPairs.append(['16jN5NhB4eoUqFrSvuNnvDEc57oz6GRNi4', recipValue])
recipPairs.append(['17aLXn2XHKH7nhwdCPaWmkY6jgr36zSjyz', recipValue])
recipPairs.append(['1PjURhoxGr6cdK5YY5SyDDY2pQhEpbZdoK', recipValue])
recipPairs.append(['1NgBFTvqM6FsooFtkvFgf7VxzRBdXKnxpR', recipValue])
recipPairs.append(['176msrhhemi6q8DEdpBCoTQJvRCiGV5qEm', recipValue])
recipPairs.append(['16FSHWWyUv6wzT9qpbi7tCaovf6XX7T9xN', recipValue])
recipPairs.append(['1JiLbGTrVNmk6BsePVQWmBiD7DFUDmMYXw', recipValue])
recipPairs.append(['124DJWV7vYS8DUcVan4SXcGNAubopS1BHj', recipValue])
recipPairs.append(['1PESigPSLwsvaQAQfCDDPZM21i9m8Vqt21', recipValue])
recipPairs.append(['18i1rVZHMMXQwRxZuSrHZrpqUoejkV2Gh2', recipValue])
recipPairs.append(['1PZjRprkrM93GVXNdJ5zu7C1p84weTovWj', recipValue])
recipPairs.append(['14cKqt9e8QvgMaBrwbuykBjha1vXNtaj72', recipValue])
recipPairs.append(['1QJUzen8xL7EyBTGnkDUX6fnoMX9TL1fU7', recipValue])
recipPairs.append(['17iRBkToUTzDvVpXsNUT8usT6c6aEDe15R', recipValue])
recipPairs.append(['1NVJS8DWLdrte45rc5oGvWyjrAe9y1rtFt', recipValue])
recipPairs.append(['1MzxEf2Ck9XSC7U5y5DHQvMyPhL2UNcjSD', recipValue])
#pair1 = [recipAddr, recipValue]
#pair2 = [pywlt.getAddrByIndex(0), sumTxOutList(prelimSelection)-(recipValue+fee)]
#if random.uniform(0,1) < 0.5:
   #recipPairs = [pair1, pair2]
#else:
   #recipPairs = [pair2, pair1]
   
print '\n\nCreating TxDistProposal:'
txdp = PyTxDistProposal().createFromTxOutSelection(prelimSelection, recipPairs)
txdp.pprint()

print '\n\nSigning the TxDP:'
signedTxDP = pywlt.signTxDistProposal(txdp)
txToBroadcast = signedTxDP.getFinalPyTx()
txToBroadcast.pprint()

print binary_to_hex(txToBroadcast.serialize())
pprintHex(binary_to_hex(txToBroadcast.serialize()))
