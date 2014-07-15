'''
Created on Jul 29, 2013

@author: Andy
'''
import sys
sys.path.append('..')
import hashlib
import locale
from random import shuffle
import time
import unittest


from armoryengine.ArmoryUtils import *
from armoryengine.BinaryPacker import *
from armoryengine.BinaryUnpacker import *
import armoryengine.ArmoryUtils
from armoryengine import ArmoryUtils


#sys.argv.append('--nologging')

UNICODE_STRING = u'unicode string'
NON_ASCII_STRING = '\xff\x00 Non-ASCII string \xff\x00'
ASCII_STRING = 'ascii string'
LONG_TEST_NUMBER = 98753178900


################################################################################
################################################################################
class ArmoryEngineTest(unittest.TestCase):


   #############################################################################
   def testIsASCII(self):
      self.assertTrue(isASCII(ASCII_STRING))
      self.assertFalse(isASCII(NON_ASCII_STRING))

   #############################################################################
   def testToBytes(self):
      self.assertEqual(toBytes(UNICODE_STRING), UNICODE_STRING.encode('utf-8'))
      self.assertEqual(toBytes(ASCII_STRING), ASCII_STRING)
      self.assertEqual(toBytes(NON_ASCII_STRING), NON_ASCII_STRING)
      self.assertEqual(toBytes(5), None)

   #############################################################################
   def testToUnicode(self):
      self.assertEqual(toUnicode(ASCII_STRING), unicode(ASCII_STRING, 'utf-8'))
      self.assertEqual(toUnicode(UNICODE_STRING), UNICODE_STRING)
      self.assertEqual(toUnicode(5),unicode(5))

   #############################################################################
   def testToPreferred(self):
      self.assertEqual(toPreferred(ASCII_STRING), toUnicode(ASCII_STRING).encode(locale.getpreferredencoding()))

   #############################################################################
   def testLenBytes(self):
      self.assertEqual(lenBytes(ASCII_STRING), len(ASCII_STRING))

   #############################################################################
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

   #############################################################################
   def callTestFunction(self, fnName, expectedOutput, *args, **kwargs):
      """
      Provide a function name, inputs and some known outputs
      Prints a pass/fail string if the outputs match
      """
      fn = getattr(ArmoryUtils, fnName)
      actualOutput = fn(*args,**kwargs)
      self.assertAlmostEqual(expectedOutput, actualOutput, 4, \
         '\n\t' + '___Inputs___:' + str(args) + '\n\t' + '___ExpOut___:' + \
         str(expectedOutput) + '\n\t' + '___ActOut___:' + str(actualOutput))


   #############################################################################
   def testPluralsBasic(self):
      ##### Test the basic replacePlurals function
      strIn     = 'Hello my @{kitty|2 kitties}@.  I love you@{| guys}@!'
      strOut    = ['','','']
      strOut[1] = 'Hello my kitty.  I love you!'
      strOut[2] = 'Hello my 2 kitties.  I love you guys!'

      # Test singular
      for i in range(1,3):
         replOut = replacePlurals(strIn, i)
         self.assertEqual(replOut, strOut[i])

         replOut = replacePlurals(strIn, i, i)
         self.assertEqual(replOut, strOut[i])


      noStr = 'No replacements'
      self.assertEqual( replacePlurals(noStr), noStr)


      # Not enough arguments
      self.assertRaises(IndexError, replacePlurals, strIn)
      self.assertRaises(IndexError, replacePlurals, strIn + ' @{A cat|many cats}@', 1,1)

      # Too many arguments
      self.assertRaises(TypeError, replacePlurals, strIn, 1,1,1)

      # No format specifiers
      self.assertRaises(TypeError, replacePlurals, noStr, 1)



   #############################################################################
   def testFormatWithPlurals(self):
      ##### Test the formatWithPlurals function
      strIn     = 'Hello my @{kitty|%d kitties}@.  I love you@{| guys}@!'
      strOut    = ['','','','','']
      strOut[1] = 'Hello my kitty.  I love you!'
      strOut[2] = 'Hello my 2 kitties.  I love you guys!'
      strOut[3] = 'Hello my kitty.  I love you guys!'
      strOut[4] = 'Hello my 2 kitties.  I love you!'

      ## Test singular
      for i in range(1,3):
         replOut = formatWithPlurals(strIn, i, i)
         self.assertEqual(replOut, strOut[i])

         replOut = formatWithPlurals(strIn, [i], [i])
         self.assertEqual(replOut, strOut[i])

         replOut = formatWithPlurals(strIn, [i], [i, i])
         self.assertEqual(replOut, strOut[i])

         replOut = formatWithPlurals(strIn, i, [i])
         self.assertEqual(replOut, strOut[i])

         replOut = formatWithPlurals(strIn, i, [i, i])
         self.assertEqual(replOut, strOut[i])


      replOut = formatWithPlurals(strIn, 2, [1,2])
      self.assertEqual(replOut, strOut[3])

      replOut = formatWithPlurals(strIn, 2, [2,1])
      self.assertEqual(replOut, strOut[4])
   



   #############################################################################
   def testPyBackgroundThread(self):

      # This will be used for testing
      def doLongOperation(throwError=False):
         j = '\xab'*32
         n = 20000
         for i in xrange(n):
            j = hash160(j)
            if i==n/2 and throwError:
               raise ValueError('This is a forced error')
         return j

      # On completion, the following should be the output
      ans = '\\\xea\xef\xc6:\xd4\xd7\xed\xee_YM\xf1\xa1aV\x81\x03Y\xc1'

      # Test proper thread execution
      thr = PyBackgroundThread(doLongOperation, False)
      thr.start()
      while not thr.isFinished():
         thr.join(0.1)

      self.assertTrue(thr.isFinished())
      self.assertEqual(thr.getOutput(), ans)
      self.assertFalse(thr.didThrowError())
      self.assertEqual(thr.getErrorType(), None)
      self.assertEqual(thr.getErrorMsg(), '')


      # Test error thrown
      thr = PyBackgroundThread(doLongOperation, True)
      thr.start()
      while not thr.isFinished():
         thr.join(0.1)

      self.assertTrue(thr.isFinished())
      self.assertEqual(thr.getOutput(), None)
      self.assertTrue(thr.didThrowError())
      self.assertEqual(thr.getErrorType(), ValueError)
      self.assertEqual(thr.getErrorMsg(), 'This is a forced error')
      self.assertRaises(ValueError, thr.raiseLastError)

   #############################################################################
   def test_read_address(self):
      hashVal = hex_to_binary('c3a9eb6753c449c88ac193e9ddf7ab3a0be8c5ad')
      addrStr00  = hash160_to_addrStr(hashVal)
      addrStr05  = hash160_to_p2shAddrStr(hashVal)
      addrStrA3  = '28tvtpKmqbKUVaGHshsVKWTaRHJ5yG36xvv'
      addrStrBad = '1JqaKdBsruwgGcZkiVCNU2DBh56DHBsEb1'

      prefix, a160 = addrStr_to_hash160(addrStr00)
      self.assertEqual(prefix, ADDRBYTE)
      self.assertEqual(a160, hashVal)
      self.assertFalse(addrStr_is_p2sh(addrStr00))

      prefix, a160 = addrStr_to_hash160(addrStr05)
      self.assertEqual(prefix, P2SHBYTE)
      self.assertEqual(a160, hashVal)
      self.assertTrue(addrStr_is_p2sh(addrStr05))

      self.assertRaises(BadAddressError, addrStr_to_hash160, addrStrA3)
      self.assertRaises(ChecksumError, addrStr_to_hash160, addrStrBad)
      self.assertRaises(P2SHNotSupportedError, addrStr_to_hash160, addrStr05, False)


   #############################################################################
   def test_p2pkhash_script(self):
      pkh = '\xab'*20
      computed = hash160_to_p2pkhash_script(pkh)
      expected = '\x76\xa9\x14' + pkh + '\x88\xac'
      self.assertEqual(computed, expected)

      # Make sure it raises an error on non-20-byte inputs
      self.assertRaises(InvalidHashError, hash160_to_p2pkhash_script, '\xab'*21)


   #############################################################################
   def test_p2sh_script(self):
      scriptHash = '\xab'*20
      computed = hash160_to_p2sh_script(scriptHash)
      expected = '\xa9\x14' + scriptHash + '\x87'
      self.assertEqual(computed, expected)
   
      # Make sure it raises an error on non-20-byte inputs
      self.assertRaises(InvalidHashError, hash160_to_p2sh_script, '\xab'*21)


   #############################################################################
   def test_p2pk_script(self):
      pubkey   = ['\x3a'*33, \
                  '\x3a'*65]

      expected = ['\x21' + '\x3a'*33 + '\xac', \
                  '\x41' + '\x3a'*65 + '\xac']

      for i in range(2):
         pk = pubkey[i]
         exp = expected[i]
         self.assertEqual( pubkey_to_p2pk_script(pk), exp)


      # Make sure it raises an error on non-[33,65]-byte inputs
      self.assertRaises(KeyDataError, pubkey_to_p2pk_script, '\xab'*21)


   #############################################################################
   def test_script_to_p2sh(self):
      script = '\xab'*10
      scriptHash = hex_to_binary('fc7eb079a69ac4a98e49ea373c91f62b8b9cebe2')
      expected = '\xa9\x14' + scriptHash + '\x87'
      self.assertEqual( script_to_p2sh_script(script), expected)

   #############################################################################
   def test_pklist_to_multisig(self):
      pk1 = 'x01'*33
      pk2 = 'xfa'*33
      pk3 = 'x33'*33
      pk4 = 'x01'*65
      pk5 = 'xfa'*65
      pk6 = 'x33'*65
      pkNot = 'x33'*100
      pkList1 = [pk1, pk2, pk3]
      pkList2 = [pk4, pk5, pk6]
      pkList3 = [pk1, pk5, pk3]
      pkList4 = [pk1, pkNot, pk3] # error

      #self.assertTrue(False) # STUB
     

   #############################################################################
   def testCppScrAddr(self):

      ##### Pay to hash(pubkey)
      script  = hex_to_binary("76a914a134408afa258a50ed7a1d9817f26b63cc9002cc88ac")
      a160    = hex_to_binary(      "a134408afa258a50ed7a1d9817f26b63cc9002cc")
      scraddr = hex_to_binary(    "00a134408afa258a50ed7a1d9817f26b63cc9002cc")

      self.assertEqual(script,  scrAddr_to_script(scraddr))
      self.assertEqual(scraddr, script_to_scrAddr(script))  # this uses C++
      # Go round trip to avoid dependency on the network. Works in both main-net or testnet
      self.assertEqual(scraddr, addrStr_to_scrAddr(scrAddr_to_addrStr(scraddr)))
      

      ##### Pay to PubKey65
      script = hex_to_binary( "4104"
                              "b0bd634234abbb1ba1e986e884185c61"
                              "cf43e001f9137f23c2c409273eb16e65"
                              "37a576782eba668a7ef8bd3b3cfb1edb"
                              "7117ab65129b8a2e681f3c1e0908ef7b""ac")
      a160    = hex_to_binary(  "e24b86bff5112623ba67c63b6380636cbdf1a66d")
      scraddr = hex_to_binary("00e24b86bff5112623ba67c63b6380636cbdf1a66d")
      self.assertEqual(scraddr, script_to_scrAddr(script))
      self.assertEqual(scraddr, addrStr_to_scrAddr(scrAddr_to_addrStr(scraddr)))


      ##### Pay to PubKey33
      script = hex_to_binary( "2102"
                              "4005c945d86ac6b01fb04258345abea7"
                              "a845bd25689edb723d5ad4068ddd3036""ac")
      a160    = hex_to_binary(  "0c1b83d01d0ffb2bccae606963376cca3863a7ce")
      scraddr = hex_to_binary("000c1b83d01d0ffb2bccae606963376cca3863a7ce")

      self.assertEqual(scraddr, script_to_scrAddr(script))
      self.assertEqual(scraddr, addrStr_to_scrAddr(scrAddr_to_addrStr(scraddr)))

      ##### Non-standard script
      # This was from block 150951 which was erroneously produced by MagicalTux
      # This is not only non-standard, it's non-spendable
      script  = hex_to_binary("76a90088ac")
      scraddr = hex_to_binary("ff") + hash160(hex_to_binary("76a90088ac"))

      self.assertEqual(scraddr, script_to_scrAddr(script))

      
      ##### P2SH
      script  = hex_to_binary("a914d0c15a7d41500976056b3345f542d8c944077c8a87")
      a160    = hex_to_binary(  "d0c15a7d41500976056b3345f542d8c944077c8a")
      scraddr = hex_to_binary("05d0c15a7d41500976056b3345f542d8c944077c8a")

      self.assertEqual(script,  scrAddr_to_script(scraddr))
      self.assertEqual(scraddr, script_to_scrAddr(script))  # this uses C++
      self.assertEqual(scraddr, addrStr_to_scrAddr(scrAddr_to_addrStr(scraddr)))


################################################################################
################################################################################
class BinaryPackerUnpackerTest(unittest.TestCase):

   #############################################################################
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

   #############################################################################
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

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()