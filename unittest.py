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
i    =  4093
hstr = 'fd0f'
bstr = '\xfd\x0f'


testFunction('int_to_hex',    hstr, i   )
testFunction('hex_to_int',    i,    hstr)
testFunction('int_to_binary', bstr, i   )
testFunction('binary_to_int', i,    bstr)
testFunction('hex_to_binary', bstr, hstr)
testFunction('binary_to_hex', hstr, bstr)
testFunction('hex_switchEndian', '67452301', '01234567')

blockhead = '010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d0000000000009762547903d36881a86751f3f5049e23050113f779735ef82734ebf0b4450081d8c8c84db3936a1a334b035b'
blockhash   = '1195e67a7a6d0674bbd28ae096d602e1f038c8254b49dfe79d47000000000000'
blockhashBE = '000000000000479de7df494b25c838f0e102d696e08ad2bb74066d7a7ae69511'
testFunction('hex_to_hexHash256', blockhash, blockhead)
testFunction('hex_to_hexHash256', blockhashBE, blockhead, LE, BE)

#testFunction('addrStr_to_base58Str', b58, addr)
#testFunction('base58Str_to_int', i, b58)

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



privInt = hex_to_int('2a'*32)
pvkey = EcPrivKey(privInt)

msg = int_to_binary(39029348428)
theHash = binary_to_binHash256(msg)

dersig = pvkey.derSignature(theHash)
pbkey = EcPubKey(pvkey)
print 'Testing ECDSA sign/verify:',  pbkey.verifyBinarySignature( theHash, dersig)


