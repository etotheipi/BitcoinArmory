#! /usr/bin/python
import sys
sys.path.append('..')
sys.path.append('.')

from armoryengine import *
import getpass
from sys import argv
import os

# Do not ever access the same wallet file from two different processes at the same time
print '\n'
raw_input('PLEASE CLOSE ARMORY BEFORE RUNNING THIS SCRIPT!  (press enter to continue)\n')

if len(argv)<3:
   print 'USAGE: %s <wallet file> <unsigned.tx file>' % argv[0]
   exit(0)

wltfile  = argv[1]
txdpfile = argv[2]

if not os.path.exists(wltfile):
   print 'Wallet file was not found: %s' % wltfile

if not os.path.exists(txdpfile):
   print 'Transaction file was not found: %s' % txdpfile

wlt  = PyBtcWallet().readWalletFile(wltfile)
txdp = PyTxDistProposal().unserializeAscii( open(txdpfile,'r').read())

for a160 in txdp.inAddr20Lists:
   if not wlt.hasAddr(a160[0]):
      print 'ERROR: Not all transaction inputs can be signed by this wallet!'
      print '       Did you supply the correct wallet?'
      exit(0)

print '********************************************************************************'
print 'PLEASE VERIFY THE TRANSACTION DETAILS BEFORE SIGNING'
print '********************************************************************************'

btcIn  = sum(txdp.inputValues)
btcOut = sum([o.value for o in txdp.pytxObj.outputs])
btcFee = btcIn - btcOut

print '   INPUTS:  (%s)' % coin2str(btcIn).strip()
for i,a160 in enumerate(txdp.inAddr20Lists):
   print    '      %s          -->\t%s' % (hash160_to_addrStr(a160[0]), coin2str(txdp.inputValues[i]))

print '   OUTPUTS: (%s)' % coin2str(btcOut).strip()
for i,txout in enumerate(txdp.pytxObj.outputs):
   a160 = TxOutScriptExtractAddr160(txout.binScript)
   if wlt.hasAddr(a160):
      print '      %s (change) <--\t%s' % (hash160_to_addrStr(a160), coin2str(txout.value))
   else:
      print '      %s          <--\t%s' % (hash160_to_addrStr(a160), coin2str(txout.value))
print '      %s          <--\t%s' % ('Fee'.ljust(34), coin2str(btcFee))

confirm = raw_input('\nDoes this look right?  [y/N]: ')
if not confirm.lower().startswith('y'):
   print 'User did not approve of the transaction.  Aborting.'
   exit(0)


# If the wallet is encrypted, get the passphrase
if wlt.useEncryption:
   print 'Please enter your passphrase to unlock your wallet: '
   for ntries in range(3):
      passwd = SecureBinaryData(getpass.getpass('Wallet Passphrase: '))
      if wlt.verifyPassphrase(passwd):
         break;

      print 'Passphrase was incorrect!'
      if ntries==2:
         print 'Wallet could not be unlocked.  Aborting.'
         exit(0)

   print 'Correct Passphrase.  Unlocking wallet...'
   wlt.unlock(securePassphrase=passwd)
   passwd.destroy()


try:
   wlt.signTxDistProposal(txdp)
except WalletLockError:
   print 'Error signing transaction.  Wallet is somehow still locked'
   raise
except:
   print 'Error signing transaction.  Unknown reason.'
   raise
     
if not txdp.checkTxHasEnoughSignatures():
   print 'Error signing transaction.  Most likely this is not the correct wallet.'
   exit(0)

outfilename = '.'.join(txdpfile.split('.')[:-2] + ['signed.tx'] )
outfile = open(outfilename, 'w')
outfile.write(txdp.serializeAscii())
outfile.close()
print '\nSigning was successful!  The signed transaction is located:'
print '\t', outfilename, '\n'
doDelete = raw_input('Would you like to delete the old unsigned transaction? [Y/n]: ')
if not doDelete.lower().startswith('n'):
   os.remove(txdpfile) 

print ''
print 'The *.signed.tx file can now be broadcast from any computer running '
print 'Armory in online mode.  Click "Offline Transactions" and "Broadcast".'
print ''
