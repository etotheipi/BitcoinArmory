'''
The BDM stands for Block Data Manager. It maintains the history for all 
registered wallets. 

In this example, we will initialize the BDM and indefinitely wait
on new blocks, on which occasion we will print out our registered wallet's
balance

This example needs one argument, the path to the wallet to monitor.  
'''

from armoryengine.ALL import *

#load wallet from file
wlt = PyBtcWallet().readWalletFile( CLI_ARGS[0] )

################################################################################
def printWalletBalance():
   
   print 'unspent balance for wallet ' + wlt.uniqueIDB58 + ': ' + \
          coin2str(wlt.getBalance("full"))
   
   print 'spendable balance for wallet ' + wlt.uniqueIDB58 + ': ' + \
          coin2str(wlt.getBalance('spendable'))
   
   print 'unconfirmed balance for wallet ' + wlt.uniqueIDB58 + ': ' + \
          coin2str(wlt.getBalance('unconfirmed'))
   print '-------------'

################################################################################
def BDM_callback(signal, args):
   '''
   This is a prototype callback method. It requires 2 arguments:
      1) signal: the type of signal received from the BDM
      2) args: an object containing the extra arguments passed to the callback, 
         depends on the signal type 
         
      Once this callback is registered with the BDM, it will receive all
      notifications from the BDM. Notification you don't need to handle can 
      simply be ignored
   '''
   
   if signal == FINISH_LOAD_BLOCKCHAIN_ACTION:
      #This signal indicates the BDM has finished initializing. All wallet 
      #history is up to date on the BDM side. At this point
      #you can query balance and create transactions for your wallets.
      #args is None
      print 'BDM is ready!'
      print ''
      
      printWalletBalance()
      
   elif signal == NEW_BLOCK_ACTION:
      #This signal indicates a new block has been parsed by the BDM. As with
      #FINISH_LOAD_BLOCKCHAIN_ACTION, all wallets history has been updated
      #before the signal was emitted.
      
      #args is an integer list with only one element, the current top block
      #height. 

      newBlocks = args[0]
      if newBlocks>0:       
         print 'New Block: ', TheBDM.getTopBlockHeight()
         print ''
         
         printWalletBalance()


################################################################################
################################################################################
################################################################################

#Register the BDM callback
TheBDM.registerCppNotification(BDM_callback)

# Register our wallet with the BDM.
# Pass False during registration because we don't know if the wallet is new. 
# The BDM will make sure the history is up to date before signaling our callback
wlt.registerWallet(False)

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

while(True):
   time.sleep(1)


