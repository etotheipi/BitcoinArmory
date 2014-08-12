# This is a sample plugin file that will be used to create a new tab 
# in the Armory main window.  All plugin files (such as this one) will 
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this 
# file can use any utils or objects accessible to functions in ArmoryQt.py.

import ast
import urllib2

from PyQt4.Qt import QPushButton, SIGNAL, Qt, QLineEdit, QTableWidget, \
   QGridLayout, QSpacerItem, QWidget, QScrollArea, QTableWidgetItem

from armorycolors import htmlColor
from armoryengine.ArmoryUtils import RightNow, secondsToHumanTime, coin2str
from armoryengine.BDM import TheBDM
from qtdefines import makeHorizFrame, makeVertFrame, STYLE_PLAIN, QRichLabel, \
   GETFONT


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

   tabName = 'Exchange Rates'
   maxVersion = '0.92'
   
   #############################################################################
   def __init__(self, main):

      self.main = main

      ##########################################################################
      ##### Display the conversion values based on the Coinbase API
      self.lastPriceFetch = 0
      self.lblHeader    = QRichLabel(tr("""<b>Tracking buy and sell prices on 
         Coinbase every 60 seconds</b>"""), doWrap=False)
      self.lblLastTime  = QRichLabel('', doWrap=False)
      self.lblSellLabel = QRichLabel(tr('Coinbase <b>Sell</b> Price (USD):'), doWrap=False)
      self.lblBuyLabel  = QRichLabel(tr('Coinbase <b>Buy</b> Price (USD):'),  doWrap=False)
      self.lblSellPrice = QRichLabel('<Not Available>')
      self.lblBuyPrice  = QRichLabel('<Not Available>')

      self.lastSellStr = ''
      self.lastBuyStr = ''

      self.btnUpdate = QPushButton(tr('Check Now'))
      self.main.connect(self.btnUpdate, SIGNAL('clicked()'), self.checkUpdatePrice)

      ##########################################################################
      ##### A calculator for converting prices between USD and BTC
      lblCalcTitle = QRichLabel(tr("""Convert between USD and BTC using 
         Coinbase sell price"""), hAlign=Qt.AlignHCenter, doWrap=False)
      self.edtEnterUSD = QLineEdit()
      self.edtEnterBTC = QLineEdit()
      self.lblEnterUSD1 = QRichLabel('$')
      self.lblEnterUSD2 = QRichLabel('USD')
      self.lblEnterBTC = QRichLabel('BTC')
      btnClear = QPushButton('Clear')

      self.main.connect(self.edtEnterUSD, SIGNAL('textEdited(QString)'), self.updateCalcBTC)
      self.main.connect(self.edtEnterBTC, SIGNAL('textEdited(QString)'), self.updateCalcUSD)

      def clearCalc():
         self.edtEnterUSD.setText('')
         self.edtEnterBTC.setText('')

      self.main.connect(btnClear, SIGNAL('clicked()'), clearCalc)

      frmCalcMid = makeHorizFrame( [self.lblEnterUSD1,
                                    self.edtEnterUSD,
                                    self.lblEnterUSD2,
                                    'Stretch',
                                    self.edtEnterBTC,
                                    self.lblEnterBTC])

      frmCalcClear = makeHorizFrame(['Stretch', btnClear, 'Stretch'])
      frmCalc = makeVertFrame([lblCalcTitle, frmCalcMid, frmCalcClear], STYLE_PLAIN)

      ##########################################################################
      ##### A table showing you the total balance of each wallet in USD and BTC
      lblWltTableTitle = QRichLabel(tr("Wallet balances converted to USD"), 
                                            doWrap=False, hAlign=Qt.AlignHCenter)
      numWallets = len(self.main.walletMap)
      self.wltTable = QTableWidget(self.main)
      self.wltTable.setRowCount(numWallets)
      self.wltTable.setColumnCount(4)
      self.wltTable.horizontalHeader().setStretchLastSection(True)
      self.wltTable.setMinimumWidth(600)


      ##########################################################################
      ##### Setup the main layout for the tab
      mainLayout = QGridLayout()
      i=0
      mainLayout.addWidget(self.lblHeader,      i,0,  1,3)
      i+=1
      mainLayout.addItem(QSpacerItem(15,15),    i,0)
      mainLayout.addWidget(self.lblSellLabel,   i,1)
      mainLayout.addWidget(self.lblSellPrice,   i,2)
      i+=1
      mainLayout.addItem(QSpacerItem(15,15),    i,0)
      mainLayout.addWidget(self.lblBuyLabel,    i,1)
      mainLayout.addWidget(self.lblBuyPrice,    i,2)
      i+=1
      mainLayout.addWidget(self.lblLastTime,    i,0,  1,2)
      mainLayout.addWidget(self.btnUpdate,      i,2)
      i+=1
      mainLayout.addItem(QSpacerItem(20,20),    i,0)
      i+=1
      mainLayout.addWidget(frmCalc,             i,0,  1,3)
      i+=1
      mainLayout.addItem(QSpacerItem(30,30),    i,0)
      i+=1
      mainLayout.addWidget(lblWltTableTitle,    i,0,  1,3)
      i+=1
      mainLayout.addWidget(self.wltTable,       i,0,  1,3)

      mainLayout.setColumnStretch(0,0)
      mainLayout.setColumnStretch(1,1)
      mainLayout.setColumnStretch(2,1)
      tabWidget = QWidget()
      tabWidget.setLayout(mainLayout)

      frmH = makeHorizFrame(['Stretch', tabWidget, 'Stretch'])
      frm  = makeVertFrame(['Space(20)', frmH, 'Stretch'])


      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(frm)


   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay


   #############################################################################
   def addCommasToPrice(self, pstr):
      dispStr = pstr.strip().split('.')[0] 
      dispStr = ','.join([dispStr[::-1][3*i:3*(i+1)][::-1] \
                            for i in range((len(dispStr)-1)/3+1)][::-1])
      if '.' in pstr:
         dispStr = dispStr + '.' + pstr.split('.')[1]
      return dispStr


   #############################################################################
   def fetchFormattedPrice(self, url):
      sock = urllib2.urlopen(url)
      value = ast.literal_eval(sock.read())['subtotal']['amount']
      return self.addCommasToPrice(value)



   #############################################################################
   def checkUpdatePrice(self):

      urlBase = 'http://coinbase.com/api/v1/prices/'
      urlSell = urlBase + 'sell'
      urlBuy  = urlBase + 'buy'

      try:
         self.lastSellStr = self.fetchFormattedPrice(urlSell)
         self.lastBuyStr  = self.fetchFormattedPrice(urlBuy)
         
         self.lblSellPrice.setText('<b><font color="%s">$%s</font> / BTC</b>' % \
                                           (htmlColor('TextBlue'), self.lastSellStr))
         self.lblBuyPrice.setText( '<b><font color="%s">$%s</font> / BTC</b>' % \
                                           (htmlColor('TextBlue'), self.lastBuyStr))
      
         self.lastPriceFetch = RightNow()

         self.updateLastTimeStr()
         self.updateWalletTable()
         self.updateCalcUSD(self.edtEnterBTC.text())
      except:
         #LOGEXCEPT('Failed to fetch price data from %s' % urlBase)
         pass

   

   #############################################################################
   def updateLastTimeStr(self):
      secs = RightNow() - self.lastPriceFetch
      tstr = 'Less than 1 min'
      if secs > 60:
         tstr = secondsToHumanTime(secs)

      self.lblLastTime.setText(tr("""<font color="%s">Last updated:  
         %s ago</font>""") % (htmlColor('DisableFG'), tstr))

   #############################################################################
   def injectGoOnlineFunc(self, topBlock):
      self.checkUpdatePrice()

   #############################################################################
   def injectHeartbeatAlwaysFunc(self):
      # Check the price every 60 seconds, update widgets
      self.updateLastTimeStr()
      if RightNow() < self.lastPriceFetch+60:
         return

      self.lastPriceFetch = RightNow()
      self.checkUpdatePrice() 


   #############################################################################
   def updateCalcUSD(self, newBTCVal):
      try:
         convertVal = float(self.lastSellStr.replace(',',''))
         usdVal = convertVal * float(newBTCVal.replace(',',''))
         self.edtEnterUSD.setText(self.addCommasToPrice('%0.2f' % usdVal))
      except:
         self.edtEnterUSD.setText('')
         
   #############################################################################
   def updateCalcBTC(self, newUSDVal):
      try:
         convertVal = float(self.lastSellStr.replace(',',''))
         btcVal = float(newUSDVal.replace(',','')) / convertVal
         self.edtEnterBTC.setText(self.addCommasToPrice('%0.8f' % btcVal))
      except:
         self.edtEnterBTC.setText('')
      
      
   #############################################################################
   def updateWalletTable(self):
      numWallets = len(self.main.walletMap)
      self.wltTable.setRowCount(numWallets)
      self.wltTable.setColumnCount(4)

      row = 0
      for wltID,wltObj in self.main.walletMap.iteritems():
         wltValueBTC = '(...)'
         wltValueUSD = '(...)'
         if TheBDM.getBDMState()=='BlockchainReady':
            convertVal = float(self.lastSellStr.replace(',',''))
            wltBal = wltObj.getBalance('Total')
            wltValueBTC = coin2str(wltBal, maxZeros=2)
            wltValueUSD = '$' + self.addCommasToPrice('%0.2f' % (wltBal*convertVal/1e8))

         rowItems = []
         rowItems.append(QTableWidgetItem(wltID))
         rowItems.append(QTableWidgetItem(wltObj.labelName))
         rowItems.append(QTableWidgetItem(wltValueBTC))
         rowItems.append(QTableWidgetItem(wltValueUSD))

         rowItems[-2].setTextAlignment(Qt.AlignRight)
         rowItems[-1].setTextAlignment(Qt.AlignRight)
         rowItems[-2].setFont(GETFONT('Fixed', 10))
         rowItems[-1].setFont(GETFONT('Fixed', 10))

         for i,item in enumerate(rowItems):
            self.wltTable.setItem(row, i, item)
            item.setFlags(Qt.NoItemFlags)

         self.wltTable.setHorizontalHeaderItem(0, QTableWidgetItem(tr('Wallet ID')))
         self.wltTable.setHorizontalHeaderItem(1, QTableWidgetItem(tr('Wallet Name')))
         self.wltTable.setHorizontalHeaderItem(2, QTableWidgetItem(tr('BTC Balance')))
         self.wltTable.setHorizontalHeaderItem(3, QTableWidgetItem(tr('USD ($) Value')))
         self.wltTable.verticalHeader().hide()

         row += 1
      
