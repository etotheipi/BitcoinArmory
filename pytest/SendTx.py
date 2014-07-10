import sys
from twisted.trial._synctest import SkipTest
sys.path.append('..')
from pytest.Tiab import TiabTest

from armoryengine.ALL import *

from twisted.internet import reactor

TIAB_DIR = '.\\tiab'
TEST_TIAB_DIR = '.\\test\\tiab'
NEED_TIAB_MSG = "This Test must be run with J:/Development_Stuff/bitcoin-testnet-boxV2.7z (Armory jungle disk). Copy to the test directory."

class Test:
   def __init__(self):
      self.success=False
      
   def txReturned(self, tx):
      # a round trip was completed
      # print "got something back"
      #if protoObj.serialize() == tx:
      self.factory1.stopTrying()
      self.factory2.stopTrying()
      reactor.stop()
      self.success=True
      
   def timeout(self):
      self.factory1.stopTrying()
      self.factory2.stopTrying()
      reactor.stop()
      self.success=False


   def run(self, tiab):
      class T:
         def port(self, p):
            if p == 0:
               return 19000
            else:
               return 19010
      # sends 10BTC between primary two wallets
      tx = hex_to_binary("0100000001721507bc7c4cdbd7cf798d362272b2e5941e619f2f300f46ac956933cb421811000000008b4830450220045e83813973971742e87a00a1dae5de02475ec4d9111373d77cac8b22b30dd802210095ced701b5ebfe41bf32a551e94fcd254189b6386f7ebaae06c22cd61aa93b2801410462326939525c697781dc280cd80a5d93f1a92ed480e30adfbeebe1b1bc1e161b3f06a222dcca62ba045c7536d3a31de2554842a58a2706b996bbdfe3bcc46a8fffffffff02404eaca0150000001976a914bec7782c7a686b60300f7831032d2740288b3fb888ac00ca9a3b000000001976a914d2f1cb6d6cee483b9c18c6ebfe371d37ad381b0488ac00000000");

      self.success=False

      def sendTx(protoObj):
         # print "sent"
         pytx = PyTx()
         pytx.unserialize(tx)
         protoObj.sendMessage(PayloadTx(pytx))
         
      self.factory1 = ArmoryClientFactory(None, sendTx)
      reactor.callWhenRunning( \
         reactor.connectTCP, '127.0.0.1', \
         tiab.port(0), self.factory1)

      self.factory2 = ArmoryClientFactory( None, func_inv=self.txReturned)
      reactor.callWhenRunning( \
         reactor.connectTCP, '127.0.0.1', \
         tiab.port(0), self.factory2)


      reactor.callLater(15, self.timeout)
      reactor.run()
      
      return self.success
   

# Disabling this test because it's not actually testing Armory.
@SkipTest
class TiabSendTxTest(TiabTest):
  
   def test_sendtx(self):
      self.assertTrue(Test().run(self.tiab))

   
