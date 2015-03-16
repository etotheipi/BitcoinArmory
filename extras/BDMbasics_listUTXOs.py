'''
The BDM stands for Block Data Manager. It maintains the history for all 
registered wallets. 

In this example, we will list all unpsent txouts for our wallet. 

This example needs one argument, the path to the wallet to monitor.
'''

from armoryengine.ALL import *

cv = threading.Condition(None)

#load wallet from file
wlt = PyBtcWallet().readWalletFile( CLI_ARGS[0] )

################################################################################
def listUTXOs():
   #get the UTXOs from the wallet
   utxos = wlt.getFullUTXOList()
   
   print ''
   print 'printing UTXOs for wallet: ' + wlt.uniqueIDB58
   print '---------------'
   
   pprintUnspentTxOutList(utxos)
   
   #we're done, let's signal the waiting main thread to move on
   cv.acquire()
   cv.notify_all()
   cv.release()

################################################################################
def BDM_callback(signal, args):
   '''
   This is a prototype callback method. It has to take 2 arguments:
      1) signal: the type of signal received from the BDM
      2) args: an object containing the extra arguments passed to the callback, 
         dependant on the signal type 
         
      Once this callback is registered with the BDM, it will receive all
      notifications from the BDM. Notification you don't need handle can simply
      be ignored
   '''
   
   if signal == FINISH_LOAD_BLOCKCHAIN_ACTION:
      #This signal indicates the BDM has finished initializing. All wallet 
      #history is up to date on the BDM side. At this point
      #you can query balance and create transactions for your wallets.
      #args is None
      print 'BDM is ready!'
      print ''

      listUTXOs()

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
own loop, otherwise it would exit and shutdown our entire process. 

Here we have nothing to do so we'll have the main thread wait on a condition
variable that listUTXOs will notify once it is done, which will result in the
main thread exiting and the subsequent termination of the process.
'''

cv.acquire()
cv.wait()
cv.release()
   
print 'exiting'
