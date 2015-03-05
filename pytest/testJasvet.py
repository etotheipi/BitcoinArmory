import sys
from unittest.case import SkipTest
sys.path.append('..')
from armoryengine.ALL import *
from jasvet import *
import unittest


class JasvetTester(unittest.TestCase):

   def testRandomK(self):
      r = randomk()
      self.assertTrue(r)

   def testHash160ToBC(self):
      # most of these values are form the private key 1
      h160 = b'751e76e8199196d454941c45d1b3a323f1433bd6'
      addr = b'1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH'
      h160b = binary_to_hex(bc_address_to_hash_160(addr))
      self.assertEqual(h160, h160b)
      addrb = hash_160_to_bc_address(hex_to_binary(h160))
      self.assertEqual(addr, addrb)
      pubkey = b'0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
      addrb = public_key_to_bc_address(hex_to_binary(pubkey))
      self.assertEqual(addr, addrb)

      h160 = b'91b24bf9f5288532960ac687abb035127b1d28a5'
      addr = b'1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm'
      h160b = binary_to_hex(bc_address_to_hash_160(addr))
      self.assertEqual(h160, h160b)
      addrb = hash_160_to_bc_address(hex_to_binary(h160))
      self.assertEqual(addr, addrb)
      pubkey = b'0479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8'
      addrb = public_key_to_bc_address(hex_to_binary(pubkey))
      self.assertEqual(addr, addrb)

   def testB58(self):
      b = hex_to_binary(b'00010203')
      b58 = b'1Ldp'
      b58b = b58encode(b)
      self.assertEqual(b58,b58b)
      bb = b58decode(b58, 4)
      self.assertEqual(b,bb)

   def testI2d(self):
      k = EC_KEY(1)
      r = binary_to_hex(i2d_ECPrivateKey(k))
      expected = b'3082011302010104200000000000000000000000000000000000000000000000000000000000000001a081a53081a2020101302c06072a8648ce3d0101022100fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f300604010004010704410479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141020101a1440342000479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8'
      self.assertEqual(r,expected)

      r = binary_to_hex(i2d_ECPrivateKey(k, True))
      expected = b'3081d302010104200000000000000000000000000000000000000000000000000000000000000001a08185308182020101302c06072a8648ce3d0101022100fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f300604010004010704210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141020101a1240322000279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
      self.assertEqual(r,expected)

   def testDec(self):
      x = b'7483729483792178'
      x2 = binary_to_hex(decbin(0x7483729483792178))
      self.assertEqual(x,x2)

      x = b'ff7821798394728374'
      x2 = binary_to_hex(decvi(0x7483729483792178))
      self.assertEqual(x,x2)
      
   def testFormat(self):
      x = b'18426974636f696e205369676e6564204d6573736167653a0a0568656c6c6f'
      x2 = binary_to_hex(format_msg_to_sign(b'hello'))
      self.assertEqual(x,x2)

   def testSer(self):
      k = EC_KEY(1)
      x = b'0479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8'
      x2 = binary_to_hex(k.pubkey.ser())
      self.assertEqual(x,x2)
      addr = public_key_to_bc_address(k.pubkey.ser())
      addr2 = b'1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm'
      self.assertEqual(addr,addr2)


   def testVerify(self):
      sign = b'HErgpyJcLnUDnGt0Vt0uocomgBVY2f5YwngZ4vfbAGyLwR7sQgnb2b3RpSD7mMAUJN2qn0vD9lu3vlhlq0Vn1Lw='
      msg = b'hello there'
      self.assertTrue(verify_message_Bitcoin(sign, msg))

   def testSign(self):
      r,s = 1,1
      x = b'00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001'
      x2 = binary_to_hex(Signature(r,s).ser())
      self.assertEqual(x,x2)
      secret = b'secretsecretsecretsecretsecretse'
      message = b'hello there'
      data2 = sign_message_Bitcoin(secret, message)
      sign, msg = data2['b64-signature'], data2['message']
      self.assertTrue(verify_message_Bitcoin(sign, msg))

   def testMisc(self):
      pvk1=b'\x01'*32
      text1=b'Hello world!\n'

      sv0=ASv0(pvk1, text1)
      self.assertTrue(verifySignature(sv0['b64-signature'], sv0['message'], signVer='v0'))
      d = ASv1B64(pvk1, text1)
      self.assertEqual(d[:31], b'-----BEGIN BITCOIN MESSAGE-----')
      self.assertEqual(d[-29:], b'-----END BITCOIN MESSAGE-----')



