# This is a sample plugin file that will be used to create a new tab 
# in the Armory main window.  All plugin files (such as this one) will 
# be injected with the locals() from ArmoryQt.py, which includes pretty
# much 100% of Bitcoin & Armory related stuff that you need.  So this 
# file can use any utils or objects accessible to functions in ArmoryQt.py.

import urllib2


# Normally we create layouts like this inside of functions or dialogs.
# In plugins, all the top-level variables will be imported behind the 
# module (i.e.  plugin.topLevelVar), so the top-level space here behaves
# very much like a scoped namespace.  


class PluginObject(object):

   tabName = 'Exchange Rates'
   
   #############################################################################
   def __init__(self, parent):

      self.parent = parent

      self.lastPriceFetch = 0
      self.lblHeader    = QRichLabel(tr("""Tracking buy and sell prices on 
         Coinbase every 60 seconds"""), doWrap=False)
      self.lblLastTime  = QRichLabel('')
      self.lblSellLabel = QRichLabel(tr('Coinbase <b>Sell</b> Price (USD):'), doWrap=False)
      self.lblBuyLabel  = QRichLabel(tr('Coinbase <b>Buy</b> Price (USD):'),  doWrap=False)
      self.lblSellPrice = QRichLabel('<Not Available>')
      self.lblBuyPrice  = QRichLabel('<Not Available>')

      self.btnUpdate = QPushButton(tr('Check Now'))
      parent.connect(self.btnUpdate, SIGNAL('clicked()'), self.checkUpdatePrice)

      lblCalcTitle = QRichLabel(tr("""Convert between USD and BTC using 
         Coinbase sell price"""), hAlign=Qt.AlignHCenter, doWrap=False)
      self.edtEnterUSD = QLineEdit()
      self.edtEnterBTC = QLineEdit()
      self.lblEnterUSD = QRichLabel('USD ($)')
      self.lblEnterBTC = QRichLabel('BTC')
      btnClear = QPushButton('Clear')

      parent.connect(self.edtEnterUSD, SIGNAL('textEdited(QString)'), self.updateCalcBTC)
      parent.connect(self.edtEnterBTC, SIGNAL('textEdited(QString)'), self.updateCalcUSD)

      def clearCalc():
         self.edtEnterUSD.setText('')
         self.edtEnterBTC.setText('')

      parent.connect(btnClear, SIGNAL('clicked()'), clearCalc)

      frmCalcMid = makeHorizFrame( [self.edtEnterUSD,
                                    self.lblEnterUSD,
                                    'Stretch',
                                    self.edtEnterBTC,
                                    self.lblEnterBTC])

      frmCalcClear = makeHorizFrame(['Stretch', btnClear, 'Stretch'])
      frmCalc = makeVertFrame([lblCalcTitle, frmCalcMid, frmCalcClear], STYLE_PLAIN)

      mainLayout = QGridLayout()
      mainLayout.addWidget(self.lblHeader,      0,0,  1,3)
      mainLayout.addItem(QSpacerItem(15,15),    1,0)
      mainLayout.addWidget(self.lblSellLabel,   1,1)
      mainLayout.addWidget(self.lblSellPrice,   1,2)
      mainLayout.addItem(QSpacerItem(15,15),    2,0)
      mainLayout.addWidget(self.lblBuyLabel,    2,1)
      mainLayout.addWidget(self.lblBuyPrice,    2,2)
      mainLayout.addWidget(self.lblLastTime,    3,0,  1,3)
      mainLayout.addWidget(self.btnUpdate,      4,2)

      mainLayout.addItem(QSpacerItem(20,20),    5,1)

      mainLayout.addWidget(frmCalc,             6,0,  1,3)
      

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
      dispStr = pstr.split('.')[0] 
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
      except:
         LOGEXCEPT('Failed to fetch price data from %s' % urlBase)

      self.updateLastTimeStr()
   

   #############################################################################
   def updateLastTimeStr(self):
      secs = RightNow() - self.lastPriceFetch
      tstr = 'Less than 1 min'
      if secs > 60:
         tstr = secondsToHumanTime(secs)

      self.lblLastTime.setText(tr("""<font color="%s">Last updated:  
         %s ago</font>""") % (htmlColor('DisableFG'), tstr))


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
         LOGEXCEPT('ERR')  # delete me... just for debugging
         self.edtEnterUSD.setText('')
         
   #############################################################################
   def updateCalcBTC(self, newUSDVal):
      try:
         convertVal = float(self.lastSellStr.replace(',',''))
         btcVal = float(newUSDVal.replace(',','')) / convertVal
         self.edtEnterBTC.setText(self.addCommasToPrice('%0.8f' % btcVal))
      except:
         LOGEXCEPT('ERR')  # delete me... just for debugging
         self.edtEnterUSD.setText('')
      
      


   


   
