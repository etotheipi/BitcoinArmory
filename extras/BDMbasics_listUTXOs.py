'''
The BDM stands for Block Data Manager. It maintains the history for all 
registered wallets. 

In this example, we will list all unpsent txouts for our wallet. 

This example needs one argument, the path to the wallet to monitor.
'''

import os
import sys
sys.path.append('..')
from armoryengine.ALL import *

# Check that user actually supplied a wallet file
if len(CLI_ARGS) < 1:
   print 'Must supply path to wallet file as first argument!'
   exit(1)

# Check that wallet file exists
walletPath = CLI_ARGS[0]
if not os.path.exists(walletPath):
   print 'Wallet file does not exist: "%s"' % walletPath
   exit(1)
   
# Read it into a PyBtcWallet object
wlt = PyBtcWallet().readWalletFile(walletPath)

# Creates a shared condition variable for signaling main thread shutdown
cvShutdown = threading.Condition(None)


################################################################################
def listUTXOs(*args):
   # Leverages armoryengine.CoinSelection.py to print all UTXOs
   # args is ignored -- we only care that this is called after BDM is loaded
   print 'Printing UTXOs for wallet: ' + wlt.uniqueIDB58
   utxos = wlt.getFullUTXOList()
   pprintUnspentTxOutList(utxos)

   # Signal to main thread that we're done
   cvShutdown.acquire(); cvShutdown.notify_all(); cvShutdown.release()
   

# Register the method to be called when TheBDM is done loading the blockchain
TheBDM.RegisterEventForSignal(listUTXOs, FINISH_LOAD_BLOCKCHAIN_ACTION)

# Register our wallet with the BDM before we attempt to load the blockchain
# The BDM will make sure the history is up to date before signaling our callback
wlt.registerWallet(isNew=False)

# Now start the BDM.  It will load & update databases, emit signals when ready
TheBDM.goOnline()

'''
The BDM runs on its own thread and will signal our callback when a new event 
occurs. All actions take place on a signal basis, while the main thread is
left to perform its own operations. For this reason, our main thread needs it 
own loop, otherwise it would exit and shutdown our entire process. 

Here we have nothing to do so we'll have the main thread wait on a condition
variable that listUTXOs will notify once it is done, which will result in the
main thread exiting and the subsequent termination of the process.
'''

# This will pause the main thread until notification is received
cvShutdown.acquire(); cvShutdown.wait(); cvShutdown.release()
   
print '...Done'
