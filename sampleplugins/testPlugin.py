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
   
   def __init__(self):

      self.lastPriceFetch = 0
      self.lblHeader    = QRichLabel(tr("""
               Tracking buy and sell prices on Coinbase every 30 seconds"""))
      self.lblLastTime  = QRichLabel('')
      self.lblSellLabel = QRichLabel(tr('Coinbase <b>Sell</b> Price (USD):'))
      self.lblBuyLabel  = QRichLabel(tr('Coinbase <b>Buy</b> Price (USD):'))
      self.lblSellPrice = QRichLabel('<Not Available>')
      self.lblBuyPrice  = QRichLabel('<Not Available>')


      pLayout = QGridLayout()
      pLayout.addWidget(self.lblHeader,      0,0,  1,2)
      pLayout.addWidget(self.lblSellLabel,   1,0)
      pLayout.addWidget(self.lblSellPrice,   1,1)
      pLayout.addWidget(self.lblBuyLabel,    2,0)
      pLayout.addWidget(self.lblBuyPrice,    2,1)
      pLayout.addWidget(self.lblLastTime,    3,0,  1,2)


      # Put the layout into a generic widget
      tabWidget = QWidget()
      tabWidget.setLayout(pLayout)

      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(tabWidget)



   def getTabToDisplay(self):
      return self.tabToDisplay


   def integerTruncateWithCommas(self, pstr):
      pstr = pstr.split('.')[0] 
      pstr = ','.join([pstr[::-1][3*i:3*(i+1)][::-1] for i in range((len(pstr)-1)/3+1)][::-1])
      return pstr


   def fetchFormattedPrice(self, url):
      sock = urllib2.urlopen(url)
      value = ast.literal_eval(sock.read())['subtotal']['amount']
      return self.integerTruncateWithCommas(value)

   def injectHeartbeatAlwaysFunc(self):
      # Check the price every 30 seconds, update widgets
      if RightNow() < self.lastPriceFetch+30:
         return

      self.lastPriceFetch = RightNow()

      urlBase = 'http://coinbase.com/api/v1/prices/'
      urlSell = urlBase + 'sell'
      urlBuy  = urlBase + 'buy'

      try:
         sellstr = self.fetchFormattedPrice(urlSell)
         buystr  = self.fetchFormattedPrice(urlBuy)
         print sellstr,buystr
         
         self.lblSellPrice.setText('<b><font color="%s">$%s</font> / BTC</b>' % \
                                                (htmlColor('TextBlue'), sellstr))
         self.lblBuyPrice.setText( '<b><font color="%s">$%s</font> / BTC</b>' % \
                                                (htmlColor('TextBlue'), buystr))
      
         timestr = unixTimeToFormatStr(RightNow())
         self.lblLastTime.setText('Last successful price check: %s' % timestr)
      except:
         LOGEXCEPT('Failed to fetch price data from %s' % urlBase)

   

      


   


   
