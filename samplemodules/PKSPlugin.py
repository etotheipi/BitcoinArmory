# This is a sample plugin file that will be used to create a new tab
# in the Armory main window.  All plugin files (such as this one) will
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from PyQt4.Qt import QPushButton, QScrollArea, SIGNAL, QLabel, QLineEdit, \
   QTextEdit
from qtdefines import QRichLabel, makeVertFrame, makeHorizFrame, GETFONT, \
   relaxedSizeNChar, VERTICAL
from qtdialogs import createAddrBookButton
from ui.WalletFrames import SelectWalletFrame
from armoryengine.BDM import getBDM
from twisted.internet import reactor
from armoryengine.ArmoryOptions import getTestnetFlag

class PluginObject(object):
   # PKS is a place holder - As are all labels in this dialog
   tabName = 'PKS'
   maxVersion = '0.99'

   #############################################################################
   def __init__(self, main):
      self.main = main
      self.wlt = None

      ##########################################################################
      ##### Display the conversion values based on the Coinbase API
      headerLabel    = QRichLabel(tr("<b>PKS</b>"""), doWrap=False)
      addressLabel = QLabel('Choose wallet:')
      self.frmSelectedWlt = SelectWalletFrame(main, main, 
                     VERTICAL,
                     selectWltCallback=self.setWallet)
      self.pksButton     = QPushButton('Save PKS')
      self.dnssecButton     = QPushButton('Save PKS && PMTA')
      self.paymentRequestButton     = QPushButton('Payment Request')
      paymentRequestLabel = QLabel('Payment Request:')
      self.paymentRequestTextArea = QTextEdit()
      self.paymentRequestTextArea.setFont(GETFONT('Fixed', 8))
      w,h = relaxedSizeNChar(self.paymentRequestTextArea, 68)[0], int(12 * 8.2)
      self.paymentRequestTextArea.setMinimumWidth(w)
      self.paymentRequestTextArea.setMinimumHeight(h)
      self.paymentRequestTextArea.setReadOnly(True)
      self.clearButton     = QPushButton('Clear')

      # Qt GUI calls must occur on the main thread. We need to update the wallet
      # once the BDM is ready. So, we register a signal with the main thread
      # that can be used to call a function.
      self.main.connect(self.main, SIGNAL('pluginNotify'), self.UpdateWallet)

      def pksAction():
         print "PKS Button Press"
         self.savePKSFile()

      def dnssecButton():
         print "PKS & PMTA Button Press"
         self.savePKSFile()
         self.savePMTAFile()

      def paymentRequestAction():
         self.paymentRequestTextArea.setText("<Payment Request Blob>")

      def clearTextArea():
         self.paymentRequestTextArea.setText('')

      self.main.connect(self.pksButton, SIGNAL('clicked()'), pksAction)
      self.main.connect(self.dnssecButton, SIGNAL('clicked()'), dnssecButton)
      self.main.connect(self.paymentRequestButton, SIGNAL('clicked()'), paymentRequestAction)
      self.main.connect(self.clearButton, SIGNAL('clicked()'), clearTextArea)

      pluginFrame = makeVertFrame([headerLabel,
                                   makeHorizFrame([addressLabel, 'Stretch']),
                                   makeHorizFrame([self.frmSelectedWlt, 'Stretch']),
                                   makeHorizFrame([self.pksButton, self.dnssecButton, self.paymentRequestButton, 'Stretch']),
                                   paymentRequestLabel,
                                   makeHorizFrame([self.paymentRequestTextArea,'Stretch']),
                                   makeHorizFrame([self.clearButton, 'Stretch']),
                                   'Stretch'])

      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(pluginFrame)

      # Register a BDM callback that can be called when the BDM is ready.
      TheBDM.registerCppNotification(self.handleNotification)


   def savePKSFile(self):
         defName = 'armory_%s.pks' % self.wlt.uniqueIDB58
         filePath = unicode(self.main.getFileSave(defaultFilename = defName))

         if not len(filePath)>0:
            print 'NOTHING SAVED!'
            return
         else:
            sbdPublicKey33 = SecureBinaryData(self.wlt.sbdPublicKey33)
            sbdPublicKey65 = CryptoECDSA().UncompressPoint(sbdPublicKey33);

            pathdir = os.path.dirname(filePath)
            pathfn  = os.path.basename(filePath)

            if not os.path.exists(pathdir):
               raise FileExistsError('Path for new wlt does not exist: %s', pathdir)

            if os.path.exists(filePath):
               raise FileExistsError('File already exists, will not overwrite')

            myPKS = PublicKeySource()
            myPKS.initialize(False, False, False, False, False, sbdPublicKey65.toBinStr(), False)
            with open(filePath, 'wb') as newWltFile:
               newWltFile.write(myPKS.serialize())
            return myPKS


   def savePMTAFile(self):
         defName = 'armory_%s.pmta' % self.wlt.uniqueIDB58
         payNet = PAYNET_BTC
         if getTestnetFlag():
            payNet = PAYNET_TBTC

         filePath = unicode(self.main.getFileSave(defaultFilename = defName))
         if not len(filePath)>0:
            print 'NOTHING SAVED!'
            return
         else:
            sbdPublicKey33 = SecureBinaryData(self.wlt.sbdPublicKey33)
            sbdPublicKey65 = CryptoECDSA().UncompressPoint(sbdPublicKey33);

            pathdir = os.path.dirname(filePath)
            pathfn  = os.path.basename(filePath)

            if not os.path.exists(pathdir):
               raise FileExistsError('Path for new wlt does not exist: %s', pathdir)

            if os.path.exists(filePath):
               raise FileExistsError('File already exists, will not overwrite')

            with open(filePath, 'wb') as newWltFile:
               myPKS = PublicKeySource()
               myPKS.initialize(False, False, False, False, False, sbdPublicKey65.toBinStr(), True)
               myPMTA = PMTARecord()
               myPMTA.initialize(myPKS.serialize(), payNet)
               newWltFile.write(myPMTA.serialize())


   def setWallet(self, wlt, isDoubleClick=False):
      self.wlt = wlt


   # Updates the wallet balance on startup.
   def UpdateWallet(self):
      self.frmSelectedWlt.updateOnWalletChange()


   # Place any code here that must be executed once the BDM is ready. For now,
   # the only thing we do is emit a signal so that the GUI can be updated by the
   # main thread (Qt GUI requirement), which updates the wallet balance.
   def handleNotification(self, action, args):
      if action == FINISH_LOAD_BLOCKCHAIN_ACTION:
         self.main.emit(SIGNAL('pluginNotify'))


   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay
