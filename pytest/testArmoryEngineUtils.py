'''
Created on Jul 29, 2013

@author: Andy
'''
import sys
sys.path.append('..')
import hashlib
import locale
import os
import tempfile
import time
import unittest

from armoryengine import ArmoryUtils
from armoryengine.ALL import *
from armoryengine.ArmorySettings import SettingsFile
from armoryengine.BitSet import BitSet


UNICODE_STRING = u'unicode string'
NON_ASCII_STRING = '\xff\x00 Non-ASCII string \xff\x00'
ASCII_STRING = 'ascii string'
LONG_TEST_NUMBER = 98753178900


################################################################################
################################################################################
class ArmoryEngineTest(unittest.TestCase):


   #############################################################################
   def setUp(self):
      useMainnet()
      initializeOptions()
      self.tmpdir = tempfile.mkdtemp("armory_engineutils")
      setArmoryHomeDir(self.tmpdir)


   #############################################################################
   def tearDown(self):
      shutil.rmtree(self.tmpdir)


   #############################################################################
   def testSwitch(self):
      useMainnet()
      # set the rpc port back to the default
      ARMORY_OPTIONS.satoshiPort = DEFAULT
      self.assertFalse(getTestnetFlag())
      self.assertEqual(getBitcoinPort(), 8333)
      self.assertEqual(getAddrByte(), '\x00')
      useTestnet()
      self.assertTrue(getTestnetFlag())
      self.assertEqual(getBitcoinPort(), 18333)
      self.assertEqual(getAddrByte(), '\x6f')
      useMainnet()
      self.assertFalse(getTestnetFlag())
      self.assertEqual(getBitcoinPort(), 8333)
      self.assertEqual(getAddrByte(), '\x00')


   #############################################################################
   def testPrintArmoryInfo(self):
      result = getPrintableArmoryInfo()
      self.assertTrue(getArmoryHomeDir() in result)
      self.assertTrue(getOS() in result)


   #############################################################################
   def testLog(self):
      for func in (LOGDEBUG, LOGINFO, LOGWARN, LOGERROR, LOGEXCEPT, LOGCRIT):
         func("test")
         self.assertRaises(TypeError, func, "some string %s", "toomany", "args")
      LOGPPRINT(PayloadVerack())
      LOGRAWDATA('03000000fd1bc6371eae1a73fcd78f8ef3f9b273b4224d570711e68351cd')


   #############################################################################
   def testGetExecDir(self):
      self.assertTrue(GetExecDir() in os.path.realpath(__file__))

   #############################################################################
   def testSatoshiIsAvailable(self):
      self.assertFalse(satoshiIsAvailable(port=9999))

   #############################################################################
   def testMakeSixteenBytesEasy(self):
      self.assertRaises(ValueError, makeSixteenBytesEasy, '')
      text = "hellotherejoseph"
      self.assertEqual(makeSixteenBytesEasy(text),
                       'jwjh juju jnkg jwjh  kdjh jrjn kfjh kajw  dejt')

   #############################################################################
   def testSecondsToHumanTime(self):
      outputs = { 1: 'second', 60: 'minute', 3600: 'hour', 86400: 'day',
                  7*86400: 'week', 31*86400: 'month', 365*86400: 'year',}
      for seconds, human in outputs.items():
         self.assertEqual(secondsToHumanTime(seconds), '1 %s' % human)
         self.assertEqual(secondsToHumanTime(1.5*seconds), '1.5 %ss' % human)
         self.assertEqual(secondsToHumanTime(2*seconds), '2 %ss' % human)

   #############################################################################
   def testBytesToHumanSize(self):
      outputs = {2**10:'kB', 2**20:'MB', 2**30:'GB', 2**40:'TB',
                 2**50:'PB'}
      self.assertEqual(bytesToHumanSize(10), "10 bytes")
      for b, human in outputs.items():
         self.assertEqual(bytesToHumanSize(b), "1.0 %s" % human)

   #############################################################################
   def testCreateQRMatrix(self):
      data = createBitcoinURI('2MuKNwPm3cxwB4L473ZwowttqpfD5stqdSg',
                              0.1, "test(this)")
      self.assertEqual(CreateQRMatrix(data, 'H')[1], 49)

   #############################################################################
   def testEstimateCumulativeBlockSize(self):
      self.assertEqual(EstimateCumulativeBlockchainSize(0), 285)
      self.assertEqual(EstimateCumulativeBlockchainSize(100800), 60605119)
      self.assertTrue(EstimateCumulativeBlockchainSize(170000) > 100000000)
      self.assertTrue(EstimateCumulativeBlockchainSize(400000) > 42000000000)

   #############################################################################
   def testGetBlockID(self):
      asciiText = ["=====LOCKBOX-12345678===========\n",
                  "ckhc3hqhhuih7gGGOUT78hweds\n",
                  "================================\n",
                  "=====LOCKBOX-AbCdEfGh===========\n",
                  "ckhc3hqhhuih7gGGOUT78hweds\n",]

      self.assertEqual(getBlockID(asciiText, 'LOCKBOX'),
                       ['-12345678', '-AbCdEfGh'])

   #############################################################################
   def testGetLastBytesOfFile(self):
      filename = b"test.file"
      f = open(filename, b"wb")
      f.write("hello")
      f.close()
      self.assertEqual(getLastBytesOfFile(filename,3), "llo")

   #############################################################################
   def testHardcodedKeyMask(self):
      params = HardcodedKeyMaskParams()
      secret = "\x00"
      self.assertEqual(len(params), 8)
      securePrint = params['FUNC_PWD'](secret)
      self.assertEqual(securePrint.getSize(), 11)
      self.assertTrue(params['FUNC_CHKPWD'](securePrint))
      maskKey = params['FUNC_KDF'](securePrint)
      data = SecureBinaryData('a')
      masked = params['FUNC_MASK'](data, ekey=maskKey)
      self.assertEqual(masked.getSize(), data.getSize())
      unmasked = params['FUNC_UNMASK'](masked, ekey=maskKey)
      self.assertEqual(unmasked.getSize(), data.getSize())
      # TODO the unmasked version should be the same as the original
      # make that test work

   #############################################################################
   def testSettingsFile(self):
      fileName = 'settings.test'
      sf = SettingsFile(fileName)
      sf.set('a','b')
      sf.pprint()
      self.assertTrue(sf.hasSetting('a'))
      self.assertFalse(sf.hasSetting('1'))
      self.assertEqual(sf.get('a'), 'b')
      sf.extend('a','c')
      self.assertEqual(sf.getSettingOrSetDefault('a', 'd'), ['b','c'])
      self.assertEqual(len(sf.getAllSettings()), 1)
      self.assertEqual(sf.getSettingOrSetDefault('z', 'd'), 'd')
      self.assertEqual(sf.get('a'), ['b','c'])
      sf.delete('z')
      sf2 = SettingsFile(fileName)
      self.assertEqual(sf2.get('a'), ['b','c'])
      removeIfExists(fileName)

   #############################################################################
   def testIsInternetAvailable(self):
      self.assertEqual(isInternetAvailable(), INTERNET_STATUS.Available)


   #############################################################################
   def testCalcWalletID(self):
      wid = 'BWrVHaTU'
      self.assertEqual(calcWalletID('\x00' * 16), wid)

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
      self.callTestFunction('_decodeMiniPrivateKey', miniPriv, miniKey)

      self.callTestFunction('coin2str','            0.0000', 0, 4)

      self.callTestFunction('coin2str','          987.5318', LONG_TEST_NUMBER, 4)
      self.callTestFunction('coin2str','987.53178900', LONG_TEST_NUMBER, 8, False)
      self.callTestFunction('coin2str','987.5317890000', LONG_TEST_NUMBER, 12, False, 10)
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
   def testBitcoinUriParser(self):
      ##### Test BIP 0021 parser functions.
      uri1 = "bitcoin:1BTCorgHwCg6u2YSAWKgS17qUad6kHmtQW?amount=0.1&label=Foo%20bar&r=https://example.com/foo/bar/"
      uri2 = "bitcoin:mq7se9wy2egettFxPbmn99cK8v5AFq55Lx?amount=0.11&r=https://merchant.com/pay.php?h%3D2a8628fc2fbe"
      uri3 = "bitcoin:175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W"
      uri4 = "bitcoin:175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W?label=Luke-Jr"
      uri5 = "bitcoin:175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W?amount=20.3&label=Luke-Jr"
      uri6 = "bitcoin:175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W?amount=50&label=Luke-Jr&message=Donation%20for%20project%20xyz"
      uri7 = "bitcoin:175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W?req-somethingyoudontunderstand=50&req-somethingelseyoudontget=999"
      uri8 = "bitcoin:175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W?somethingyoudontunderstand=50&somethingelseyoudontget=999"

      expectedOut1 = {
         "address": "1BTCorgHwCg6u2YSAWKgS17qUad6kHmtQW",
         "amount": 10000000,
         "label": "Foo bar",
         "r": "https://example.com/foo/bar/"
      }
      expectedOut2 = {
         "address": "mq7se9wy2egettFxPbmn99cK8v5AFq55Lx",
         "amount": 11000000,
         "r": "https://merchant.com/pay.php?h=2a8628fc2fbe"
      }
      expectedOut3 = {
         "address": "175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W"
      }
      expectedOut4 = {
         "address": "175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W",
         "label": "Luke-Jr"
      }
      expectedOut5 = {
         "address": "175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W",
         "amount": 2030000000,
         "label": "Luke-Jr"
      }
      expectedOut6 = {
         "address": "175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W",
         "amount": 5000000000,
         "label": "Luke-Jr",
         "message": "Donation for project xyz"
      }
      expectedOut7 = {
         "address": "175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W",
         "req-somethingyoudontunderstand": "50",
         "req-somethingelseyoudontget": "999"
      }
      expectedOut8 = {
         "address": "175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W",
         "somethingyoudontunderstand": "50",
         "somethingelseyoudontget": "999"
      }

      parseOut1 = parseBitcoinURI(uri1)
      parseOut2 = parseBitcoinURI(uri2)
      parseOut3 = parseBitcoinURI(uri3)
      parseOut4 = parseBitcoinURI(uri4)
      parseOut5 = parseBitcoinURI(uri5)
      parseOut6 = parseBitcoinURI(uri6)
      parseOut7 = parseBitcoinURI(uri7)
      parseOut8 = parseBitcoinURI(uri8)
      self.assertEqual(parseOut1, expectedOut1)
      self.assertEqual(parseOut2, expectedOut2)
      self.assertEqual(parseOut3, expectedOut3)
      self.assertEqual(parseOut4, expectedOut4)
      self.assertEqual(parseOut5, expectedOut5)
      self.assertEqual(parseOut6, expectedOut6)
      self.assertEqual(parseOut7, expectedOut7)
      self.assertEqual(parseOut8, expectedOut8)


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
      self.assertEqual(prefix, getAddrByte())
      self.assertEqual(a160, hashVal)
      self.assertFalse(addrStr_is_p2sh(addrStr00))

      prefix, a160 = addrStr_to_hash160(addrStr05)
      self.assertEqual(prefix, getP2SHByte())
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
   def setUp(self):
      useMainnet()

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


