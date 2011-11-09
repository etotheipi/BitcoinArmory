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


# Load the blockchain
loadBlockchainFile()

# Load our private key into a wallet object -- private key for:
#   addrStr = '12HFYcL3Gj8EPhgeXk5689z8Wcc7x7FsNx' 
#   addr160 = '0e0aec36fe2545fb31a41164fb6954adcd96b342'
#   pubKeyHex = ('04' '8d103d81ac9691cf13f3fc94e44968ef67b27f58b27372c13108552d24a6ee04'
#                     '785838f34624b294afee83749b64478bb8480c20b242c376e77eea2b3dc48b4b')
pywlt = PyBtcWallet()
# temp altered private key for git-commit/push
privKeyHex = 'ffffffd8d7103877f577aa176926b18b1e004195644abb7f7dc19e3f267e7aa4'
pywlt.addAddress(hex_to_binary(privKeyHex))
pywlt.syncWithBlockchain()
utxoList = pywlt.getUnspentTxOutList()
pprintUnspentTxOutList(utxoList, 'All unspent coins:')

#addrStr1 = hex_to_binary('0e0aec36fe2545fb31a41164fb6954adcd96b342');
#cppWallet = Cpp.BtcWallet()
#cppWallet.addAddress_1_(addrStr1);
#bdm.scanBlockchainForTx_FromScratch(cppWallet);
#print 'Getting unspent TxOuts for addresses:'
#utxolist = bdm.getUnspentTxOutsForWallet(cppWallet)
#pprintUnspentTxOutList(utxolist, "All utxos:")



print ''
print 'Testing some random targets for the SelectCoins method:'
tryTgtVals = [a*1e8 for a in [0.01, 0.05, 0.1, 0.3, 0.99, 1.4]]
for tgt in tryTgtVals:
   selected = PySelectCoins(utxoList, tgt, 0)
   pprintUnspentTxOutList(selected, ' Selection: Target=' + coin2str(tgt,4))

recipAddr  = PyBtcAddress().createFromAddrStr(argv[1])
recipValue = long(float(argv[2]) * COIN)
fee       =  0
   
print ''
print '\n\nNow trying a specific tx with fees:'

prelimSelection = PySelectCoins(utxoList, recipValue, fee)
feeRecommended = calcMinSuggestedFees(prelimSelection, recipValue, fee)
pprintUnspentTxOutList(prelimSelection, 'Selected TxOuts for (tgt,fee)=(%s,%s)' % \
                           (coin2str(recipValue), coin2str(fee)))
print 'Recommended fees:', feeRecommended

recipPairs = []
pair1 = [recipAddr.getAddr160(), recipValue]
pair2 = [pywlt.getAddrByIndex(0).getAddr160(), sumTxOutList(prelimSelection)-(recipValue+fee)]
if random.uniform(0,1) < 0.5:
   recipPairs = [pair1, pair2]
else:
   recipPairs = [pair2, pair1]
   
print '\n\nCreating TxDistProposal:'
txdp = PyTxDistProposal().createFromTxOutSelection(prelimSelection, recipPairs)
txdp.pprint()

print '\n\nSigning the TxDP:'
signedTxDP = pywlt.signTxDistProposal(txdp)
txToBroadcast = signedTxDP.getFinalPyTx()
txToBroadcast.pprint()

print binary_to_hex(txToBroadcast.serialize())
pprintHex(binary_to_hex(txToBroadcast.serialize()))
