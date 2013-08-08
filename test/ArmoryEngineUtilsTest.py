'''
Created on Jul 29, 2013

@author: Andy
'''
from random import shuffle
from utilities.ArmoryUtils import isASCII, toBytes, toUnicode, toPreferred, \
   lenBytes, BIGENDIAN, hex_to_binary, LITTLEENDIAN, hash256, NegativeValueError, \
   TooMuchPrecisionError, hex_switchEndian, str2coin
from utilities.BinaryPacker import BinaryPacker, UINT8, UINT16, UINT32, UINT64, \
   INT8, INT16, INT32, INT64, VAR_INT, VAR_STR, FLOAT, BINARY_CHUNK, PackerError
from utilities.BinaryUnpacker import BinaryUnpacker, UnpackerError
import hashlib
import locale
import time
import unittest
import utilities.ArmoryUtils

UNICODE_STRING = u'unicode string'  
NON_ASCII_STRING = '\xff\x00 Non-ASCII string \xff\x00'
ASCII_STRING = 'ascii string'
LONG_TEST_NUMBER = 98753178900
RightNow = time.time

class ArmoryEngineTest(unittest.TestCase):

   def testIsASCII(self):
      self.assertTrue(isASCII(ASCII_STRING))
      self.assertFalse(isASCII(NON_ASCII_STRING))

   def testToBytes(self):
      self.assertEqual(toBytes(UNICODE_STRING), UNICODE_STRING.encode('utf-8'))
      self.assertEqual(toBytes(ASCII_STRING), ASCII_STRING)
      self.assertEqual(toBytes(NON_ASCII_STRING), NON_ASCII_STRING)
      self.assertEqual(toBytes(5), None)
      
   def testToUnicode(self):
      self.assertEqual(toUnicode(ASCII_STRING), unicode(ASCII_STRING, 'utf-8'))
      self.assertEqual(toUnicode(UNICODE_STRING), UNICODE_STRING)
      self.assertEqual(toUnicode(5),None)
      
   def testToPreferred(self):
      self.assertEqual(toPreferred(ASCII_STRING), toUnicode(ASCII_STRING).encode(locale.getpreferredencoding()))

   def testLenBytes(self):
      self.assertEqual(lenBytes(ASCII_STRING), len(ASCII_STRING))
   
   def testBasicUtils(self):
      addr = '1Ncui8YjT7JJD91tkf42dijPnqywbupf7w'  # Sam Rushing's BTC address
      i    =  4093
      hstr = 'fd0f'
      bstr = '\xfd\x0f'
      
      self.callTestFunction('int_to_hex',    hstr, i   )
      self.callTestFunction('int_to_hex',    hstr, long(i))
      self.callTestFunction('int_to_hex',    hstr + "00", i, 3)
      self.callTestFunction('hex_to_int',    i,    hstr)
      self.callTestFunction('int_to_binary', bstr, i   )
      self.callTestFunction('binary_to_int', i,    bstr)
      self.callTestFunction('hex_to_binary', bstr, hstr)
      self.callTestFunction('binary_to_hex', hstr, bstr)
      self.callTestFunction('hex_switchEndian', '67452301', '01234567')
      
      hstr = '0ffd'
      bstr = '\x0f\xfd'
      
      self.callTestFunction('int_to_hex',    hstr, i   , 2, BIGENDIAN)
      self.callTestFunction('hex_to_int',    i,    hstr, BIGENDIAN)
      self.callTestFunction('int_to_binary', bstr, i   , 2, BIGENDIAN)
      self.callTestFunction('binary_to_int', i,    bstr, BIGENDIAN)
   
      #h   = '00000123456789abcdef000000'
      #ans = 'aaaaabcdeghjknrsuwxyaaaaaa'
      #self.callTestFunction('binary_to_typingBase16', ans, h  )
      #self.callTestFunction('typingBase16_to_binary', h,   ans)
      
      blockhead = '010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d0000000000009762547903d36881a86751f3f5049e23050113f779735ef82734ebf0b4450081d8c8c84db3936a1a334b035b'
      blockhash   = '1195e67a7a6d0674bbd28ae096d602e1f038c8254b49dfe79d47000000000000'
      blockhashBE = '000000000000479de7df494b25c838f0e102d696e08ad2bb74066d7a7ae69511'
      blockhashBEDifficulty = 3.6349e-48
      allF        = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
      
      self.callTestFunction('ubtc_to_floatStr', '12.05600000', 1205600000)
      self.callTestFunction('floatStr_to_ubtc', 1205600000, '12.056')
      self.callTestFunction('float_to_btc', 1205600000, 12.056)
      
      self.callTestFunction('packVarInt', ['A',1], 65)
      self.callTestFunction('packVarInt', ['\xfd\xff\x00', 3], 255)
      self.callTestFunction('packVarInt', ['\xfe\x00\x00\x01\x00', 5], 65536)
      self.callTestFunction('packVarInt', ['\xff\x00\x10\xa5\xd4\xe8\x00\x00\x00', 9], 10**12)
      
      self.callTestFunction('unpackVarInt', [65,1], 'A')
      self.callTestFunction('unpackVarInt', [255, 3], '\xfd\xff\x00')
      self.callTestFunction('unpackVarInt', [65536, 5], '\xfe\x00\x00\x01\x00')
      self.callTestFunction('unpackVarInt', [10**12, 9], '\xff\x00\x10\xa5\xd4\xe8\x00\x00\x00')
   
   
      data   = hex_to_binary('11' + 'aa'*31)
      dataBE = hex_to_binary('11' + 'aa'*31, endIn=LITTLEENDIAN, endOut=BIGENDIAN)
      dataE1 = hex_to_binary('11' + 'aa'*30 + 'ab')
      dataE2 = hex_to_binary('11' + 'aa'*29 + 'abab')
      dchk = hash256(data)[:4]
      self.callTestFunction('verifyChecksum', data, data, dchk)
      self.callTestFunction('verifyChecksum', data, dataBE, dchk, beQuiet=True)
      self.callTestFunction('verifyChecksum', '',   dataE1, dchk, hash256, False, True)  # don't fix
      self.callTestFunction('verifyChecksum', data, dataE1, dchk, hash256,  True, True)  # try fix
      self.callTestFunction('verifyChecksum', '',   dataE2, dchk, hash256, False, True)  # don't fix
      self.callTestFunction('verifyChecksum', '',   dataE2, dchk, hash256,  True, True)  # try fix
   
   
      verTuple = (0,50,0,0)
      verInt   = 5000000
      verStr   = '0.50'
      self.callTestFunction('getVersionString',   verStr, verTuple)
      self.callTestFunction('getVersionInt',      verInt, verTuple)
      self.callTestFunction('readVersionString',  verTuple, verStr)
      self.callTestFunction('readVersionInt',     verTuple, verInt)
   
      verTuple = (1,0,12,0)
      verInt   =  10012000
      verStr   = '1.00.12'
      self.callTestFunction('getVersionString',   verStr, verTuple)
      self.callTestFunction('getVersionInt',      verInt, verTuple)
      self.callTestFunction('readVersionString',  verTuple, verStr)
      self.callTestFunction('readVersionInt',     verTuple, verInt)
   
      verTuple = (0,20,0,108)
      verInt   =  2000108
      verStr   = '0.20.0.108'
      self.callTestFunction('getVersionString',   verStr, verTuple)
      self.callTestFunction('getVersionInt',      verInt, verTuple)
      self.callTestFunction('readVersionString',  verTuple, verStr)
      self.callTestFunction('readVersionInt',     verTuple, verInt)
   
      miniKey  = 'S4b3N3oGqDqR5jNuxEvDwf'
      miniPriv = hex_to_binary('0c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe471be89827e19d72aa1d')
      self.callTestFunction('decodeMiniPrivateKey', miniPriv, miniKey)
      
      self.callTestFunction('coin2str','            0.0000', 0, 4)

      self.callTestFunction('coin2str','          987.5318', LONG_TEST_NUMBER, 4)
      self.callTestFunction('coin2str','987.53178900', LONG_TEST_NUMBER, 8, False)
      self.callTestFunction('coin2str','987.5317890000', LONG_TEST_NUMBER, 12, False, 10)
      self.callTestFunction('coin2strNZ','      987.531789  ', LONG_TEST_NUMBER)
      self.callTestFunction('coin2strNZS','987.531789', LONG_TEST_NUMBER)
      self.callTestFunction('coin2str_approx','      988       ', LONG_TEST_NUMBER)
      self.callTestFunction('coin2str_approx','     -988       ', LONG_TEST_NUMBER * -1)
      self.callTestFunction('str2coin', LONG_TEST_NUMBER, '987.53178900')
      self.assertRaises(ValueError, str2coin, '    ')
      self.assertRaises(NegativeValueError, str2coin, '-1', False)
      self.callTestFunction('str2coin', -100000000, '-1', True)
      self.assertRaises(NegativeValueError, str2coin, '-1.1', False)
      self.assertRaises(TooMuchPrecisionError, str2coin, '.1111', True, 2, False)
      self.callTestFunction('str2coin', 11110000, '.1111', True, 8, True)
      self.callTestFunction('sha1', hashlib.new('sha1', bstr).digest(), bstr)
      self.callTestFunction('sha512', hashlib.new('sha512', bstr).digest(), bstr)
      self.callTestFunction('ripemd160', hex_to_binary('13988143ae67128f883765a4a4b19d77c1ea1ee9'), bstr)
      self.callTestFunction('hash160', hex_to_binary('d418dd224e11e1d3b37b5f46b072ccf4e4e26203'), bstr)
      self.callTestFunction('binaryBits_to_difficulty', blockhashBEDifficulty, blockhashBE)
            
   def callTestFunction(self, fnName, expectedOutput, *args, **kwargs):
      """
      Provide a function name, inputs and some known outputs
      Prints a pass/fail string if the outputs match
      """
      fn = getattr(utilities.ArmoryUtils, fnName)
      actualOutput = fn(*args,**kwargs)
      self.assertAlmostEqual(expectedOutput, actualOutput, 4, \
         '\n\t' + '___Inputs___:' + str(args) + '\n\t' + '___ExpOut___:' + \
         str(expectedOutput) + '\n\t' + '___ActOut___:' + str(actualOutput))
   