################################################################################
class BitSetTests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      useMainnet()

   #############################################################################
   def testBitSets(self):
      bs = BitSet()
      self.assertEqual(bs.getNumBits(), 0)
      self.assertEqual(len(bs), 0)
      self.assertEqual(bs.toInteger(), 0)
      self.assertEqual(bs.toBitString(), '')
      self.assertEqual(bs.toBinaryString(), '')

      bs = BitSet(0)
      self.assertEqual(bs.getNumBits(), 0)
      self.assertEqual(bs.toInteger(), 0)
      self.assertEqual(bs.toBitString(), '')
      
      bs = BitSet(1)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(), 0)
      self.assertEqual(bs.toBitString(), '00000000')
      self.assertEqual(bs.toBinaryString(), '\x00')
      
      bs = BitSet(7)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(), 0)
      self.assertEqual(bs.toBitString(), '00000000')

      bs = BitSet(8)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(), 0)
      self.assertEqual(bs.toBitString(), '00000000')

      bs = BitSet(9)
      self.assertEqual(bs.getNumBits(), 16)
      self.assertEqual(bs.toInteger(), 0)
      self.assertEqual(bs.toBitString(), '00000000'*2)
      self.assertEqual(bs.toBinaryString(), '\x00\x00')

      bs = BitSet.CreateFromInteger(9)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(len(bs), 8)
      self.assertEqual(bs.toInteger(), 9)
      self.assertEqual(bs.toBitString(), '00001001')

      bs = BitSet.CreateFromInteger(9, 14)
      self.assertEqual(bs.getNumBits(), 16)
      self.assertEqual(len(bs), 16)
      self.assertEqual(bs.toInteger(), 9)
      self.assertEqual(bs.toBitString(), '0000000000001001')

      bs = BitSet.CreateFromInteger(9, 16)
      self.assertEqual(bs.getNumBits(), 16)
      self.assertEqual(bs.toInteger(), 9)
      self.assertEqual(bs.toBitString(), '0000000000001001')
      self.assertEqual(bs.toBinaryString(), '\x00\x09')

      bs = BitSet.CreateFromInteger(1, 40)
      self.assertEqual(bs.getNumBits(), 40)
      self.assertEqual(bs.toInteger(), 1)
      self.assertEqual(bs.toBitString(), '0'*39 + '1')
      self.assertEqual(bs.toBinaryString(), '\x00\x00\x00\x00\x01')


      bs = BitSet.CreateFromInteger(9)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(), 9)
      self.assertEqual(bs.toBitString(), '00001001')
      self.assertEqual(bs.getBit(0), 0)
      bs.setBit(0, 1)
      self.assertEqual(bs.getBit(0), 1)
      self.assertEqual(bs.toBitString(), '10001001')
      self.assertEqual(bs.toInteger(), 137)
      self.assertEqual(bs.getBit(7), 1)
      bs.setBit(7, 1)
      self.assertEqual(bs.getBit(7), 1)
      self.assertEqual(bs.toBitString(), '10001001')
      self.assertEqual(bs.toInteger(), 137)
      bs.setBit(7, 0)
      self.assertEqual(bs.getBit(7), 0)
      self.assertEqual(bs.toBitString(), '10001000')
      self.assertEqual(bs.toInteger(), 136)
      bs.setBit(1, 1)
      self.assertEqual(bs.toBitString(), '11001000')
      self.assertEqual(bs.toInteger(), 200)
      for i in range(8):
         self.assertEqual(int('11001000'[i]), bs.getBit(i))
      self.assertRaises(IndexError, bs.setBit, 9, 1)

      self.assertEqual(bs.toBinaryString(), '\xc8')


      # Test Reset functions
      bs = BitSet.CreateFromInteger(9)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(), 9)
      self.assertEqual(bs.toBitString(), '00001001')
      bs.reset()
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(),  0)
      self.assertEqual(bs.toBitString(), '00000000')
      self.assertEqual(bs.toBinaryString(), '\x00')
      bs.reset(1)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(),  255)
      self.assertEqual(bs.toBitString(), '11111111')
      self.assertEqual(bs.toBinaryString(), '\xff')
      bs.reset(False)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(),  0)
      self.assertEqual(bs.toBitString(), '00000000')
      self.assertEqual(bs.toBinaryString(), '\x00')
      bs.reset(True)
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(),  255)
      self.assertEqual(bs.toBitString(), '11111111')
      self.assertEqual(bs.toBinaryString(), '\xff')

      # Test reading bit strings
      bs = BitSet.CreateFromBitString('11001000')
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(), 200)
      self.assertEqual(bs.toBitString(), '11001000')
      self.assertEqual(bs.getBit(0), 1)
      self.assertEqual(bs.getBit(2), 0)

      bs = BitSet.CreateFromBitString('00000001 11001000')
      self.assertEqual(bs.getNumBits(), 16)
      self.assertEqual(bs.toInteger(), 456)
      self.assertEqual(bs.toBitString(), '0000000111001000')
      self.assertEqual(bs.getBit(0), 0)
      self.assertEqual(bs.getBit(7), 1)
      self.assertEqual(bs.getBit(8), 1)

      bs = BitSet.CreateFromBitString('00000001 1100100')
      self.assertEqual(bs.getNumBits(), 16)
      self.assertEqual(bs.toInteger(), 456)
      self.assertEqual(bs.toBitString(), '0000000111001000')
      self.assertEqual(bs.getBit(0), 0)
      self.assertEqual(bs.getBit(7), 1)
      self.assertEqual(bs.getBit(8), 1)

      # Test reading binary strings
      bs = BitSet.CreateFromBinaryString('\xc8')
      self.assertEqual(bs.getNumBits(), 8)
      self.assertEqual(bs.toInteger(), 200)
      self.assertEqual(bs.toBitString(), '11001000')
      self.assertEqual(bs.toBinaryString(), '\xc8')
      self.assertEqual(bs.getBit(0), 1)
      self.assertEqual(bs.getBit(2), 0)


      bs = BitSet.CreateFromBinaryString('\x01\xc8')
      self.assertEqual(bs.getNumBits(), 16)
      self.assertEqual(bs.toInteger(), 456)
      self.assertEqual(bs.toBitString(), '0000000111001000')
      self.assertEqual(bs.toBinaryString(), '\x01\xc8')
      self.assertEqual(bs.getBit(0), 0)
      self.assertEqual(bs.getBit(7), 1)
      self.assertEqual(bs.getBit(8), 1)


      # Test copy operations
      bs1 = BitSet.CreateFromBitString('11110000 11110001')
      self.assertEqual(bs1.getNumBits(), 16)
      self.assertEqual(bs1.toInteger(), 61681)

      bs2 = bs1.copy()
      self.assertEqual(bs2.getNumBits(), 16)
      self.assertEqual(bs2.toInteger(), 61681)
      self.assertEqual(bs2.toBitString(), '1111000011110001')

      bs3 = bs1.copy(newSize=8)
      self.assertEqual(bs3.getNumBits(), 8)
      self.assertEqual(bs3.toInteger(), 240)
      self.assertEqual(bs3.toBitString(), '11110000')

      bs4 = bs3.copy(newSize=32)
      self.assertEqual(bs4.getNumBits(), 32)
      self.assertEqual(bs4.toInteger(), 240<<24)
      self.assertEqual(bs4.toBitString(), '11110000' + '0'*24)

      # Test slicing
      bs1 = BitSet.CreateFromBitString('11110000 11110001 01010101')
      bs2 = bs1.getSlice( 0, 8)
      bs3 = bs1.getSlice( 8, 8)
      bs4 = bs1.getSlice(16, 8)
      bs5 = bs1.getSlice( 8,16)
      bs6 = bs1.getSlice( 5, 8)

      self.assertEqual(bs2.toBitString(),  '11110000')
      self.assertEqual(bs3.toBitString(),  '11110001')
      self.assertEqual(bs4.toBitString(),  '01010101')
      self.assertEqual(bs5.toBitString(),  '1111000101010101')
      self.assertEqual(bs6.toBitString(),  '00011110')
      

      # Test binary packer/unpacker methods
      bs = BitSet.CreateFromBitString('11110000 11110001 01010101')
      self.assertEqual(bs.toBinaryString(), '\xf0\xf1\x55')
      bp = BinaryPacker()
      bp.put(UINT8,  255)
      bp.put(BITSET, bs, 3)
      bp.put(BINARY_CHUNK, '\x2a')
      self.assertEqual(bp.getBinaryString(), '\xff\xf0\xf1\x55\x2a')
      bu = BinaryUnpacker(bp.getBinaryString())
      self.assertEqual(bu.get(UINT8), 255)
      newBS = bu.get(BITSET, 3)
      self.assertEqual(bu.get(BINARY_CHUNK, 1), '\x2a')
      self.assertEqual(newBS.getNumBits(), 24)
      self.assertEqual(newBS.toBinaryString(), '\xf0\xf1\x55')

      bs = BitSet.CreateFromBitString('11110000 11110001 01010101')
      self.assertEqual(bs.toBinaryString(), '\xf0\xf1\x55')
      bp = BinaryPacker()
      self.assertRaises(PackerError, bp.put, BITSET, bs, 2)

      bs = BitSet.CreateFromBitString('11110000 11110001 01010101')
      self.assertEqual(bs.toBinaryString(), '\xf0\xf1\x55')
      bp = BinaryPacker()
      bp.put(BITSET, bs, 5)
      self.assertEqual(bp.getBinaryString(), '\xf0\xf1\x55\x00\x00')



