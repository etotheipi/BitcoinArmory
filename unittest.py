from btcarmoryengine import *
import btcarmoryengine

LE = LITTLEENDIAN
BE = BIGENDIAN


# Pass in the name of a function,
def testFunction( fnName, expectedOutput, *args):
   fn = getattr(btcarmoryengine, fnName)
   actualOutput = fn(*args)
   testPassed = (expectedOutput == actualOutput)
   passStr = '____PASS____' if testPassed else '***FAIL***'
   print '\t', passStr, '( function:', fnName, ')'
   if not testPassed:
      print '\t','___Inputs___:', args
      print '\t','___ExpOut___:', expectedOutput
      print '\t','___ActOut___:', actualOutput
      

def printpassorfail(abool):
   if abool:
      print '*** PASSED ***',
   else:
      print '___ FAILED ___',
   

print ''
print ''
print '*** Running Bitcoin engine unit tests ***'

addr = '1Ncui8YjT7JJD91tkf42dijPnqywbupf7w'  # Sam Rushing's BTC address
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

hstr = '0ffd'
bstr = '\x0f\xfd'

testFunction('int_to_hex',    hstr, i   , 2, BIGENDIAN)
testFunction('hex_to_int',    i,    hstr, BIGENDIAN)
testFunction('int_to_binary', bstr, i   , 2, BIGENDIAN)
testFunction('binary_to_int', i,    bstr, BIGENDIAN)

blockhead = '010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d0000000000009762547903d36881a86751f3f5049e23050113f779735ef82734ebf0b4450081d8c8c84db3936a1a334b035b'
blockhash   = '1195e67a7a6d0674bbd28ae096d602e1f038c8254b49dfe79d47000000000000'
blockhashBE = '000000000000479de7df494b25c838f0e102d696e08ad2bb74066d7a7ae69511'

#testFunction('hex_to_hexHash256', blockhash, blockhead)
#testFunction('hex_to_hexHash256', blockhashBE, blockhead, LE, BE)



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





