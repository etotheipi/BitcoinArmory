################################################################################
#
# Copyright (C) 2011-2014, Armory Technologies, Inc.                         
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################

from getpass import getpass
import os
import sys
# Must move and clear the Args list before importing anything
# Otherwise it will process the args for this script.
promoKitArgList = sys.argv
# Clear and add --testnet unless you are running this on main net
sys.argv = sys.argv[:1]
import time

from PyQt4.QtGui import *
from pywin.scintilla import view
from armoryengine.PyBtcWallet import PyBtcWallet
from CppBlockUtils import SecureBinaryData
from armoryengine.ArmoryUtils import makeSixteenBytesEasy, NegativeValueError, \
   WalletAddressError, MIN_RELAY_TX_FEE, LOGINFO, hash160_to_p2pkhash_script
from armoryengine.BDM import TheBDM
from armoryengine.CoinSelection import calcMinSuggestedFees, PySelectCoins
from armoryengine.Transaction import UnsignedTransaction
from qtdefines import GETFONT, tr
from qtdialogs import SimplePrintableGraphicsScene



   
sys.path.append('..')
sys.path.append('.')


# Generates a list of new promo wallets
def createWalletList(n, nameString):
   walletList = []
   for i in range(n):
      name = "%s #%d" % (nameString, i)
      newWallet = PyBtcWallet().createNewWallet( \
                                           withEncrypt=False, \
                                           shortLabel=name, \
                                           longLabel=name, \
                                           doRegisterWithBDM=False)
      walletList.append(newWallet)
   return walletList

# Pulled from qtdialogs. Assumes single sheet 1.35c backups
def createPrintScene(wallet, amountString, expiresString):
   
   scene = SimplePrintableGraphicsScene(None, None)

   INCH = scene.INCH
   MARGIN = scene.MARGIN_PIXELS 
   scene.resetCursor()
   scene.drawPixmapFile(':/armory_logo_h36.png') 
   scene.newLine()
   scene.drawText('Paper Backup for Armory Wallet', GETFONT('Var', 11))
   scene.newLine()
   scene.drawText('http://www.bitcoinarmory.com')

   scene.newLine(extra_dy=20)
   scene.drawHLine()
   scene.newLine(extra_dy=20)


   ssType = ' (Unencrypted)'
   bType = tr('Single-Sheet ' + ssType)
   colRect, rowHgt = scene.drawColumn(['Wallet Version:', 'Wallet ID:', \
                                                'Wallet Name:', 'Backup Type:'])
   scene.moveCursor(15, 0)
   suf = 'c'
   colRect, rowHgt = scene.drawColumn(['1.35'+suf, wallet.uniqueIDB58, \
                                                wallet.labelName, bType])
   scene.moveCursor(15, colRect.y() + colRect.height(), absolute=True)

   # Display warning about unprotected key data
   wrap = 0.9*scene.pageRect().width()

   container = 'this wallet'
   warnMsg = tr(""" 
         <font color="#aa0000"><b>WARNING:</b></font> Anyone who has access to this 
         page has access to all the bitcoins in %s!  Please keep this 
         page in a safe place.""" % container)

   scene.newLine()
   scene.drawText(warnMsg, GETFONT('Var', 9), wrapWidth=wrap)

   scene.newLine(extra_dy=20)
   scene.drawHLine()
   scene.newLine(extra_dy=20)
   numLine = 'two'

   descrMsg = tr(""" 
      The following %s lines backup all addresses 
      <i>ever generated</i> by this wallet (previous and future).
      This can be used to recover your wallet if you forget your passphrase or 
      suffer hardware failure and lose your wallet files. """ % numLine)
   scene.drawText(descrMsg, GETFONT('var', 8), wrapWidth=wrap)
   scene.newLine(extra_dy=10)
  
   ###########################################################################
   # Finally, draw the backup information.
   bottomOfSceneHeader = scene.cursorPos.y()

   code12 = wallet.addrMap['ROOT'].binPrivKey32_Plain.toBinStr()
   Lines = []
   Prefix = [] 
   Prefix.append('Root Key:')
   Lines.append(makeSixteenBytesEasy(code12[:16]))
   Prefix.append('')
   Lines.append(makeSixteenBytesEasy(code12[16:]))
   # Draw the prefix
   origX,origY = scene.getCursorXY()
   scene.moveCursor(20,0) 
   colRect, rowHgt = scene.drawColumn(['<b>'+l+'</b>' for l in Prefix])
   
   nudgeDown = 2  # because the differing font size makes it look unaligned
   scene.moveCursor(20, nudgeDown)
   scene.drawColumn(Lines, 
                    
                           font=GETFONT('Fixed', 8, bold=True), \
                           rowHeight=rowHgt, 
                           useHtml=False)

   scene.moveCursor(MARGIN, colRect.y()-2, absolute=True)
   width = scene.pageRect().width() - 2*MARGIN
   scene.drawRect( width, colRect.height()+7, edgeColor=QColor(0,0,0), fillColor=None)

   scene.newLine(extra_dy=30)
   scene.drawText( tr("""
      The following QR code is for convenience only.  It contains the 
      exact same data as the %s lines above.  If you copy this backup 
      by hand, you can safely ignore this QR code. """ % numLine), wrapWidth=4*INCH)

   scene.moveCursor(20,0)
   x,y = scene.getCursorXY()
   edgeRgt = scene.pageRect().width() - MARGIN
   edgeBot = scene.pageRect().height() - MARGIN

   qrSize = max(1.5*INCH, min(edgeRgt - x, edgeBot - y, 2.0*INCH))
   scene.drawQR('\n'.join(Lines), qrSize)
   scene.newLine(extra_dy=25)
   scene.drawHLine(7*INCH, 5)
   scene.newLine(extra_dy=25)
   scene.drawText(tr(""" 
         <font color="#aa0000"><b>CONGRATULATIONS:</b></font> You have received a Bitcoin Armory
         promotional wallet containing %s You may collect this money by installing Bitcoin Armory
         from the website shown above. After you install the software move the funds to a new
         wallet or any address that you own. Do not deposit any bitcoins to this wallet. You
         don't know where this paper has been! You have until %s to claim your bitcoins. After
         this date we will remove all remaining bitcoins from this wallet.""" %
         (amountString, expiresString)), GETFONT('Var', 11), wrapWidth=wrap)
      
   scene.newLine(extra_dy=25)
   return scene