class BinaryPackerUnpackerTest(unittest.TestCase):  
   
   def testBinaryUnpacker(self):
      ts = '\xff\xff\xff'
      bu = BinaryUnpacker(ts)
      self.assertEqual(bu.getSize(), len(ts))
      bu.advance(1)
      self.assertEqual(bu.getRemainingSize(), len(ts)-1)
      self.assertEqual(bu.getBinaryString(), ts)
      self.assertEqual(bu.getRemainingString(), ts[1:])
      bu.rewind(1)
      self.assertEqual(bu.getRemainingSize(), len(ts))
      bu.resetPosition(2)
      self.assertEqual(bu.getRemainingSize(), len(ts) - 2)
      self.assertEqual(bu.getPosition(), 2)
      bu.resetPosition()
      self.assertEqual(bu.getRemainingSize(), len(ts))
      self.assertEqual(bu.getPosition(), 0)
      bu.append(ts)
      self.assertEqual(bu.getBinaryString(), ts + ts)
   
   def testBinaryPacker(self):
      UNKNOWN_TYPE = 100
      TEST_FLOAT = 1.23456789
      TEST_UINT = 0xff
      TEST_INT = -1
      TEST_VARINT = 78
      TEST_STR = 'abc'
      TEST_BINARY_PACKER_STR = hex_to_binary('ffff00ff000000ff00000000000000ffffffffffffffffffffffffffffff4e0361626352069e3fffffffffffff00')
      FS_FOR_3_BYTES = '\xff\xff\xff'
      bp = BinaryPacker()
      bp.put(UINT8, TEST_UINT)
      bp.put(UINT16, TEST_UINT)
      bp.put(UINT32, TEST_UINT)
      bp.put(UINT64, TEST_UINT)
      bp.put(INT8, TEST_INT)
      bp.put(INT16, TEST_INT)
      bp.put(INT32, TEST_INT)
      bp.put(INT64, TEST_INT)
      bp.put(VAR_INT, TEST_VARINT)
      bp.put(VAR_STR, TEST_STR)
      bp.put(FLOAT, TEST_FLOAT)
      bp.put(BINARY_CHUNK, FS_FOR_3_BYTES)
      bp.put(BINARY_CHUNK, FS_FOR_3_BYTES, 4)
      self.assertRaises(PackerError, bp.put, UNKNOWN_TYPE, TEST_INT)
      self.assertRaises(PackerError, bp.put, BINARY_CHUNK, FS_FOR_3_BYTES, 2)
      self.assertEqual(bp.getSize(), len(TEST_BINARY_PACKER_STR))
      ts = bp.getBinaryString()
      self.assertEqual(ts, TEST_BINARY_PACKER_STR)
      bu = BinaryUnpacker(ts)
      self.assertEqual(bu.get(UINT8), TEST_UINT)
      self.assertEqual(bu.get(UINT16), TEST_UINT)
      self.assertEqual(bu.get(UINT32), TEST_UINT)
      self.assertEqual(bu.get(UINT64), TEST_UINT)
      self.assertEqual(bu.get(INT8), TEST_INT)
      self.assertEqual(bu.get(INT16), TEST_INT)
      self.assertEqual(bu.get(INT32), TEST_INT)
      self.assertEqual(bu.get(INT64), TEST_INT)
      self.assertEqual(bu.get(VAR_INT), TEST_VARINT)
      self.assertEqual(bu.get(VAR_STR), TEST_STR)
      self.assertAlmostEqual(bu.get(FLOAT), TEST_FLOAT, 2)
      self.assertEqual(bu.get(BINARY_CHUNK, 3), FS_FOR_3_BYTES)
      self.assertEqual(bu.get(BINARY_CHUNK, 4), FS_FOR_3_BYTES+"\x00")
      self.assertRaises(UnpackerError, bu.get, BINARY_CHUNK, 1)
      self.assertRaises(UnpackerError, bu.get, UNKNOWN_TYPE)
      self.assertRaises(UnpackerError, bu.get, BINARY_CHUNK, 1)

if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testArmoryEngine']
   unittest.main()