# Unserialize an reserialize
#tx1raw= '\x01\x00\x00\x00\x02\x0f{\x7f\xb8mL\xf6F\x05\x8eA\xd3\xb0\x07\x18?\xdfysn\xd1\x9b*th\xab\xc5\xbd\x04\xb1n\x91\x00\x00\x00\x00\x8cI0F\x02!\x00\xb2\xee9\xd2\xfc\xc2\xe5TJW\xc3\x0f{NI\xcf\xb8""fm\x03O\xb9\x0e"4\x8e\x17\xe2\x8e\x0f\x02!\x00\xdb\x91\xc3\x19\x9c\xc7\xb4\x1dMz\xfc\xe0\xcc\xb4\xce\xb4$\xb9GmQ\xc0aBX=\xafS\xce\n\x9bf\x01A\x04\xc3"\x15\xa9\t0\x11\xbd<A(:\xce=\x00,f`w\xb2J`[<\xfc\x8fq\x01\x9a\x0fC\xdff\xf3\x89\xf3\xd9\xa6!\x88\xa4\x94\xb8i\xdc~_\x9d\xff\xc9\x8av\xd3\x08\x8a!\xe9\xb78\xec\x9e\xba\x98\xcb\xff\xff\xff\xff\x97\x00A%R\x8f{^\xd34e\xca\xaa\xe0!\xc0\xb8\x15\xf3\xe6\xa3pvA\xd5\xa0\xbc\xa4?\xc1II\x01\x00\x00\x00\x8aG0D\x02 3\xd0,.\x89o\x1a\x12RH\x8dSL\xfb\x08\xab\xf3\xe7\xea\x90\xab\xa7\xbaoW\xab\xf1\x89\xce\xf1\xd87\x02 \x05f\x8duP\x13\xb0\xe5\x9a*\xf5\x14_\x10\xef\xe6.\xa7\x16\xd33&\x8b\x0bZ>\xfb\xd8-\x149\xbe\x01A\x04\xc3"\x15\xa9\t0\x11\xbd<A(:\xce=\x00,f`w\xb2J`[<\xfc\x8fq\x01\x9a\x0fC\xdff\xf3\x89\xf3\xd9\xa6!\x88\xa4\x94\xb8i\xdc~_\x9d\xff\xc9\x8av\xd3\x08\x8a!\xe9\xb78\xec\x9e\xba\x98\xcb\xff\xff\xff\xff\x01\x00\xc2\xeb\x0b\x00\x00\x00\x00\x19v\xa9\x14\x02\xbfK(\x89\xc6\xad\xa8\x19\x0c%.p\xbd\xe1\xa1\x90\x9f\x96\x17\x88\xac\x00\x00\x00\x00'
#tx2raw= "\x01\x00\x00\x00\x030\xf3p\x1f\x9b\xc4dU/pIW\x91\x04\x08\x17\xcewz\xd5\xed\xe1nR\x9f\xcd\x0c\x0e\x94\x91V\x94\x00\x00\x00\x00\x8cI0F\x02!\x00\xf5tk\x0b%OZ7\xe7RQE\x9cz#\xb6\xdf\xcb\x86\x8a\xc7F~\xdd\x9ao\xdd\x1d\x96\x98q\xbe\x02!\x00\x88\x94\x8a\xea)\xb6\x91a\xca4\x1cI\xc0&\x86\xa8\x1d\x8c\xbbs\x94\x0f\x91\x7f\xa0\xedqThm>[\x01A\x04G\xd4\x90V\x1f9l\x8a\x9e\xfc\x14Hk\xc1\x98\x88K\xa1\x83y\xbc\xac.\x0b\xe2\xd8RQ4\xabt/0\x1a\x9a\xca6`n])\xaa#\x8a\x9e)\x93\x001PB=\xf6\x92Ecd-J\xfe\x9b\xf4\xfe(\xff\xff\xff\xffr\x14+\xf7hl\xe9,m\xe5\xb73e\xbf\xb9\xd5\x9b\xb6\x0c,\x80\x98-YX\xc1\xe6\xa3\xb0\x8e\xa6\x89\x00\x00\x00\x00JI0F\x02!\x00\xbc\xe4:\xd3\xac\xbcy\xb0$~T\xc8\xc9\x1e\xac\x1c\xf9\x03u\x05\x00\x0e\x01\xd1\xfd\x81\x18T\xd8[\xc2\x1a\x02!\x00\x99*oo/\xebob\xd3po;\x9a\xaa\xb8\x8d\x9f\x112\x95j\x1d\xff\xa9&\xcdUn\xd5S`\xdf\x01\xff\xff\xff\xff\xd2\x81(\xbb\xb6 |\x1c=\nc\x0c\xc6\x19\xdc~{\xeaV\xac\x19\xa1\xda\xb1'\xc6,x\xfa\x1bc,\x00\x00\x00\x00IH0E\x02  \x97W6\x81aSw\x08\xfd)\xd8\x9b\xb1\xe9\xd6H\x00yI\xec\xfd\xedx\x9bQ\xa9c$\xcbe\x18\x02!\x00\xcd\x0f|0!9\x16H+n\x16m\x8aO+\x98\x1fw~\xb1\x84\xcd\x8aI_\x1b=6\x90\xfb\xbf-\x01\xff\xff\xff\xff\x01\x00\xa6\xf7_\x02\x00\x00\x00\x19v\xa9\x14\x9e5\xd9<w\x92\xbd\xca\xadV\x97\xdd\xeb\xf0CS\xd9\xa5\xe1\x96\x88\xac\x00\x00\x00\x00"

tx1raw = hex_to_binary('01000000016290dce984203b6a5032e543e9e272d8bce934c7de4d15fa0fe44dd49ae4ece9010000008b48304502204f2fa458d439f957308bca264689aa175e3b7c5f78a901cb450ebd20936b2c500221008ea3883a5b80128e55c9c6070aa6264e1e0ce3d18b7cd7e85108ce3d18b7419a0141044202550a5a6d3bb81549c4a7803b1ad59cdbba4770439a4923624a8acfc7d34900beb54a24188f7f0a40689d905d4847cc7d6c8d808a457d833c2d44ef83f76bffffffff0242582c0a000000001976a914c1b4695d53b6ee57a28647ce63e45665df6762c288ac80d1f008000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00000000')
tx2raw = hex_to_binary('0100000001f658dbc28e703d86ee17c9a2d3b167a8508b082fa0745f55be5144a4369873aa010000008c49304602210041e1186ca9a41fdfe1569d5d807ca7ff6c5ffd19d2ad1be42f7f2a20cdc8f1cc0221003366b5d64fe81e53910e156914091d12646bc0d1d662b7a65ead3ebe4ab8f6c40141048d103d81ac9691cf13f3fc94e44968ef67b27f58b27372c13108552d24a6ee04785838f34624b294afee83749b64478bb8480c20b242c376e77eea2b3dc48b4bffffffff0200e1f505000000001976a9141b00a2f6899335366f04b277e19d777559c35bc888ac40aeeb02000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00000000')