tx1raw= '\x01\x00\x00\x00\x02\x0f{\x7f\xb8mL\xf6F\x05\x8eA\xd3\xb0\x07\x18?\xdfysn\xd1\x9b*th\xab\xc5\xbd\x04\xb1n\x91\x00\x00\x00\x00\x8cI0F\x02!\x00\xb2\xee9\xd2\xfc\xc2\xe5TJW\xc3\x0f{NI\xcf\xb8""fm\x03O\xb9\x0e"4\x8e\x17\xe2\x8e\x0f\x02!\x00\xdb\x91\xc3\x19\x9c\xc7\xb4\x1dMz\xfc\xe0\xcc\xb4\xce\xb4$\xb9GmQ\xc0aBX=\xafS\xce\n\x9bf\x01A\x04\xc3"\x15\xa9\t0\x11\xbd<A(:\xce=\x00,f`w\xb2J`[<\xfc\x8fq\x01\x9a\x0fC\xdff\xf3\x89\xf3\xd9\xa6!\x88\xa4\x94\xb8i\xdc~_\x9d\xff\xc9\x8av\xd3\x08\x8a!\xe9\xb78\xec\x9e\xba\x98\xcb\xff\xff\xff\xff\x97\x00A%R\x8f{^\xd34e\xca\xaa\xe0!\xc0\xb8\x15\xf3\xe6\xa3pvA\xd5\xa0\xbc\xa4?\xc1II\x01\x00\x00\x00\x8aG0D\x02 3\xd0,.\x89o\x1a\x12RH\x8dSL\xfb\x08\xab\xf3\xe7\xea\x90\xab\xa7\xbaoW\xab\xf1\x89\xce\xf1\xd87\x02 \x05f\x8duP\x13\xb0\xe5\x9a*\xf5\x14_\x10\xef\xe6.\xa7\x16\xd33&\x8b\x0bZ>\xfb\xd8-\x149\xbe\x01A\x04\xc3"\x15\xa9\t0\x11\xbd<A(:\xce=\x00,f`w\xb2J`[<\xfc\x8fq\x01\x9a\x0fC\xdff\xf3\x89\xf3\xd9\xa6!\x88\xa4\x94\xb8i\xdc~_\x9d\xff\xc9\x8av\xd3\x08\x8a!\xe9\xb78\xec\x9e\xba\x98\xcb\xff\xff\xff\xff\x01\x00\xc2\xeb\x0b\x00\x00\x00\x00\x19v\xa9\x14\x02\xbfK(\x89\xc6\xad\xa8\x19\x0c%.p\xbd\xe1\xa1\x90\x9f\x96\x17\x88\xac\x00\x00\x00\x00'
tx2raw= "\x01\x00\x00\x00\x030\xf3p\x1f\x9b\xc4dU/pIW\x91\x04\x08\x17\xcewz\xd5\xed\xe1nR\x9f\xcd\x0c\x0e\x94\x91V\x94\x00\x00\x00\x00\x8cI0F\x02!\x00\xf5tk\x0b%OZ7\xe7RQE\x9cz#\xb6\xdf\xcb\x86\x8a\xc7F~\xdd\x9ao\xdd\x1d\x96\x98q\xbe\x02!\x00\x88\x94\x8a\xea)\xb6\x91a\xca4\x1cI\xc0&\x86\xa8\x1d\x8c\xbbs\x94\x0f\x91\x7f\xa0\xedqThm>[\x01A\x04G\xd4\x90V\x1f9l\x8a\x9e\xfc\x14Hk\xc1\x98\x88K\xa1\x83y\xbc\xac.\x0b\xe2\xd8RQ4\xabt/0\x1a\x9a\xca6`n])\xaa#\x8a\x9e)\x93\x001PB=\xf6\x92Ecd-J\xfe\x9b\xf4\xfe(\xff\xff\xff\xffr\x14+\xf7hl\xe9,m\xe5\xb73e\xbf\xb9\xd5\x9b\xb6\x0c,\x80\x98-YX\xc1\xe6\xa3\xb0\x8e\xa6\x89\x00\x00\x00\x00JI0F\x02!\x00\xbc\xe4:\xd3\xac\xbcy\xb0$~T\xc8\xc9\x1e\xac\x1c\xf9\x03u\x05\x00\x0e\x01\xd1\xfd\x81\x18T\xd8[\xc2\x1a\x02!\x00\x99*oo/\xebob\xd3po;\x9a\xaa\xb8\x8d\x9f\x112\x95j\x1d\xff\xa9&\xcdUn\xd5S`\xdf\x01\xff\xff\xff\xff\xd2\x81(\xbb\xb6 |\x1c=\nc\x0c\xc6\x19\xdc~{\xeaV\xac\x19\xa1\xda\xb1'\xc6,x\xfa\x1bc,\x00\x00\x00\x00IH0E\x02  \x97W6\x81aSw\x08\xfd)\xd8\x9b\xb1\xe9\xd6H\x00yI\xec\xfd\xedx\x9bQ\xa9c$\xcbe\x18\x02!\x00\xcd\x0f|0!9\x16H+n\x16m\x8aO+\x98\x1fw~\xb1\x84\xcd\x8aI_\x1b=6\x90\xfb\xbf-\x01\xff\xff\xff\xff\x01\x00\xa6\xf7_\x02\x00\x00\x00\x19v\xa9\x14\x9e5\xd9<w\x92\xbd\xca\xadV\x97\xdd\xeb\xf0CS\xd9\xa5\xe1\x96\x88\xac\x00\x00\x00\x00"

tx1 = Tx().unserialize(tx1raw)
tx2 = Tx().unserialize(tx2raw)

tx1.pprint()
print '\n'*3
tx2.pprint()
print '\n'*3


#tx1ser = tx1.serialize()
#print tx1ser == tx1raw


exBlock = (
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
    '23faa676485a53817af975ddf85a104f764fb93b02201ac6af32ddf597e610b4002e41f2de46664587a379a0161323a85389b4f82dda014104ec8883d3e4f7a3'
    '9d75c9f5bb9fd581dc9fb1b7cdf7d6b5a665e4db1fdb09281a74ab138a2dba25248b5be38bf80249601ae688c90c6e0ac8811cdb740fcec31dffffffff022f66'
    'ac61050000001976a914964642290c194e3bfab661c1085e47d67786d2d388ac2f77e200000000001976a9141486a7046affd935919a3cb4b50a8a0c233c286c'
    '88ac00000000')

blk = Block().unserialize( hex_to_binary(exBlock) )
blk.pprint()

print blk.serialize()

print binary_to_hex( blk.header.serialize() )


blk.pprint()

ser = blk.serialize()
blk.unserialize(ser)

blk.pprint()
