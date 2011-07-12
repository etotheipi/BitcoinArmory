import PyBtcEngine as eng

LE = eng.LITTLEENDIAN
BE = eng.BIGENDIAN


# Pass in the name of a function,
def testFunction( fnName, expectedOutput, *args):
   fn = getattr(eng, fnName)
   print '\tTesting function:', fnName
   actualOutput = fn(*args)
   testPassed = (expectedOutput == actualOutput)
   passStr = 'PASS' if testPassed else '***FAIL***'
   print '\t\t',passStr
   if not testPassed:
      print '\t','___Inputs___:', args
      print '\t','___ExpOut___:', expectedOutput
      print '\t','___ActOut___:', actualOutput
      
   

print '*** Running Bitcoin engine unit tests ***'

addr = '1Ncui8YjT7JJD91tkf42dijPnqywbupf7w'  # Sam Rushing's BTC address
b58  =  'Ncui8YjT7JJD91tkf42dijPnqywbupf7w'
i    =  5814786094848085103559667442017195135920933988948668162114L
hstr = 'ed2533122ffd7f0724c424599206ccb23e89d6f79641a042'
bstr = '\xed%3\x12/\xfd\x7f\x07$\xc4$Y\x92\x06\xcc\xb2>\x89\xd6\xf7\x96A\xa0B'

testFunction('hexStr_switchEndian', '67452301', '01234567')
testFunction('addrStr_to_base58Str', b58, addr)
testFunction('base58Str_to_int', i, b58)
testFunction('int_to_hexStr', hstr, i)
testFunction('hexStr_to_binStr', bstr, hstr)

blockhead = '01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc604d91b9b7541a4ecfbb0a1a64f1ade7'
blockhash   = '7d97d862654e03d6c43b77820a40df894e3d6890784528e9cd05000000000000'
blockhashBE = '00000000000005cde928457890683d4e89df400a82773bc4d6034e6562d8977d'

testFunction('hexStr_to_hexHash256', blockhash, blockhead)
testFunction('hexStr_to_hexHash256', blockhashBE, blockhead, LE, BE)

pubKeyHex  = '123abc'
pubKeyAddr = '1NePmEXs4sqRGXqPrYAWc9V9eTBBGCfg7B'

testFunction('hexPubKey_to_addrStr', pubKeyAddr, pubKeyHex)
testFunction('verify_addrStr', True, pubKeyAddr)

testFunction('ubtc_to_floatStr', '12.05600000', 1205600000)
testFunction('floatStr_to_ubtc', 1205600000, '12.056')
testFunction('float_to_btc', 1205600000, 12.056)


testFunction('packVarInt', ['A',1], 65)
testFunction('packVarInt', ['\xfd\xff\x00', 3], 255)
testFunction('packVarInt', ['\xfe\x00\x00\x01\x00', 5], 65536)
testFunction('packVarInt', ['\xff\x00\x10\xa5\xd4\xe8\x00\x00\x00', 9], 10**12)

testFunction('unpackVarInt', [65,1], 'A')
testFunction('unpackVarInt', [255, 3], '\xfd\xff\x00')
testFunction('unpackVarInt', [65536, 5], '\xfe\x00\x00\x01\x00')
testFunction('unpackVarInt', [10**12, 9], '\xff\x00\x10\xa5\xd4\xe8\x00\x00\x00')
