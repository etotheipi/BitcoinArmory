import unittest
import sys
sys.argv.append('--nologging')
sys.argv.append('--testnet')


from armoryengine.ALL import *

from twisted.internet import reactor

from test import Tiab


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


   def run(self):
      class T:
         def port(self, p):
            if p == 0:
               return 19000
            else:
               return 19010

      #tiab = T()
      tiab = Tiab.TiabSession(tiabdatadir='.\\tiab')
      # sends 10BTC between primary two wallets
      tx = hex_to_binary("0100000001b547cc4ec882fb7bf79d7409310c9f4f439cd8f9d5d1f86fbda987f3f41536d2010000008a473044022069ad6c556d9b8c7a91355e031e191b1eee73747292f04ff756910f98342db5d8022036eb3d42aa8cb430edf2a81d1686ed164bb245fa230e1ca6feb3c7667be4eafe0141040af91327d33ae74b487ce5b42b2f8ec872bd9b11ff0be02a2b8b1884eee3dae58e2fdd8bcd9fcb3d5f50706f2f73261f9c7a6aa8bea241d30f84cd0e8bed2bb3ffffffff0200ca9a3b000000001976a914c03d7ae9d043213ce013d56b464c5e986592768688acd0048ef9390000001976a9143504d74e81775e4d087b76d3a03c46fa7ec84ab288ac00000000");


      success=False

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

      tiab.clean()
      
      return self.success
   


class TiabSendTxTest(unittest.TestCase):

   def setUp(self):
      pass
      
   def tearDown(self):
      pass
   
   def test_sendtx(self):
      self.assertTrue(Test().run())


if not USE_TESTNET:
   LOGERROR("Must be run with --testnet")
   sys.exit(1)
   
if __name__ == "__main__":
   s = Test().run()
   if not s:
      print "Failed"

# kate: indent-width 3; replace-tabs on;
