
import sys
sys.path.append('..')
import unittest

from armoryengine.ArmoryUtils import hex_to_binary
from armoryengine.ConstructedScript import PaymentRequest
from dnssec_dane.daneHandler import validatePaymentRequest
from pytest.testConstructedScript import PR1_v0, PR2_v0

################################################################################
class confirmPRValidity(unittest.TestCase):
   # Use serialize/unserialize to generate a payment request, then confirm that
   # we can validate any scripts.
   def testSerialization(self):
      # PKS1 with a checksum & uncompressed key.
      pr1 = PaymentRequest().unserialize(PR1_v0)
      valResult = validatePaymentRequest(pr1)
      self.assertEqual(valResult, 1)


if __name__ == "__main__":
   unittest.main()
