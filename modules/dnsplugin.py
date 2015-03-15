# This is a sample plugin file that will be used to create a new tab 
# in the Armory main window.  All plugin files (such as this one) will 
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this 
# file can use any utils or objects accessible to functions in ArmoryQt.py.

import sys
import ast
import urllib2
import getdns

from PyQt4.Qt import QPushButton, SIGNAL, Qt, QLineEdit, QTableWidget, \
   QGridLayout, QSpacerItem, QWidget, QScrollArea, QTableWidgetItem
from armorycolors import htmlColor
from armoryengine.ArmoryUtils import RightNow, secondsToHumanTime, coin2str, \
                                 sha224, binary_to_hex, hash160_to_addrStr, LOGERROR
from armoryengine.BDM import TheBDM, BDM_BLOCKCHAIN_READY
from qtdefines import makeHorizFrame, makeVertFrame, STYLE_PLAIN, QRichLabel, \
                                GETFONT
from binascii import hexlify
from armoryengine.ConstructedScript import PublicKeySource
from dnssec_dane.daneHandler import getDANERecord, BTCAID_PAYLOAD_TYPE


# ArmoryQt will access this by importing PluginObject and initializing one
#   -- It adds plugin.getTabToDisplay() to the main window tab list
#   -- It uses plugin.tabName as the label for that tab.
#   -- It uses plugin.tabName as the label for that tab.
#
# Make sure you test your plugin not only when it's online, but also when
#   -- Armory is in offline mode, and internet is not accessible
#   -- Armory is in offline mode, and internet *is* accessible
#   -- User uses skip-offline-check so online, but service can't be reached
class PluginObject(object):

   tabName = 'DNSSEC Demo'
   maxVersion = '0.99'
   
   #############################################################################
   def __init__(self, main):

      self.main = main

      ##########################################################################
      ##### Display the conversion values based on the Coinbase API
      self.lblHeader    = QRichLabel(tr("<b>PMTA Record Fetcher</b>"""), doWrap=False)
      self.lblPayWho    = QRichLabel(tr("Who do you want to pay?"), doWrap=False)
      self.edtPayWho    = QLineEdit()
      self.btnFetch     = QPushButton('Fetch payment info')
      self.btnClear     = QPushButton('Clear')
      self.lblResult    = QRichLabel('')

      self.edtPayWho.setMaximumWidth(relaxedSizeNChar(self.edtPayWho, 50)[0])

      def clearCalc():
         self.edtPayWho.setText('')
         self.lblResult.setText('')

      self.main.connect(self.btnFetch, SIGNAL('clicked()'), self.fetchPMTA)
      self.main.connect(self.btnClear, SIGNAL('clicked()'), clearCalc)

      pluginFrame = makeVertFrame( [self.lblHeader,
                                    makeHorizFrame([self.lblPayWho, self.edtPayWho, 'Stretch']),
                                    self.lblResult,
                                    makeHorizFrame([self.btnFetch, self.btnClear, 'Stretch']),
                                    'Stretch'])

      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(pluginFrame)


   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay


   #############################################################################
   # Code lifted from armoryd. Need to place in a common space one day....
   def fetchPMTA(self):
      self.lblResult.setText('')
      inAddr = str(self.edtPayWho.text())

      retDict = {}
      userAddr = ''
      recordUser, recordDomain = inAddr.split('@', 1)
      sha224Res = sha224(recordUser)
      daneReqName = binary_to_hex(sha224Res) + '._pmta.' + recordDomain

      # Go out and get the DANE record.
      pmtaRecType, daneRec = getDANERecord(daneReqName)
      if pmtaRecType == BTCAID_PAYLOAD_TYPE.PublicKeySource:
         # HACK HACK HACK: Just assume we have a PKS record that is static and
         # has a Hash160 value.
         pksRec = PublicKeySource().unserialize(daneRec)

         # Convert Hash160 to Bitcoin address. Make sure we get a PKS, which we
         # won't if the checksum fails.
         if daneRec != None and pksRec != None:
            userAddr = hash160_to_addrStr(pksRec.rawSource, ADDRBYTE)
         else:
            raise InvalidDANESearchParam('PKS record is invalid.')

         self.lblResult.setText('Found static Public Key Source: %s' % userAddr)
      else:
         self.lblResult.setText(inAddr + " has no DANE record", color='DisableFG')
         raise InvalidDANESearchParam(inAddr + " has no DANE record")


      result = MsgBoxCustom(MSGBOX.Good, 'Found PMTA Record', tr("""
         Found static address from Public Key Source record: 
         <br><br>
         %s
         <br><br>
         Raw Record Data: %s<br>
         PKS Version: %d<br>
         isStatic: %d<br>
         useComp: %d<br>
         hash160: %d<br>
         isStealth: %d<br>
         isUserKey: %d<br>
         isExtSrc: %d<br>
         isChksumPres: %d<br>
         Hash160 value: %s<br>
         Checksum Value: %s
         <br><br>
         Would you like to create a payment to this address?""") %
         (userAddr, binary_to_hex(pksRec.serialize()), pksRec.version,
          pksRec.isStatic, len(pksRec.rawSource)==33, pksRec.useHash160,
          pksRec.isStealth, pksRec.isUserKey, pksRec.isExternalSrc,
          pksRec.isChksumPresent, binary_to_hex(pksRec.rawSource),
          binary_to_hex(pksRec.serialize()[-4:])),
         wCancel=True, yesStr='Create Payment')

      if result:
         firstWlt = self.main.walletMap[self.main.walletMap.keys()[0]]
         DlgSendBitcoins(firstWlt, self.main, self.main, {'address': userAddr}).exec_()

      return userAddr
