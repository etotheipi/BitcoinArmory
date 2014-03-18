import unittest

from armoryengine.ALL import *

from armoryengine.Networking import ArmoryClientFactory
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
      tiab = Tiab.TiabSession()
      # sends 10BTC from Charles's TIAB wallet to mwxN3Xw7P7kfkKY41KC99eD6cHtFYV9fun (also in that wallet)
      tx = hex_to_binary("0100000001cce316f49284cb1e7d0c582064df8bb5dad960a3feeeca938cbb9fec7ba75694010000008b483045022100ad0dd567452c9d6d4b668e7847c360d1e866932a49f687927acfce86bf583d470220212028998cec632e41ea8d1bdd330da4e7c9b33f109bef9d9f8ae3fa85448aa80141043636a37759b535cc29ae611d770efdd7dc18830e0fc3a7a67851c5fe41737ae1a8ec90219aaea2684ec443344c16d385090359832d5eb71a6f07fb07bc06dcfdffffffff02f0c6c99d450000001976a9145d07242295d11e2fddb4535e7b0a5cdbea32db6888ac00ca9a3b000000001976a914b4503c9ef81c2d09f13a51ebd1d92e2368912b2d88ac00000000");

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
