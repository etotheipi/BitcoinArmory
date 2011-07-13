from PyBtcEngine import *
import PyBtcEngine

LE = LITTLEENDIAN
BE = BIGENDIAN


# Pass in the name of a function,
def testFunction( fnName, expectedOutput, *args):
   fn = getattr(PyBtcEngine, fnName)
   actualOutput = fn(*args)
   testPassed = (expectedOutput == actualOutput)
   passStr = '____PASS____' if testPassed else '***FAIL***'
   print '\t', passStr, '( function:', fnName, ')'
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


testFunction('hex_switchEndian', '67452301', '01234567')
testFunction('addrStr_to_base58Str', b58, addr)
testFunction('base58Str_to_int', i, b58)
testFunction('int_to_hex', hstr, i)
testFunction('hex_to_binary', bstr, hstr)

blockhead = '01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc604d91b9b7541a4ecfbb0a1a64f1ade7'
blockhash   = '7d97d862654e03d6c43b77820a40df894e3d6890784528e9cd05000000000000'
blockhashBE = '00000000000005cde928457890683d4e89df400a82773bc4d6034e6562d8977d'

testFunction('hex_to_hexHash256', blockhash, blockhead)
testFunction('hex_to_hexHash256', blockhashBE, blockhead, LE, BE)

# Execute the tests with Satoshi's public key from the Bitcoin specification page
satoshiPubKeyHex = '04fc9702847840aaf195de8442ebecedf5b095cdbb9bc716bda9110971b28a49e0ead8564ff0db22209e0374782c093bb899692d524e9d6a6956e7c5ecbcd68284'
satoshiAddrStr = '1AGRxqDa5WjUKBwHB9XYEjmkv1ucoUUy1s'

addrPiece1Hex = '65a4358f4691660849d9f235eb05f11fabbd69fa'
addrPiece2Hex = 'd8b2307a'
addrPiece1Bin = hex_to_binary(addrPiece1Hex)
addrPiece2Bin = hex_to_binary(addrPiece2Hex)

testFunction('hexPubKey_to_addrStr', satoshiAddrStr, satoshiPubKeyHex)
testFunction('addrStr_to_binaryPair', (addrPiece1Bin, addrPiece2Bin), satoshiAddrStr)
testFunction('addrStr_isValid', True, satoshiAddrStr)

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


satoshiPubKeyBin = hex_to_binary(satoshiPubKeyHex)

