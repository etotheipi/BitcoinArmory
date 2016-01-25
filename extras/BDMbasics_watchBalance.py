################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
"""
This example needs one argument, the path to the wallet to monitor.  It can
be either a "full" wallet or a watch-only wallet.

The BDM stands for "Block Data Manager." It maintains the history for all 
registered wallets.  

In this example, we will list all initialize the BDM and indefinitely wait
on new blocks, on which occasion we will print out our registered wallet's
balance
"""

import os
import sys
sys.path.append('..') # this is for when the script is run in the extras dir
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

################################################################################
def printWalletBalance(args):
   # If any args, it's because this is a NEW_BLOCK_ACTION with a new top block
   print 'Current top block:', TheBDM.getTopBlockHeight()

   # Print all three types of balances you can query for a wallet
   for balType in ['full', 'spendable', 'unconfirmed']:
      balStr  = coin2str(wlt.getBalance(balType))
      typeStr = balType.upper().rjust(16)
      print '%s balance for wallet %s: %s BTC' % (typeStr, wlt.uniqueIDB58, balStr)
   


################################################################################
#Register the BDM callback
TheBDM.RegisterEventForSignal(printWalletBalance, FINISH_LOAD_BLOCKCHAIN_ACTION)
TheBDM.RegisterEventForSignal(printWalletBalance, NEW_BLOCK_ACTION)

# Register our wallet with the BDM.
# Pass False during registration because we don't know if the wallet is new. 
# The BDM will make sure the history is up to date before signaling our callback
wlt.registerWallet(isNew=False)

#Now start the BDM
TheBDM.goOnline()

'''
The BDM runs on its own thread and will signal our callback when a new event 
occurs. All actions take place on a signal basis, while the main thread is
left to perform its own operations. For this reason, our main thread needs it 
own loop, otherwise it would exit and shutdown our entire process. Here we have 
nothing to do so we'll use an empty loop that sleeps for a second on every 
iteration
'''

try:
   while(True):
      time.sleep(1)
except KeyboardInterrupt:
   exit(0)