# This function will display a print dialog. It may hide behind other windows
def printWalletList(walletList, amountString, expiresString):
   printer = QPrinter(QPrinter.HighResolution)
   printer.setPageSize(QPrinter.Letter)

   if QPrintDialog(printer).exec_():
      painter = QPainter(printer)
      painter.setRenderHint(QPainter.TextAntialiasing)
      for wallet in walletList:
         scene = createPrintScene(wallet, amountString, expiresString)
         scene.getScene().render(painter)
         if wallet != walletList[-1]:
            printer.newPage()
      painter.end()

# Assumes a secure wallet has been created and is provided. There should not be any
# imported addresses in this wallet. It is assumed that all of this wallet's imported 
# addresses are about to be imported in this function
def importAddrsToMasterWallet(masterWallet, walletList, addrsPerWallet, masterWalletName):
   masterWallet.unlock(securePassphrase = SecureBinaryData(getpass('Enter your secret string:')))
   for wallet in walletList:
      for i in range(addrsPerWallet):
         addr = wallet.getNextUnusedAddress()
         masterWallet.importExternalAddressData(privKey = addr.binPrivKey32_Plain,
                                                pubKey = addr.binPublicKey65)
   return masterWallet

# Distribute amount to each imported address in the wallet.
def distributeBtc(masterWallet, amount, sendingAddrList):
   pytx = None
   setupTheBDM()
   try:
      recipValuePairs = []
      utxoList = []
      for sendingAddr in sendingAddrList:
         addr160 = sendingAddr.getAddr160()
         # Make sure the sending addresses are in the masterWallet
         if not masterWallet.hasAddr(addr160):
            raise WalletAddressError, 'Address is not in wallet! [%s]' % sendingAddr.getAddrStr()
         utxoList.extend(masterWallet.getAddrTxOutList(addr160))
   

      for importedAddr in masterWallet.getLinearAddrList():
         if importedAddr.chainIndex<0:
            recipValuePairs.append((importedAddr.getAddr160(),amount))
      totalSpend = len(recipValuePairs)*amount
      fee = calcMinSuggestedFees(utxoList, totalSpend, MIN_RELAY_TX_FEE, len(recipValuePairs))[1]
      # Get the necessary utxo list
      selectedUtxoList = PySelectCoins(utxoList, totalSpend, fee)
      # get total value   
      totalAvailable = sum([u.getValue() for u in selectedUtxoList])
      totalChange = totalAvailable - (totalSpend + fee)

      # Make sure there are funds to cover the transaction.
      if totalChange < 0:
         print '***ERROR: you are trying to spend more than your balance!'
         raise NegativeValueError
      recipValuePairs.append((masterWallet.getNextUnusedAddress().getAddr160(), totalChange ))

      # ACR:  To support P2SH in general, had to change createFromTxOutSelection
      #       to take full scripts, not just hash160 values.  Convert the list
      #       before passing it in
      scrPairs = [[hash160_to_p2pkhash_script(r), v] for r,v in recipValuePairs]
      txdp = UnsignedTransaction().createFromTxOutSelection(selectedUtxoList, scrPairs)
      
      masterWallet.unlock(securePassphrase = SecureBinaryData(getpass('Enter your secret string:')))
      # Sign and prepare the final transaction for broadcast
      masterWallet.signTxDistProposal(txdp)
      pytx = txdp.getPyTxSignedIfPossible()
   
      print '\nSigned transaction to be broadcast using Armory "offline transactions"...'
      print txdp.serializeAscii()
   finally:
      TheBDM.execCleanShutdown()
   return pytx