block_135687 = (
    '01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc'
    '604d91b9b7541a4ecfbb0a1a64f1ade70301000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0804cfbb0a1a'
    '02360affffffff0100f2052a01000000434104c2239c4eedb3beb26785753463be3ec62b82f6acd62efb65f452f8806f2ede0b338e31d1f69b1ce449558d7061'
    'aa1648ddc2bf680834d3986624006a272dc21cac000000000100000003e8caa12bcb2e7e86499c9de49c45c5a1c6167ea4b894c8c83aebba1b6100f343010000'
    '008c493046022100e2f5af5329d1244807f8347a2c8d9acc55a21a5db769e9274e7e7ba0bb605b26022100c34ca3350df5089f3415d8af82364d7f567a6a297f'
    'cc2c1d2034865633238b8c014104129e422ac490ddfcb7b1c405ab9fb42441246c4bca578de4f27b230de08408c64cad03af71ee8a3140b40408a7058a1984a9'
    'f246492386113764c1ac132990d1ffffffff5b55c18864e16c08ef9989d31c7a343e34c27c30cd7caa759651b0e08cae0106000000008c4930460221009ec9aa'
    '3e0caf7caa321723dea561e232603e00686d4bfadf46c5c7352b07eb00022100a4f18d937d1e2354b2e69e02b18d11620a6a9332d563e9e2bbcb01cee559680a'
    '014104411b35dd963028300e36e82ee8cf1b0c8d5bf1fc4273e970469f5cb931ee07759a2de5fef638961726d04bd5eb4e5072330b9b371e479733c942964bb8'
    '6e2b22ffffffff3de0c1e913e6271769d8c0172cea2f00d6d3240afc3a20f9fa247ce58af30d2a010000008c493046022100b610e169fd15ac9f60fe2b507529'
    '281cf2267673f4690ba428cbb2ba3c3811fd022100ffbe9e3d71b21977a8e97fde4c3ba47b896d08bc09ecb9d086bb59175b5b9f03014104ff07a1833fd8098b'
    '25f48c66dcf8fde34cbdbcc0f5f21a8c2005b160406cbf34cc432842c6b37b2590d16b165b36a3efc9908d65fb0e605314c9b278f40f3e1affffffff0240420f'
    '00000000001976a914adfa66f57ded1b655eb4ccd96ee07ca62bc1ddfd88ac007d6a7d040000001976a914981a0c9ae61fa8f8c96ae6f8e383d6e07e77133e88'
    'ac00000000010000000138e7586e0784280df58bd3dc5e3d350c9036b1ec4107951378f45881799c92a4000000008a47304402207c945ae0bbdaf9dadba07bdf'
    '23faa676485a53817af975ddf85a104f764fb93b02201ac6af32ddf597e610b4002e41f2de46664587a379a0161323a8gg5389b4f82dda014104ec8883d3e4f7a3'
    '9d75c9f5bb9fd581dc9fb1b7cdf7d6b5a665e4db1fdb09281a74ab138a2dba25248b5be38bf80249601ae688c90c6e0ac8811cdb740fcec31dffffffff022f66'
    'ac61050000001976a914964642290c194e3bfab661c1085e47d67786d2d388ac2f77e200000000001976a9141486a7046affd935919a3cb4b50a8a0c233c286c'
    '88ac00000000'
    )

#outHash = '3de0c1e913e6271769d8c0172cea2f00d6d3240afc3a20f9fa247ce58af30d2a' 
#index   = int_to_hex(1)
#scriptLen = hex_to_int('49')
#script  = '3046022100b610e169fd15ac9f60fe2b507529281cf2267673f4690ba428cbb2ba3c3811fd022100ffbe9e3d71b21977a8e97fde4c3ba47b896d08bc09ecb9d086bb59175b5b9f03014104ff07a1833fd8098b25f48c66dcf8fde34cbdbcc0f5f21a8c2005b160406cbf34cc432842c6b37b2590d16b165b36a3efc9908d65fb0e605314c9b278f40f3e1a'
#seq =  int_to_hex(4294967295)

#exampleScriptHex = '493046022100e2f5af5329d1244807f8347a2c8d9acc55a21a5db769e9274e7e7ba0bb605b26022100c34ca3350df5089f3415d8af82364d7f567a6a297fcc2c1d2034865633238b8c014104129e422ac490ddfcb7b1c405ab9fb42441246c4bca578de4f27b230de08408c64cad03af71ee8a3140b40408a7058a1984a9f246492386113764c1ac132990d1'
#pkHex = '04129e422ac490ddfcb7b1c405ab9fb42441246c4bca578de4f27b230de08408c64cad03af71ee8a3140b40408a7058a1984a9f246492386113764c1ac132990d1'
#signHex = '3046022100e2f5af5329d1244807f8347a2c8d9acc55a21a5db769e9274e7e7ba0bb605b26022100c34ca3350df5089f3415d8af82364d7f567a6a297fcc2c1d2034865633238b8c01'

#[bsig, bkey, nb] = binScript_to_binSigKey( hex_to_binary(exampleScriptHex))
#addr = binPubKey_to_addrStr(bkey)

#print binary_to_hex(bsig)
#print binary_to_hex(bkey)
#print binPubKey_to_addrStr(bkey)

#pubkey = EcPubKey(bkey)
#print pubkey



privInt = hex_to_int('2a'*30)
pvkey = EcPrivKey(privInt)
msg = int_to_binary(39029348428)
dersig = pvkey.derSignature(msg)
pbkey = EcPubKey(pvkey)
pbkey.verifyBinarySignature( msg, dersig)