################################################################################
class ParsePrivKeyTests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      useMainnet()

   #############################################################################
   def testParseKeys(self):

      # This is from the BIP32 test vectors
      addrStr = '19Q2WoS5hSS6T8GjhK8KZLMgmWaq4neXrh'
      privHex = 'edb2e14f9ee77d26dd93b4ecede8d16ed408ce149b6cd80b0715a2d911a0afea'
      privWIF = 'L5BmPijJjrKbiUfG4zbiFKNqkvuJ8usooJmzuD7Z8dkRoTThYnAT'
      xprvB58 = ('xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rG'
                 'L5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7')
      xprvHex = ('0488ade4013442193e8000000047fdacbd0f1097043b78c63c20c34ef4ed9a11'
                 '1d980047ad16282c7ae623614100edb2e14f9ee77d26dd93b4ecede8d16ed408'
                 'ce149b6cd80b0715a2d911a0afea')
      pubkHex = '035a784662a4a20a65bf6aab9ae98a6c068a81c52e4b032c0fb5400c706cfccc56'
      xpubB58 = ('xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhw'
                 'BZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw')
      xpubHex = ('0488b21e013442193e8000000047fdacbd0f1097043b78c63c20c34ef4ed9a11'
                 '1d980047ad16282c7ae6236141035a784662a4a20a65bf6aab9ae98a6c068a81'
                 'c52e4b032c0fb5400c706cfccc56')


      # Will return 32-byte binary of "privHex" var above
      privHex33  = privHex + '01'
      privBin33  = hex_to_binary(privHex33)
      privWIFHex = binary_to_hex(base58_to_binary(privWIF))
      privXprv58 = xprvB58

      self.assertEqual(parsePrivateKeyData(privHex33, privkeybyte='\x80')[0],  privBin33)
      self.assertEqual(parsePrivateKeyData(privWIF, privkeybyte='\x80')[0],    privBin33)
      self.assertEqual(parsePrivateKeyData(privWIFHex, privkeybyte='\x80')[0], privBin33)
      self.assertEqual(parsePrivateKeyData(privXprv58, privkeybyte='\x80')[0], privBin33)
      
      # This is from the wiki page on mini private keys used in Casascius coins
      miniStr  = 'S6c56bnXQiBjk9mqSYE7ykVQ7NzrRy'
      miniPriv = '4c7a9640c72dc2099f23715d0c8a0d8a35f8906e3cab61dd3f78b67bf887c9ab'
      miniWIF  = '5JPy8Zg7z4P7RSLsiqcqyeAF1935zjNUdMxcDeVrtU1oarrgnB7'
      miniAddr = '1CciesT23BNionJeXrbxmjc7ywfiyM4oLW'

      miniBin = hex_to_binary(miniPriv)

      self.assertEqual(parsePrivateKeyData(miniStr, privkeybyte='\x80')[0],   miniBin)
      self.assertEqual(parsePrivateKeyData(miniPriv, privkeybyte='\x80')[0],  miniBin)
      self.assertEqual(parsePrivateKeyData(miniWIF, privkeybyte='\x80')[0],   miniBin)

      self.assertEqual(len(parsePrivateKeyData('5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf', privkeybyte='\x80')[0]), 32)