def setupTheBDM():
   TheBDM.setBlocking(True)
   if not TheBDM.isInitialized():
      TheBDM.registerWallet(masterWallet)
      TheBDM.setOnlineMode(True)
      # Only executed on the first call if blockchain not loaded yet.
      LOGINFO('Blockchain loading')
      while not TheBDM.getBDMState()=='BlockchainReady':
         LOGINFO('Blockchain Not Ready Yet %s' % TheBDM.getBDMState())
         time.sleep(2)
# Sweep all of the funds from the imported addrs back to a
# new addrin the master wallet
def sweepImportedAddrs(masterWallet):
   setupTheBDM()
   recipValuePairs = []
   utxoList = []
   for importedAddr in masterWallet.getLinearAddrList():
      if importedAddr.chainIndex<0:
         addr160 = importedAddr.getAddr160()
         utxoList.extend(masterWallet.getAddrTxOutList(addr160))

   # get total value   
   totalAvailable = sum([u.getValue() for u in utxoList])
   fee = calcMinSuggestedFees(utxoList, totalAvailable, MIN_RELAY_TX_FEE, 1)[1]
   totalSpend = totalAvailable - fee
   if totalSpend<0:
      print '***ERROR: The fees are greater than the funds being swept!'
      raise NegativeValueError
   recipValuePairs.append((masterWallet.getNextUnusedAddress().getAddr160(), totalSpend ))

   # ACR:  To support P2SH in general, had to change createFromTxOutSelection
   #       to take full scripts, not just hash160 values.  Convert the list
   #       before passing it in
   scrPairs = [[hash160_to_p2pkhash_script(r), v] for r,v in recipValuePairs]
   txdp = UnsignedTransaction().createFromTxOutSelection(utxoList, scrPairs)
   
   masterWallet.unlock(securePassphrase = SecureBinaryData(getpass('Enter your secret string:')))
   # Sign and prepare the final transaction for broadcast
   masterWallet.signTxDistProposal(txdp)
   pytx = txdp.getPyTxSignedIfPossible()

   print '\nSigned transaction to be broadcast using Armory "offline transactions"...'
   print txdp.serializeAscii()
   return pytx


# Example execution generates 3 promo wallets and imports 2 address each to 
# a master wallet that is provided
'''
walletList = createWalletList(100, 'Cambridge Bitcoin Meetup')
masterWallet = importAddrsToMasterWallet( \
    PyBtcWallet().readWalletFile('C:\\Users\\Andy\\AppData\\Roaming\\Armory\\armory_28Xrf4hbu_.wallet', False, False),\
    walletList, 2, "Master Promo Wallet")
printWalletList(walletList, "who knows how many bitcoins!?", "April 1st, 2014")
'''

# Example execution distribute .0001 Btc to each imported address in a master wallet
'''
masterWallet = PyBtcWallet().readWalletFile('C:\\Users\\Andy\\AppData\\Roaming\\Armory\\testnet3\\armory_2hzEdtr9c_.wallet', False, False)
pytx = distributeBtc(masterWallet, 10000, masterWallet.getLinearAddrList(withImported=False))
'''

# Show help whenever the args are not correct
def printHelp():
   print 'USAGE: %s --create <master wallet file path> <number of promo wallets> <addrs per promo wallet> <promo wallet label>' % sys.argv[0]
   print '   or: %s --distribute <master wallet file path> <satoshis per addr>' % sys.argv[0]
   print '   or: %s --sweep <master wallet file path>' % sys.argv[0]
   exit(0)
   
# Main execution path
# Do not ever access the same wallet file from two different processes at the same time
print '\n'
raw_input('PLEASE CLOSE ARMORY BEFORE RUNNING THIS SCRIPT!  (press enter to continue)\n')

if len(promoKitArgList)<3:
   printHelp()

operation = promoKitArgList[1]
walletFile = promoKitArgList[2]
if not os.path.exists(walletFile):
   print 'Wallet file was not found: %s' % walletFile
masterWallet = PyBtcWallet().readWalletFile(walletFile, False, False)
if operation == '--create':
   if len(promoKitArgList)<6:
      printHelp()
   else:
      numWallets = int(promoKitArgList[3])
      addrsPerWallet = int(promoKitArgList[4])
      walletLabel = promoKitArgList[5]
      walletList = createWalletList(numWallets, walletLabel)
      masterWallet = importAddrsToMasterWallet( \
            masterWallet, walletList, addrsPerWallet, "Master Promo Wallet", )
      # Didn't want to fit these into the argument list. Need to edit based on event
      printWalletList(walletList, "some amount of bitcoin. ", "July 1st, 2014")
elif operation == '--distribute':
   if len(promoKitArgList)<4:
      printHelp()
   else:
      amountPerAddr = int(promoKitArgList[3])
      distributeBtc(masterWallet, amountPerAddr, masterWallet.getLinearAddrList(withImported=False))
elif operation == '--sweep':
      sweepImportedAddrs(masterWallet)
else:
   printHelp()
