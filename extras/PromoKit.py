################################################################################
#
# Copyright (C) 2011-2014, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################

from getpass import getpass
import sys

from pywin.scintilla import view
from PyQt4.QtGui import *

from armorycolors import htmlColor, Colors
from armoryengine import *
from qtdefines import GETFONT, tr
from qtdialogs import SimplePrintableGraphicsScene
from utilities.ArmoryUtils import encodePrivKeyBase58, ComputeFragIDLineHex, \
   makeSixteenBytesEasy, pprintHex


sys.path.append('..')
sys.path.append('.')
   

def createWalletList(n, nameString, descriptionString):
   walletList = []
   for i in range(n):
      name = "%s #%d" % (nameString, i)
      newWallet = PyBtcWallet().createNewWallet( \
                                           withEncrypt=False, \
                                           shortLabel=name, \
                                           longLabel=descriptionString, \
                                           doRegisterWithBDM=False)
      walletList.append(newWallet)
   return walletList

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
         from the website shown above. After you install the software sweep the contents to a new
         wallet or any address that you own. Do not deposit any bitcoins to this wallet. You
         don't know where this paper has been! You have until %s to sweep the contents. After
         this date we will sweep this wallet to recover all unclaimed bitcoins.""" %
         (amountString, expiresString)), GETFONT('Var', 11), wrapWidth=wrap)
      
   scene.newLine(extra_dy=25)
   return scene
   
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

walletList = createWalletList(12, 'Inside Bitcoin 2013 -- ', 'Inside Bitcoins Las Vegas 2013 Promotional Wallet')
printWalletList(walletList, "who knows how many bitcoins!?", "January 1st, 2014")
