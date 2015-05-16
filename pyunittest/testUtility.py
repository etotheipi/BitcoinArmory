import sys
sys.path.append('..')
from armoryengine.ALL import *
from jasvet import *
import unittest


class UtilsTester(unittest.TestCase):

   def testConversion(self):
      b = b'\x01\x02\x03'
      br = b'\x03\x02\x01'
      h = b'010203'
      hr = b'030201'
      i = 66051
      ir = 197121
      
      # test big-endian
      h2 = binary_to_hex(b, BIGENDIAN, BIGENDIAN)
      self.assertEqual(h,h2)

      i2 = binary_to_int(b, BIGENDIAN)
      self.assertEqual(i,i2)

      b2 = hex_to_binary(h, BIGENDIAN, BIGENDIAN)
      self.assertEqual(b,b2)

      i3 = hex_to_int(h, BIGENDIAN)
      self.assertEqual(i,i3)

      b3 = int_to_binary(i, 0, BIGENDIAN)
      self.assertEqual(b,b3)

      h3 = int_to_hex(i, 0, BIGENDIAN)
      self.assertEqual(h,h3)
   
      # test padded
      b4 = int_to_binary(i, 10, BIGENDIAN)
      self.assertEqual(b'\x00'*7 + b,b4)

      h4 = int_to_hex(i, 10, BIGENDIAN)
      self.assertEqual(b'00'*7 + h,h4)

      # test big-endian
      h2 = binary_to_hex(b, BIGENDIAN, LITTLEENDIAN)
      self.assertEqual(hr,h2)

      i2 = binary_to_int(b, LITTLEENDIAN)
      self.assertEqual(ir,i2)

      b2 = hex_to_binary(h, BIGENDIAN, LITTLEENDIAN)
      self.assertEqual(br,b2)

      i3 = hex_to_int(h, LITTLEENDIAN)
      self.assertEqual(ir,i3)

      b3 = int_to_binary(i, 0, LITTLEENDIAN)
      self.assertEqual(br,b3)

      h3 = int_to_hex(i, 0, LITTLEENDIAN)
      self.assertEqual(hr,h3)
   
      # test padded
      b4 = int_to_binary(i, 10, LITTLEENDIAN)
      self.assertEqual(br + b'\x00'*7,b4)

      h4 = int_to_hex(i, 10, LITTLEENDIAN)
      self.assertEqual(hr + b'00'*7,h4)

   def testSigningKey(self):
      a160 = hash160(hex_to_binary(ARMORY_INFO_SIGN_PUBLICKEY))
      addr = hash160_to_addrStr(a160, b'\x00')
      
      self.assertEqual(addr, ARMORY_INFO_SIGN_ADDR)

