'''
The BDM stands for Block Data Manager. It maintains the history for all 
registered wallets. 

The BDV is a read only layer on top of the BDM that makes wallet and
transaction history accessible to client applications.

In this example, we will list all supporting txouts for the provided transaction
hash, as well as all transaction in which its txouts have been spent, if any. 

This example only works in supernode
This example needs one argument, the hash of the transaction to trace.
'''

import sys
sys.path.append('..')
from armoryengine.ALL import *

cv = threading.Condition(None)

################################################################################
def traceTransactionByhash(txHash):
   print ''
   print 'Tracing history for transaction: ' + txHash
   
   #get the transaction
   Tx = TheBDM.bdv().getTxByHash(hex_to_binary(txHash, endIn=BIGENDIAN, endOut=LITTLEENDIAN))
   
   #print Tx data:
   print 'Transaction is #' + str(Tx.getBlockTxIndex()) + ' in block #' +\
          str(Tx.getBlockHeight())
          
   #print supporting TxOut data
   print '--- Supporting TxOuts:'
   for i in range(0, Tx.getNumTxIn()):
      
      TxIn = Tx.getTxInCopy(i)
      outpoint = TxIn.getOutPoint()
      TxOut = TheBDM.bdv().getTxOutCopy(outpoint.getTxHash(), outpoint.getTxOutIndex())
      
      
      print '   TxIn #' + str(i) + ':'
      print '      parent Tx Hash: ' + binary_to_hex(outpoint.getTxHash(), \
                                                     endOut=BIGENDIAN)
      print '      parent Tx Block Height: ' + str(TxOut.getParentHeight())
      print '      parent Tx Index: ' + str(TxOut.getIndex())
      print '      supporting TxOut Id: ' + str(outpoint.getTxOutIndex())
      print '      supporting TxOut ScrAddr: ' + scrAddr_to_addrStr(TxOut.getScrAddressStr())
      print '      supporting TxOut value: ' + coin2str(TxOut.getValue())
      print '   +++'
   
   print ''
   print '--- Spent TxOuts:'
   for i in range (0, Tx.getNumTxOut()):
      
      TxOut = Tx.getTxOutCopy(i)
      spenderTx = TheBDM.bdv().getSpenderTxForTxOut(Tx.getBlockHeight(), Tx.getBlockTxIndex(), i)
      isSpent = False
      if spenderTx.isInitialized():
         isSpent = True
      
      print '   TxOut #' + str(i) + ':'
      print '      TxOut ScrAddr: ' + scrAddr_to_addrStr(TxOut.getScrAddressStr())
      print '      TxOut value: ' + coin2str(TxOut.getValue())
      print '      Spent: ' + str(isSpent) 
      if isSpent:
         print '      Spender Tx Hash: ' + binary_to_hex(spenderTx.getThisHash(), \
                                                         endOut=BIGENDIAN)
         print '      Spender Tx Block Height: ' + str(spenderTx.getBlockHeight())
         print '      Spender Tx Index: ' + str(spenderTx.getBlockTxIndex())
      print '   +++'
   
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

      traceTransactionByhash(CLI_ARGS[0])

################################################################################
################################################################################
################################################################################

#Register the BDM callback
TheBDM.registerCppNotification(BDM_callback)

# Register our wallet with the BDM.
# Pass False during registration because we don't know if the wallet is new. 
# The BDM will make sure the history is up to date before signaling our callback

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
