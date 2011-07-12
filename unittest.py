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

testFunction('hexHash256_hexStr', blockhash, blockhead)
testFunction('hexHash256_hexStr', blockhashBE, blockhead, LE, BE)

testFunction('verify_addrStr', True, addr)