tx1 = PyTx().unserialize(tx1raw)
tx2 = PyTx().unserialize(tx2raw)

tx1again = tx1.serialize()
tx2again = tx2.serialize()


print ''
print 'Testing transaction serialization round trip:'
print '\t Tx1 == PyTx().unserialize( Tx1.serialize() ) ? ', 
printpassorfail(tx1raw == tx1again)
print ''
print '\t Tx2 == PyTx().unserialize( Tx2.serialize() ) ? ', 
printpassorfail(tx2raw == tx2again)
print ''


hexBlock = (
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

blk = PyBlock().unserialize( hex_to_binary(hexBlock) )
blockReHex = binary_to_hex(blk.serialize())
print ''
print 'Testing block serialization round trip:'
print '\t theBlock == Block().unserialize( theBlock.serialize() ) ? ', 
printpassorfail(hexBlock == blockReHex)
print ''


binRoot = blk.blockData.getMerkleRoot()
print ''
print 'Testing merkle tree calculation:'
print '\tMerkleRoot in block header:', binary_to_hex(blk.blockHeader.merkleRoot)
print '\tMerkleRoot calculated:     ', binary_to_hex(binRoot)
print '\tRoot calculation verified? ', 
printpassorfail(blk.blockHeader.merkleRoot == blk.blockData.merkleRoot)
print ''
print ''


# Execute the tests with Satoshi's public key from the Bitcoin specification page
satoshiPubKeyHex = '04fc9702847840aaf195de8442ebecedf5b095cdbb9bc716bda9110971b28a49e0ead8564ff0db22209e0374782c093bb899692d524e9d6a6956e7c5ecbcd68284'
satoshiAddrStr = '1AGRxqDa5WjUKBwHB9XYEjmkv1ucoUUy1s'
addrPiece1Hex = '65a4358f4691660849d9f235eb05f11fabbd69fa'
addrPiece2Hex = 'd8b2307a'
addrPiece1Bin = hex_to_binary(addrPiece1Hex)
addrPiece2Bin = hex_to_binary(addrPiece2Hex)

print '\nTesting ECDSA key/address methods:'
print "\tSatoshi's PubKey:      ", satoshiPubKeyHex[:32], '...'
print "\tSatoshi's Address:     ", satoshiAddrStr
saddr = PyBtcAddress().createFromPublicKey( hex_to_binary(satoshiPubKeyHex) )
print ''
print '\tAddr calc from pubkey: ', saddr.calculateAddrStr()
print '\tAddress is valid:      ', checkAddrStrValid(satoshiAddrStr)


################################################################################
addr = PyBtcAddress().createNewRandomAddress()
msg = int_to_binary(39029348428)
theHash = hash256(msg)
derSig = addr.generateDERSignature(theHash)
print 'Testing ECDSA signing & verification -- arbitrary binary strings:', 
printpassorfail( addr.verifyDERSignature( theHash, derSig))
print ''


################################################################################
# From tx tests before, we have tx1 and tx2, where tx2 uses and output from tx1
sp = PyScriptProcessor()
sp.setTxObjects(tx1, tx2, 0)
print 'Testing ECDSA signing & verification -- two linked transactions: ',
printpassorfail( sp.verifyTransactionValid() )
print ''


################################################################################
# test signing a transaction:  create two addresses and a fake Tx between them

print 'Testing PyCreateAndSignTx'
AddrA = PyBtcAddress().createFromPrivateKey(hex_to_int('aa'*32))
AddrB = PyBtcAddress().createFromPrivateKey(hex_to_int('bb'*32))
print '   Address A:', AddrA.getAddrStr()
print '   Address B:', AddrB.getAddrStr()
# This TxIn will be completely ignored, so it can contain garbage
txinA = PyTxIn()
txinA.outpoint  = PyOutPoint().unserialize(hex_to_binary('00'*36))
txinA.binScript = hex_to_binary('99'*4)
txinA.sequence  = hex_to_binary('ff'*4)

txoutA = PyTxOut()
txoutA.value = 50 * (10**8)
txoutA.binScript = '\x76\xa9\x14' + AddrA.getAddr160() + '\x88\xac'

tx1 = PyTx()
tx1.version    = 1
tx1.numInputs  = 1
tx1.inputs     = [txinA]
tx1.numOutputs = 1
tx1.outputs    = [txoutA]
tx1.locktime   = 0

tx1hash = tx1.getHash()
print 'Creating transaction to send coins from A to B'
tx2 = PyCreateAndSignTx( [[ AddrA, tx1, 0 ]],  [[AddrB, 50*(10**8)]])

# This is not as easy as it sounds -- we did just create this transaction,
# but we need to make sure we can construct the string to be hashed/verified
# the same way as we signed it.  I had a few bugs in this process that took
# me like 2 days to sort out
print 'Verifying the transaction we just created',
psp = PyScriptProcessor()
psp.setTxObjects(tx1, tx2, 0)
verifResult = psp.verifyTransactionValid()
printpassorfail( verifResult)


# I made these two tx in a fake blockchain... but they should still work
tx1 = PyTx().unserialize(hex_to_binary( (
   '01000000 0163451d 1002611c 1388d5ba 4ddfdf99 196a86b5 990fb5b0 dc786207'
   '4fdcb8ee d2000000 004a4930 46022100 cb02fb5a 910e7554 85e3578e 6e9be315'
   'a161540a 73f84ee6 f5d68641 925c59ac 0221007e 530a1826 30b50e2c 12dd09cd'
   'ebfd809f 038be982 bdc2c7e9 d4cbf634 9e088d01 ffffffff 0200ca9a 3b000000'
   '001976a9 14cb2abd e8bccacc 32e893df 3a054b9e f7f227a4 ce88ac00 286bee00'
   '00000019 76a914ee 26c56fc1 d942be8d 7a24b2a1 001dd894 69398088 ac000000'
   '00'                                                                     ).replace(' ','')))

tx2 = PyTx().unserialize(hex_to_binary( (
   '01000000 01a5b837 da38b64a 6297862c ba8210d0 21ac59e1 2b7c6d7e 70c355f6'
   '972ee7a8 6e010000 008c4930 46022100 89e47100 d88d5f8c 8f62a796 dac3afb8'
   'f090c6fc 2eb0c4af ac7b7567 3a364c01 0221002b f40e554d ae51264b 0a86df17'
   '3e45756a 89bbd302 4f166cc4 2cfd1874 13636901 41046868 0737c76d abb801cb'
   '2204f57d be4e4579 e4f710cd 67dc1b42 27592c81 e9b5cf02 b5ac9e8b 4c9f49be'
   '5251056b 6a6d011e 4c37f6b6 d17ede6b 55faa235 19e2ffff ffff0100 286bee00'
   '00000019 76a914c5 22664fb0 e55cdc5c 0cea73b4 aad97ec8 34323288 ac000000'
   '00'                                                                     ).replace(' ','')))

print '\nVerify tx from fake blockchain :',
psp = PyScriptProcessor()
psp.setTxObjects(tx1, tx2, 0)
verifResult = psp.verifyTransactionValid()
printpassorfail( verifResult)


# 2-of-2 transaction
tx1 = PyTx().unserialize(hex_to_binary('010000000189a0022c8291b4328338ec95179612b8ebf72067051de019a6084fb97eae0ebe000000004a4930460221009627882154854e3de066943ba96faba02bb8b80c1670a0a30d0408caa49f03df022100b625414510a2a66ebb43fffa3f4023744695380847ee1073117ec90cb60f2c8301ffffffff0210c18d0000000000434104a701496f10db6aa8acbb6a7aa14d62f4925f8da03de7f0262010025945f6ebcc3efd55b6aa4bc6f811a0dc1bbdd2644bdd81c8a63766aa11f650cd7736bbcaf8ac001bb7000000000043526b006b7dac7ca914fc1243972b59c1726735d3c5cca40e415039dce9879a6c936b7dac7ca914375dd72e03e7b5dbb49f7e843b7bef4a2cc2ce9e879a6c936b6c6ca200000000'))
tx2 = PyTx().unserialize(hex_to_binary('01000000011c9608650a912be7fa88eecec664e6fbfa4b676708697fa99c28b3370005f32d01000000fd1701483045022017462c29efc9158cf26f2070d444bb2b087b8a0e6287a9274fa36fad30c46485022100c6d4cc6cd504f768389637df71c1ccd452e0691348d0f418130c31da8cc2a6e8014104e83c1d4079a1b36417f0544063eadbc44833a992b9667ab29b4ff252d8287687bad7581581ae385854d4e5f1fcedce7de12b1aec1cb004cabb2ec1f3de9b2e60493046022100fdc7beb27de0c3a53fbf96df7ccf9518c5fe7873eeed413ce17e4c0e8bf9c06e022100cc15103b3c2e1f49d066897fe681a12e397e87ed7ee39f1c8c4a5fef30f4c2c60141047cf315904fcc2e3e2465153d39019e0d66a8aaec1cec1178feb10d46537427239fd64b81e41651e89b89fefe6a23561d25dddc835395dd3542f83b32a1906aebffffffff01c0d8a700000000001976a914fc1243972b59c1726735d3c5cca40e415039dce988ac00000000'))

print '\nVerify 2-of-2 tx from Testnet  :',
psp = PyScriptProcessor()
psp.setTxObjects(tx1, tx2, 0)
verifResult = psp.verifyTransactionValid()
printpassorfail( verifResult)

# 2-of-3 transaction
tx1 = PyTx().unserialize(hex_to_binary('010000000371c06e0639dbe6bc35e6f948da4874ae69d9d91934ec7c5366292d0cbd5f97b0010000008a47304402200117cdd3ec6259af29acea44db354a6f57ac10d8496782033f5fe0febfd77f1b02202ceb02d60dbb43e6d4e03e5b5fbadc031f8bbb3c6c34ad307939947987f600bf01410452d63c092209529ca2c75e056e947bc95f9daffb371e601b46d24377aaa3d004ab3c6be2d6d262b34d736b95f3b0ef6876826c93c4077d619c02ebd974c7facdffffffffa65aa866aa7743ec05ba61418015fc32ecabd99886732056f1d4454c8f762bf8000000008c493046022100ea0a9b41c9372837e52898205c7bebf86b28936a3ee725672d0ca8f434f876f0022100beb7243a51fbc0997e55cb519d3b9cbd59f7aba68d80ba1e8adbb53443cda3c00141043efd1ca3cffc50638031281d227ff347a3a27bc145e2f846891d29f87bc068c27710559c4d9cd71f7e9e763d6e2753172406eb1ed1fadcaf9a8972b4270f05b4ffffffffd866d14151ee1b733a2a7273f155ecb25c18303c31b2c4de5aa6080aef2e0006000000008b483045022052210f95f6b413c74ce12cfc1b14a36cb267f9fa3919fa6e20dade1cd570439f022100b9e5b325f312904804f043d06c6ebc8e4b1c6cd272856c48ab1736b9d562e10c01410423fdddfe7e4d70d762dd6596771e035f4b43d54d28c2231be1102056f81f067914fe4fb6fd6e3381228ee5587ddd2028c846025741e963d9b1d6cf2c2dea0dbcffffffff0210ef3200000000004341048a33e9fd2de28137574cc69fe5620199abe37b7d08a51c528876fe6c5fa7fc28535f5a667244445e79fffc9df85ec3d79d77693b1f37af0e2d7c1fa2e7113a48acc0d454070000000061526b006b7dac7ca9143cd1def404e12a85ead2b4d3f5f9f817fb0d46ef879a6c936b7dac7ca9146a4e7d5f798e90e84db9244d4805459f87275943879a6c936b7dac7ca914486efdd300987a054510b4ce1148d4ad290d911e879a6c936b6c6ca200000000'))
tx2 = PyTx().unserialize(hex_to_binary('01000000012f654d4d1d7246d1a824c5b6c5177c0b5a1983864579aabb88cabd5d05e032e201000000fda0014730440220151ad44e7f78f9e0c4a3f2135c19ca3de8dbbb7c58893db096c0c5f1573d5dec02200724a78c3fa5f153103cb46816df46eb6cfac3718038607ddec344310066161e01410459fd82189b81772258a3fc723fdda900eb8193057d4a573ee5ad39e26b58b5c12c4a51b0edd01769f96ed1998221daf0df89634a7137a8fa312d5ccc95ed8925483045022100ca34834ece5925cff6c3d63e2bda6b0ce0685b18f481c32e70de9a971e85f12f0220572d0b5de0cf7b8d4e28f4914a955e301faaaa42f05feaa1cc63b45f938d75d9014104ce6242d72ee67e867e6f8ec434b95fcb1889c5b485ec3414df407e11194a7ce012eda021b68f1dd124598a9b677d6e7d7c95b1b7347f5c5a08efa628ef0204e1483045022074e01e8225e8c4f9d0b3f86908d42a61e611f406e13817d16240f94f52f49359022100f4c768dd89c6435afd3834ae2c882465ade92d7e1cc5c2c2c3d8d25c41b3ea61014104ce66c9f5068b715b62cc1622572cd98a08812d8ca01563045263c3e7af6b997e603e8e62041c4eb82dfd386a3412c34c334c34eb3c76fb0e37483fc72323f807ffffffff01b0ad5407000000001976a9146a4e7d5f798e90e84db9244d4805459f8727594388ac00000000'))

print '\nVerify 2-of-3 tx from Testnet  :',
psp = PyScriptProcessor()
psp.setTxObjects(tx1, tx2, 0)
verifResult = psp.verifyTransactionValid()
printpassorfail( verifResult)


# Check Multisig
tx1 = PyTx().unserialize(hex_to_binary('0100000001845ad165bdc0f9b5829cf5a594c4148dfd89e24756303f3a8dabeb597afa589b010000008b483045022063c233df8efa3d1885e069e375a8eabf16b23475ef21bdc9628a513ee4caceb702210090a102c7b602043e72b34a154d495ac19b3b9e42acb962c399451f2baead8f4c014104b38f79037ad25b84a564eaf53ede93dec70b35216e6682aa71a47cefa2996ec49acfbb0a8730577c62ef9a7cc20c740aaaaee75419bef9640a4216c2b49c42d3ffffffff02000c022900000000434104c08c0a71ccbe838403e3870aa1ab871b0ab3a6014b0ba41f6df2b9aefea73134ecaa0b27797620e402a33799e9047f86519d9e43bbd504cf753c293752933f4fac406f40010000000062537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953ae00000000'))
tx2 = PyTx().unserialize(hex_to_binary('0100000001bb664ff716b9dfc831bcc666c1767f362ad467fcfbaf4961de92e45547daab8701000000fd190100493046022100d73f633f114e0e0b324d87d38d34f22966a03b072803afa99c9408201f6d6dc6022100900e85be52ad2278d24e7edbb7269367f5f2d6f1bd338d017ca460008776614401473044022071fef8ac0aa6318817dbd242bf51fb5b75be312aa31ecb44a0afe7b49fcf840302204c223179a383bb6fcb80312ac66e473345065f7d9136f9662d867acf96c12a42015241048c006ff0d2cfde86455086af5a25b88c2b81858aab67f6a3132c885a2cb9ec38e700576fd46c7d72d7d22555eee3a14e2876c643cd70b1b0a77fbf46e62331ac4104b68ef7d8f24d45e1771101e269c0aacf8d3ed7ebe12b65521712bba768ef53e1e84fff3afbee360acea0d1f461c013557f71d426ac17a293c5eebf06e468253e00ffffffff0280969800000000001976a9140817482d2e97e4be877efe59f4bae108564549f188ac7015a7000000000062537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953ae00000000'))


print '\nOP_CHECKMULTISIG from Testnet  :',
psp = PyScriptProcessor()
psp.setTxObjects(tx1, tx2, 0)
verifResult = psp.verifyTransactionValid()
printpassorfail( verifResult)


print '\nTest multisig addr extraction  :',
scripts = []
scripts.append(hex_to_binary('4104b54b5fc1917945fff64785d4baaca66a9704e9ed26002f51f53763499643321fbc047683a62be16e114e25404ce6ffdcf625a928002403402bf9f01e5cbd5f3dad4104f576e534f9bbf6d7c5f186ff4c6e0c5442c2755314bdee62fbc656f94d6cbf32c5eb3522da21cf9f954133000ffccb20dbfec030737640cc3315ce09619210d0ac'))
scripts.append(hex_to_binary('537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953ae'))
scripts.append(hex_to_binary('527a7651a269527a829178a914731cdb75c88a01cbb96729888f726b3b9f29277a879b69527a829178a914e9b4261c6122f8957683636548923acc069e8141879b6952ae'))

for scr in scripts:
   addrList = multiSigExtractAddr160List(scr)
   print '\nNum addresses:   ', len(addrList), '\n   ',
   for a in addrList:
      print  PyBtcAddress().createFromPublicKeyHash160(a).getAddrStr(),

