import sys
sys.path.append('..')
import unittest
import random

from armoryengine.ALL import *


class SigningTester(unittest.TestCase):

   def testLowSig(self):
      sbdPrivKey = SecureBinaryData(b'\x01'*32)
      pub = CryptoECDSA().ComputePublicKey(sbdPrivKey).toBinStr()

      for i in range(100):
         msg = "some random msg %s" % random.random()
         sbdSig = CryptoECDSA().SignData(SecureBinaryData(msg), sbdPrivKey, False)
         binSig = sbdSig.toBinStr()
         derSig = createDERSigFromRS(binSig[:32], binSig[32:])
         r, s = getRSFromDERSig(derSig)
         j = binary_to_int(s, BIGENDIAN)
         self.assertTrue( j <= SECP256K1_ORDER / 2)

