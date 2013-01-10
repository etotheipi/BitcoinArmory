################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
from armoryengine import *
import CppBlockUtils as Cpp
import armoryengine 

LE = LITTLEENDIAN
BE = BIGENDIAN


Test_BasicUtils       = True
Test_PyBlockUtils     = False
Test_CppBlockUtils    = False
Test_SimpleAddress    = False
Test_MultiSigTx       = False
Test_TxSimpleCreate   = False
Test_EncryptedAddress = False
Test_EncryptedWallet  = False
Test_TxDistProposals  = False
Test_SelectCoins      = False
Test_CryptoTiming     = False
Test_PyBkgdThread     = False

Test_NetworkObjects   = False
Test_ReactorLoop      = False
Test_SettingsFile     = False
Test_WalletMigrate    = False
Test_AddressBooks     = False
Test_URIParse         = False

Test_BkgdThread       = False
Test_AsyncBDM         = False
Test_Timers           = False

'''
import optparse
parser = optparse.OptionParser(usage="%prog [options]\n"+
                               "Connects to a running bitcoin node and "+
                               "prints all or part of the best-block-chain.")
parser.add_option("--testnet", dest="testnet", action="store_true", default=False,
                  help="Speak testnet protocol")

(options, args) = parser.parse_args()
'''  



def testFunction( fnName, expectedOutput, *args, **kwargs):
   """
   Provide a function name, inputs and some known outputs
   Prints a pass/fail string if the outputs match
   """
   fn = getattr(armoryengine, fnName)
   actualOutput = fn(*args,**kwargs)
   testPassed = (expectedOutput == actualOutput)
   passStr = '____PASS____' if testPassed else '***FAIL***'
   print '\t', passStr, '( function:', fnName, ')'
   if not testPassed:
      print '\t','___Inputs___:', args
      print '\t','___ExpOut___:', expectedOutput
      print '\t','___ActOut___:', actualOutput
         
   
def printpassorfail(abool):
   """
   Print a simple, formatted pass/fail string  
   """
   w = 60
   if abool:
      print '\n' + ' '*w + '*** PASSED ***',
   else:
      print '\n' + ' '*w + '___ FAILED ___',





################################################################################
################################################################################
if Test_BasicUtils:
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

   #h   = '00000123456789abcdef000000'
   #ans = 'aaaaabcdeghjknrsuwxyaaaaaa'
   #testFunction('binary_to_typingBase16', ans, h  )
   #testFunction('typingBase16_to_binary', h,   ans)
   
   blockhead = '010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d0000000000009762547903d36881a86751f3f5049e23050113f779735ef82734ebf0b4450081d8c8c84db3936a1a334b035b'
   blockhash   = '1195e67a7a6d0674bbd28ae096d602e1f038c8254b49dfe79d47000000000000'
   blockhashBE = '000000000000479de7df494b25c838f0e102d696e08ad2bb74066d7a7ae69511'
   
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


   data   = hex_to_binary('11' + 'aa'*31)
   dataBE = hex_to_binary('11' + 'aa'*31, endIn=LITTLEENDIAN, endOut=BIGENDIAN)
   dataE1 = hex_to_binary('11' + 'aa'*30 + 'ab')
   dataE2 = hex_to_binary('11' + 'aa'*29 + 'abab')
   dchk = hash256(data)[:4]
   testFunction('verifyChecksum', data, data, dchk)
   testFunction('verifyChecksum', data, dataBE, dchk, beQuiet=True)
   testFunction('verifyChecksum', '',   dataE1, dchk, hash256, False, True)  # don't fix
   testFunction('verifyChecksum', data, dataE1, dchk, hash256,  True, True)  # try fix
   testFunction('verifyChecksum', '',   dataE2, dchk, hash256, False, True)  # don't fix
   testFunction('verifyChecksum', '',   dataE2, dchk, hash256,  True, True)  # try fix


   verTuple = (0,50,0,0)
   verInt   = 5000000
   verStr   = '0.50'
   testFunction('getVersionString',   verStr, verTuple)
   testFunction('getVersionInt',      verInt, verTuple)
   testFunction('readVersionString',  verTuple, verStr)
   testFunction('readVersionInt',     verTuple, verInt)

   verTuple = (1,0,12,0)
   verInt   =  10012000
   verStr   = '1.00.12'
   testFunction('getVersionString',   verStr, verTuple)
   testFunction('getVersionInt',      verInt, verTuple)
   testFunction('readVersionString',  verTuple, verStr)
   testFunction('readVersionInt',     verTuple, verInt)

   verTuple = (0,20,0,108)
   verInt   =  2000108
   verStr   = '0.20.0.108'
   testFunction('getVersionString',   verStr, verTuple)
   testFunction('getVersionInt',      verInt, verTuple)
   testFunction('readVersionString',  verTuple, verStr)
   testFunction('readVersionInt',     verTuple, verInt)

   miniKey  = 'S4b3N3oGqDqR5jNuxEvDwf'
   miniPriv = hex_to_binary('0c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe471be89827e19d72aa1d')
   testFunction('decodeMiniPrivateKey', miniPriv, miniKey)

   print 'Testing coin2str method'
   def printC2S(c):
      print str(c).rjust(16),
      print coin2str(c).rjust(16),
      print coin2str(c,4).rjust(16),
      print coin2str(c,2).rjust(16),
      print coin2str(c,0).rjust(16),
      print coin2str(c,8, maxZeros=6).rjust(16),
      print coin2str(c,8, maxZeros=2).rjust(16),
      print coin2str(c,6, maxZeros=4).rjust(16),
      print coin2str(c,6, maxZeros=4, rJust=False),
      print coin2str_approx(c,3)
   printC2S(0)
   printC2S(1)
   printC2S(100)
   printC2S(10000)
   printC2S(10111)
   printC2S(10000000)
   printC2S(100000000)
   printC2S(1241110000)
   printC2S(10000099080)
   printC2S(10000099000)
   printC2S(10000909001)
   printC2S(12345678900)
   printC2S(98753178900)
   printC2S(-1)
   printC2S(-100)
   printC2S(-10000)
   printC2S(-10000000)
   printC2S(-10000090000)
   printC2S(-10000990000)
   printC2S(-10009090001)
   printC2S(-10001090000)
   printC2S(100000001090000)
   

   print ''
   print 'Testing str2coin method'
   def printS2C(s):
      print ('"'+s+'"').ljust(18) , str2coin(s)
          
   printS2C('0.00000000')
   printS2C('0.0000')
   printS2C('0.0')
   printS2C('-0')
   printS2C('0.00000001')
   printS2C('0.0001')
   printS2C('.0001')
   printS2C('-.0001')
   printS2C('-0.2')
   printS2C('-1')
   printS2C('-1.0  ')
   printS2C(' -1.0  ')
   printS2C('-1.')
   printS2C('10000000')
   printS2C('100000.00000001')


# Unserialize an reserialize
tx1raw = hex_to_binary( \
   '01000000016290dce984203b6a5032e543e9e272d8bce934c7de4d15fa0fe44d'
   'd49ae4ece9010000008b48304502204f2fa458d439f957308bca264689aa175e'
   '3b7c5f78a901cb450ebd20936b2c500221008ea3883a5b80128e55c9c6070aa6'
   '264e1e0ce3d18b7cd7e85108ce3d18b7419a0141044202550a5a6d3bb81549c4'
   'a7803b1ad59cdbba4770439a4923624a8acfc7d34900beb54a24188f7f0a4068'
   '9d905d4847cc7d6c8d808a457d833c2d44ef83f76bffffffff0242582c0a0000'
   '00001976a914c1b4695d53b6ee57a28647ce63e45665df6762c288ac80d1f008'
   '000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00000000')
tx2raw = hex_to_binary( \
   '0100000001f658dbc28e703d86ee17c9a2d3b167a8508b082fa0745f55be5144'
   'a4369873aa010000008c49304602210041e1186ca9a41fdfe1569d5d807ca7ff'
   '6c5ffd19d2ad1be42f7f2a20cdc8f1cc0221003366b5d64fe81e53910e156914'
   '091d12646bc0d1d662b7a65ead3ebe4ab8f6c40141048d103d81ac9691cf13f3'
   'fc94e44968ef67b27f58b27372c13108552d24a6ee04785838f34624b294afee'
   '83749b64478bb8480c20b242c376e77eea2b3dc48b4bffffffff0200e1f50500'
   '0000001976a9141b00a2f6899335366f04b277e19d777559c35bc888ac40aeeb'
   '02000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00000000')

tx1 = PyTx().unserialize(tx1raw)
tx2 = PyTx().unserialize(tx2raw)
   
tx1again = tx1.serialize()
tx2again = tx2.serialize()
   
   
################################################################################
################################################################################
if Test_PyBlockUtils:

   print ''
   print 'Testing transaction serialization round trip:'
   print '\t Tx1 == PyTx().unserialize( Tx1.serialize() ) ? ', 
   printpassorfail(tx1raw == tx1again)
   print ''
   print '\t Tx2 == PyTx().unserialize( Tx2.serialize() ) ? ', 
   printpassorfail(tx2raw == tx2again)
   print ''
   
   # Here's a full block, which we should be able to parse and process
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
   

################################################################################
################################################################################
if Test_CppBlockUtils:

   print '\n\nLoading Blockchain from:', BLK0001_PATH
   BDM_LoadBlockchainFile(BLK0001_PATH)
   print 'Done!'


   print '\n\nCurrent Top Block is:', TheBDM.getTopBlockHeader().getBlockHeight()
   TheBDM.getTopBlockHeader().pprint()


   #print '\n\nChecking integrity of blockchain:'
   #result = TheBDM.verifyBlkFileIntegrity()
   #print 'Done!',
   #if result==True:
      #print 'No errors detected in the blk0001.dat file'
   #else:
      #print 'Integrity check failed!  Something is wrong with your blk0001.dat file.'

   cppWlt = Cpp.BtcWallet()

   if not USE_TESTNET:
      cppWlt.addAddress_1_(hex_to_binary("604875c897a079f4db88e5d71145be2093cae194"))
      cppWlt.addAddress_1_(hex_to_binary("8996182392d6f05e732410de4fc3fa273bac7ee6"))
      cppWlt.addAddress_1_(hex_to_binary("b5e2331304bc6c541ffe81a66ab664159979125b"))
      cppWlt.addAddress_1_(hex_to_binary("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"))
      cppWlt.addAddress_1_(hex_to_binary("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"))
   else:
      # Test-network addresses
      cppWlt.addAddress_1_(hex_to_binary("5aa2b7e93537198ef969ad5fb63bea5e098ab0cc"))
      cppWlt.addAddress_1_(hex_to_binary("28b2eb2dc53cd15ab3dc6abf6c8ea3978523f948"))
      cppWlt.addAddress_1_(hex_to_binary("720fbde315f371f62c158b7353b3629e7fb071a8"))
      cppWlt.addAddress_1_(hex_to_binary("0cc51a562976a075b984c7215968d41af43be98f"))
      cppWlt.addAddress_1_(hex_to_binary("57ac7bfb77b1f678043ac6ea0fa67b4686c271e5"))
      cppWlt.addAddress_1_(hex_to_binary("b11bdcd6371e5b567b439cd95d928e869d1f546a"))
      cppWlt.addAddress_1_(hex_to_binary("2bb0974f6d43e3baa03d82610aac2b6ed017967d"))
      cppWlt.addAddress_1_(hex_to_binary("61d62799e52bc8ee514976a19d67478f25df2bb1"))

   # We do the scan three times to make sure that there are no problems
   # with rescanning the same tx's multiple times (it's bound to happen 
   # so might as well make sure it's robust)
   TheBDM.scanBlockchainForTx(cppWlt)
   TheBDM.scanBlockchainForTx(cppWlt)
   TheBDM.scanBlockchainForTx(cppWlt)

   nAddr = cppWlt.getNumAddr()
   print 'Address Balances:'
   for i in range(nAddr):
      cppAddr = cppWlt.getAddrByIndex(i)
      bal = cppAddr.getBalance()
      print '   %s %s' % (hash160_to_addrStr(cppAddr.getAddrStr20())[:12], coin2str(bal))

   leVect = cppWlt.getTxLedger()
   print '\n\nLedger for all Addr:'
   for le in leVect:
      pprintLedgerEntry(le, ' '*3)
   


   #TestNonStd
   # Not sure what happened to this test...
   #bdm.findAllNonStdTx();


################################################################################
################################################################################
if Test_SimpleAddress:
   
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
################################################################################
if Test_NetworkObjects:
   print '\n'
   print '*********************************************************************'
   print 'Testing networking object ser/unser tests'
   print '*********************************************************************'
   print ''
   
   print 'Testing standard IPv4 address conversions'
   addrQuad = (192, 168, 1, 125)
   print addrQuad, '-->', quad_to_str(addrQuad)
   addrBin = quad_to_binary( addrQuad)
   print addrQuad, '-->', binary_to_hex(addrBin)
   print binary_to_hex(addrBin), '-->', binary_to_quad(addrBin)
   addrStr = '192.168.1.125'
   print addrStr, '-->',  str_to_quad(addrStr)


   netAddrHex = ('f9beb4d9 61646472 00000000 00000000'
                 '1f000000 689dcea8 01d6c7db 4e010000'
                 '00000000 00000000 00000000 000000ff'
                 'ff0233b6 ec208d'                    ).replace(' ','')

   invHex     = ('f9beb4d9 696e7600 00000000 00000000'
                 '25000000 fef89552 01010000 0021eca1'
                 '50d3f7cd 5eca5ada 7ad02f8f 3bf38420'
                 '0cb53e8d d51b153d e92bac7a 1b'      ).replace(' ','')

   getDataHex = ('f9beb4d9 67657464 61746100 00000000'
                 '25000000 f51e33f8 01010000 0018c643'
                 '1b6200ec 361a9e80 31c174ad 5e4fc5f9'
                 '26b2f2df d3acdb62 7cbf87b8 20'      ).replace(' ','')

   msgtxHex   = ( 
     'f9beb4d9 74780000 00000000 00000000 02010000 18c6431b 01000000 01bc9ea8'
     '21256fb0 eb081274 bc7afdde 6d5a4b63 6c55cfbe 2befa8f0 0a1c79e5 fc000000'
     '008b4830 45022009 4e0a68c5 5d515b23 310cc0e2 227bbfb8 cd775bb7 f9bedff1'
     '01ba06a0 637bee02 2100f81a 11389610 ab92d592 de1cc283 5f0804a0 49baae8b'
     'd20b4aeb e29cbb82 6aba0141 04fc5c28 d283c217 a857ae2a bfebcf11 33dec9d5'
     'd51bb918 c5d75326 2b3cc90a 48504bde 41993614 be6ea62e e531ce4a 4723b550'
     'b3e50492 f320c65d 10d021a2 45ffffff ff02002f 5f1c0000 00001976 a914835b'
     '78efa362 ad78474c 14c2043b 35adc697 706a88ac 807f3d36 00000000 1976a914'
     '188f9581 3b59ca6b 8e9eadc6 9fecd33e c48d65de 88ac0000 0000'
                ).replace(' ','')


   msgVerHex  = (
     'f9beb4d9 76657273 696f6e00 00000000 55000000 409c0000 01000000 00000000'
     'ff4edc4e 00000000 01000000 00000000 00000000 00000000 0000ffff 7f000001'
     '208d0100 00000000 00000000 00000000 00000000 ffff7f00 0001d447 61d0a76a'
     '8ad8e4c7 00ffffff ff' ).replace(' ','')

   
   msgVerack  = ('f9beb4d9 76657261 636b0000 00000000 00000000').replace(' ','')


   msgblk = ''
   if os.path.exists('msgblock.bin'):
      with open('msgblock.bin') as f:
         msgblk = f.read()

   msgTest = PyMessage().unserialize(hex_to_binary(msgVerHex))
   msgTest.pprint()
   ser = msgTest.serialize()
   msgTest = PyMessage().unserialize(ser)
   msgTest.pprint()
   printpassorfail(ser==msgTest.serialize())
               
   msgTest = PyMessage().unserialize(hex_to_binary(msgVerack))
   msgTest.pprint()
   ser = msgTest.serialize()
   msgTest = PyMessage().unserialize(ser)
   msgTest.pprint()
   printpassorfail(ser==msgTest.serialize())

   msgTest = PyMessage().unserialize(hex_to_binary(netAddrHex))
   msgTest.pprint()
   ser = msgTest.serialize()
   msgTest = PyMessage().unserialize(ser)
   msgTest.pprint()
   printpassorfail(ser==msgTest.serialize())


   msgTest = PyMessage().unserialize(hex_to_binary(invHex))
   msgTest.pprint()
   ser = msgTest.serialize()
   msgTest = PyMessage().unserialize(ser)
   msgTest.pprint()
   printpassorfail(ser==msgTest.serialize())


   msgTest = PyMessage().unserialize(hex_to_binary(getDataHex))
   msgTest.pprint()
   ser = msgTest.serialize()
   msgTest = PyMessage().unserialize(ser)
   msgTest.pprint()
   printpassorfail(ser==msgTest.serialize())


   msgTest = PyMessage().unserialize(hex_to_binary(msgtxHex))
   msgTest.pprint()
   ser = msgTest.serialize()
   msgTest = PyMessage().unserialize(ser)
   msgTest.pprint()
   printpassorfail(ser==msgTest.serialize())


   # 36 kB of data on the screen is unnecessary under most circumstances... 
   print '\n\nTesting blk data reading:'
   msgTest = PyMessage().unserialize(msgblk)
   #msgTest.pprint()
   msgTest.payload.header.pprint(nIndent=1)
   print '      NumTx:     ', len(msgTest.payload.txList)
   print '      ...\n'
   ser = msgTest.serialize()
   msgTest = PyMessage().unserialize(ser)
   msgTest.payload.header.pprint(nIndent=1)
   print '      NumTx:     ', len(msgTest.payload.txList)
   print '      ...\n'
   #msgTest.pprint()
   printpassorfail(ser==msgTest.serialize())


   if Test_ReactorLoop:
      ################################################################################
      # Now test the networking:  must have Satoshi client open
      print '\n\n'
      print 'Running python-twisted networking/reactor tests'
      print 'If this test works, it will connect to the localhost'
      print 'Bitcoin client, display all incoming messages, and'
      print 'request new transactions that we see from inv messages.'
      print 'You will have to manually stop this test with ctrl-C'
      from twisted.internet.protocol import Protocol, ClientFactory
      from twisted.internet.defer import Deferred
      from twisted.internet import reactor
   
      # Load blockchain so that we can test ALL the code
      BDM_LoadBlockchainFile()
      btcNetFactory = None
   
      def restartConnection(protoObj, failReason):
         print '!Trying to restart connection'
         from twisted.internet import reactor
         reactor.connectTCP(protoObj.peer[0], protoObj.peer[1], btcNetFactory)
   
      # On handshake complete, do nothing special, but we do want to tell it to
      # restart the connection
      btcNetFactory = ArmoryClientFactory( \
                                    def_handshake=None, \
                                    func_loseConnect=restartConnection)
   
      from twisted.internet import reactor
      reactor.connectTCP('127.0.0.1', BITCOIN_PORT, btcNetFactory)
      reactor.run()


################################################################################
################################################################################
if Test_TxSimpleCreate:
   
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
   txoutA.value = 50 * ONE_BTC
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

################################################################################
################################################################################
if Test_MultiSigTx:
   print '\n'
   print '*********************************************************************'
   print 'Testing Multi-signature transaction verification'
   print '*********************************************************************'
   print ''
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
      mstype, addrList, pubList = getTxOutMultiSigInfo(scr)
      print '\nNum addresses:   ', len(addrList), '\n   ',
      for a in addrList:
         print  PyBtcAddress().createFromPublicKeyHash160(a).getAddrStr(),



   # TODO:  Add some tests for the OP_CHECKMULTISIG support in TxDP





################################################################################
################################################################################
if Test_NetworkObjects:
   print '\n'
   print '*********************************************************************'
   print 'Testing secure address/wallet features'
   print '*********************************************************************'
   print ''
   
   netAddrHex = ('f9beb4d9 61646472 00000000 00000000'
                 '1f000000 689dcea8 01d6c7db 4e010000'
                 '00000000 00000000 00000000 000000ff'
                 'ff0233b6 ec208d'                    ).replace(' ','')

   invHex     = ('f9beb4d9 696e7600 00000000 00000000'
                 '25000000 fef89552 01010000 0021eca1'
                 '50d3f7cd 5eca5ada 7ad02f8f 3bf38420'
                 '0cb53e8d d51b153d e92bac7a 1b'      ).replace(' ','')

   


################################################################################
################################################################################
if Test_EncryptedAddress:
   print '\n'
   print '*********************************************************************'
   print 'Testing secure address/wallet features'
   print '*********************************************************************'
   print ''

   # Enable this flag to get a TON of debugging output!
   debugPrint = False

   # Create an address to use for all subsequent tests
   privKey = SecureBinaryData(hex_to_binary('aa'*32))
   privChk = privKey.getHash256()[:4]
   pubKey  = CryptoECDSA().ComputePublicKey(privKey)
   addr20  = pubKey.getHash160()

   # We pretend that we plugged some passphrases through a KDF
   fakeKdfOutput1 = SecureBinaryData( hex_to_binary('11'*32) )
   fakeKdfOutput2 = SecureBinaryData( hex_to_binary('22'*32) )

   # Test serializing an empty address object:  we'll be using this
   # in other methods to determine the length of an address, which
   # will be the same for all PyBtcAddress objects, empty or not
   print '\nTest serializing empty address'
   serializedAddr = PyBtcAddress().serialize()
   print 'PyBtcAddress serializations are', len(serializedAddr), 'bytes'
   printpassorfail(True) # if we didn't crash, we win!

   #############################################################################
   # Try to create addresses without crashing
   print '\n\nTesting PyBtcAddress with plaintext private key (try not to crash)'
   testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20)
   testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, chksum=privChk)
   testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
   testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey, skipCheck=True)
   testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, skipPubCompute=True)
   if debugPrint: testAddr.pprint(indent=' '*3)


   testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
   print '\nTest serializing unencrypted wallet',
   serializedAddr = testAddr.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   theIV = SecureBinaryData(hex_to_binary('77'*16))
   # Now try locking and unlock addresses
   print '\nTesting address locking'
   testAddr.enableKeyEncryption(theIV)
   testAddr.lock(fakeKdfOutput1)
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\nTest serializing locked address',
   serializedAddr = testAddr.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   print '\nTesting address unlocking'
   testAddr.unlock(fakeKdfOutput1)
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\nTest serializing encrypted-but-unlocked address',
   serializedAddr = testAddr.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   #############################################################################
   print '\n\nTest changing passphrases'
   print '  OP(None --> Key1)'
   testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
   testAddr.enableKeyEncryption(theIV)
   testAddr.changeEncryptionKey(None, fakeKdfOutput1)
   if debugPrint: testAddr.pprint(indent=' '*3)

   # Save off this data for a later test
   addr20_1      = testAddr.getAddr160()
   encryptedKey1 = testAddr.binPrivKey32_Encr
   encryptionIV1 = testAddr.binInitVect16
   plainPubKey1  = testAddr.binPublicKey65

   print '\n  OP(Key1 --> Unencrypted)'
   testAddr.changeEncryptionKey(fakeKdfOutput1, None)
   if debugPrint: testAddr.pprint(indent=' '*3)
      
   print '\n  OP(Unencrypted --> Key2)'
   if not testAddr.isKeyEncryptionEnabled():
      testAddr.enableKeyEncryption(theIV)
   testAddr.changeEncryptionKey(None, fakeKdfOutput2)
   if debugPrint: testAddr.pprint(indent=' '*3)

   # Save off this data for a later test
   addr20_2      = testAddr.getAddr160()
   encryptedKey2 = testAddr.binPrivKey32_Encr
   encryptionIV2 = testAddr.binInitVect16
   plainPubKey2  = testAddr.binPublicKey65

   print '\n  OP(Key2 --> Key1)'
   testAddr.changeEncryptionKey(fakeKdfOutput2, fakeKdfOutput1)
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\n  OP(Key1 --> Lock --> Key2)'
   testAddr.lock(fakeKdfOutput1)
   testAddr.changeEncryptionKey(fakeKdfOutput1, fakeKdfOutput2)
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\n  OP(Key2 --> Lock --> Unencrypted)'
   testAddr.changeEncryptionKey(fakeKdfOutput2, None)
   if debugPrint: testAddr.pprint(indent=' '*3)
   
   print '\nEncryption Key Tests: '
   printpassorfail(testAddr.serializePlainPrivateKey() == privKey.toBinStr())
                    

   #############################################################################
   # TODO:  Gotta test pre-encrypted key handling
   print '\n\nTest loading pre-encrypted key data'
   testAddr = PyBtcAddress().createFromEncryptedKeyData(addr20_1, \
                                                        encryptedKey1, \
                                                        encryptionIV1)
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\n  OP(EncrAddr --> Unlock1)'
   testAddr.unlock(fakeKdfOutput1)
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\n  OP(Unlock1 --> Lock1)'
   testAddr.lock()
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\n  OP(Lock1 --> Lock2)'
   testAddr.changeEncryptionKey(fakeKdfOutput1, fakeKdfOutput2)
   if debugPrint: testAddr.pprint(indent=' '*3)

   print '\nTest serializing locked wallet from pre-encrypted data',
   serializedAddr = testAddr.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   #############################################################################
   # Now testing chained-key (deterministic) address generation
   print '\n\nTest chained priv key generation'
   print 'Starting with plain key data'
   chaincode = SecureBinaryData(hex_to_binary('ee'*32))
   addr0 = PyBtcAddress().createFromPlainKeyData(privKey, addr20)
   addr0.markAsRootAddr(chaincode)
   pub0  = addr0.binPublicKey65
   if debugPrint: addr0.pprint(indent=' '*3)

   print '\nTest serializing address-chain-root',
   serializedAddr = addr0.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   print '\nGenerate chained PRIVATE key address'
   print '  OP(addr[0] --> addr[1])'
   addr1 = addr0.extendAddressChain()
   if debugPrint: addr1.pprint(indent=' '*3)

   print '\n  OP(addr[0] --> addr[1]) [again]'
   addr1a = addr0.extendAddressChain()
   if debugPrint: addr1a.pprint(indent=' '*3)

   print '\n  OP(addr[1] --> addr[2])'
   addr2 = addr1.extendAddressChain()
   pub2 = addr2.binPublicKey65.copy()
   priv2 = addr2.binPrivKey32_Plain.copy()
   if debugPrint: addr2.pprint(indent=' '*3)

   print '\nAddr1.privKey == Addr1a.privKey:',
   printpassorfail(addr1.binPublicKey65 == addr1a.binPublicKey65)

   print '\nTest serializing priv-key-chained',
   serializedAddr = addr2.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)
   
   #############################################################################
   print '\n\nGenerate chained PUBLIC key address'
   print '    addr[0]'
   addr0 = PyBtcAddress().createFromPublicKeyData(pub0)
   addr0.markAsRootAddr(chaincode)
   if debugPrint: addr0.pprint(indent=' '*3)

   print '\nTest serializing pub-key-only-root',
   serializedAddr = addr0.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   print '\n  OP(addr[0] --> addr[1])'
   addr1 = addr0.extendAddressChain()
   if debugPrint: addr1.pprint(indent=' '*3)

   print '\n  OP(addr[1] --> addr[2])'
   addr2 = addr1.extendAddressChain()
   pub2a = addr2.binPublicKey65.copy()
   if debugPrint: addr2.pprint(indent=' '*3)

   print '\nAddr2.PublicKey == Addr2a.PublicKey:',
   printpassorfail(pub2 == pub2a)

   print '\nTest serializing pub-key-from-chain',
   serializedAddr = addr2.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   #############################################################################
   print '\n\nGenerate chained keys from locked addresses'
   addr0 = PyBtcAddress().createFromPlainKeyData( privKey, \
                                             willBeEncr=True, IV16=theIV)
   addr0.markAsRootAddr(chaincode)
   print '\n  OP(addr[0] plain)'
   if debugPrint: addr0.pprint(indent=' '*3)

   print '\nTest serializing unlocked addr-chain-root',
   serializedAddr = addr0.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   print '\n  OP(addr[0] locked)'
   addr0.lock(fakeKdfOutput1)
   if debugPrint: addr0.pprint(indent=' '*3)

   print '\n  OP(addr[0] w/Key --> addr[1])'
   addr1 = addr0.extendAddressChain(fakeKdfOutput1, newIV=theIV)
   if debugPrint: addr1.pprint(indent=' '*3)

   print '\n  OP(addr[1] w/Key --> addr[2])'
   addr2 = addr1.extendAddressChain(fakeKdfOutput1, newIV=theIV)
   addr2.unlock(fakeKdfOutput1)
   priv2a = addr2.binPrivKey32_Plain.copy()
   addr2.lock()
   if debugPrint: addr2.pprint(indent=' '*3)

   print '\nAddr2.priv == Addr2a.priv:',
   printpassorfail(priv2 == priv2a)

   print '\nTest serializing chained address from locked root',
   serializedAddr = addr2.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)


   #############################################################################
   print '\n\nGenerate chained keys from locked addresses, no unlocking'
   addr0 = PyBtcAddress().createFromPlainKeyData( privKey, \
                                          willBeEncr=True, IV16=theIV)
   addr0.markAsRootAddr(chaincode)
   print '\n  OP(addr[0] locked)'
   addr0.lock(fakeKdfOutput1)
   if debugPrint: addr0.pprint(indent=' '*3)

   print '\n  OP(addr[0] locked --> addr[1] locked)'
   addr1 = addr0.extendAddressChain(newIV=theIV)
   if debugPrint: addr1.pprint(indent=' '*3)

   print '\n  OP(addr[1] locked --> addr[2] locked)'
   addr2 = addr1.extendAddressChain(newIV=theIV)
   pub2b = addr2.binPublicKey65.copy()
   if debugPrint: addr2.pprint(indent=' '*3)

   print '\nAddr2.Pub == Addr2b.pub:',
   printpassorfail(pub2 == pub2b)

   print '\nTest serializing priv-key-bearing address marked for unlock',
   serializedAddr = addr2.serialize()
   retestAddr = PyBtcAddress().unserialize(serializedAddr)
   serializedRetest = retestAddr.serialize()
   printpassorfail(serializedAddr == serializedRetest)

   addr2.unlock(fakeKdfOutput1)
   priv2b = addr2.binPrivKey32_Plain.copy()
   print '\n  OP(addr[2] locked --> unlocked)'
   if debugPrint: addr2.pprint(indent=' '*3)


   addr2.lock()
   print '\n  OP(addr[2] unlocked --> locked)'
   if debugPrint: addr2.pprint(indent=' '*3)
   
   
   print '\nAddr2.priv == Addr2b.priv:',
   printpassorfail(priv2 == priv2b)


################################################################################
################################################################################
if Test_EncryptedWallet:
   print '\n'
   print '*********************************************************************'
   print 'Testing deterministic, encrypted wallet features'
   print '*********************************************************************'
   print ''

   debugPrint = True
   debugPrintAlot = False

   # Remove wallet files, need fresh dir for this test
   
   shortlabel = 'TestWallet1'
   wltID = '6Q168oJ7'
   if USE_TESTNET:
      wltID = '3VB8XSoY'
      
   fileA    = os.path.join(ARMORY_HOME_DIR, 'armory_%s_.wallet' % wltID)
   fileB    = os.path.join(ARMORY_HOME_DIR, 'armory_%s_backup.wallet' % wltID)
   fileAupd = os.path.join(ARMORY_HOME_DIR, 'armory_%s_backup_unsuccessful.wallet' % wltID)
   fileBupd = os.path.join(ARMORY_HOME_DIR, 'armory_%s_update_unsuccessful.wallet' % wltID)

   for f in (fileA, fileB, fileAupd, fileBupd):
      print 'Removing file:', f, 
      if os.path.exists(f):
         os.remove(f)
         print '...removed!'
      else:
         print '(DNE, do nothing)'
   
   # We need a controlled test, so we script the all the normally-random stuff
   privKey   = SecureBinaryData('\xaa'*32)
   privKey2  = SecureBinaryData('\x33'*32)
   chainstr  = SecureBinaryData('\xee'*32)
   theIV     = SecureBinaryData(hex_to_binary('77'*16))
   passphrase  = SecureBinaryData('A passphrase')
   passphrase2 = SecureBinaryData('A new passphrase')
      
   wlt = PyBtcWallet().createNewWallet(withEncrypt=False, \
                                       plainRootKey=privKey, \
                                       chaincode=chainstr,   \
                                       IV=theIV, \
                                       shortLabel=shortlabel)
   wlt.addrPoolSize = 5
   wlt.detectHighestUsedIndex(True)

   print 'New wallet is at:', wlt.getWalletPath()
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)



   #############################################################################
   print '\n(1) Getting a new address:'
   newAddr = wlt.getNextUnusedAddress()
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(1) Re-reading wallet from file, compare the two wallets'
   wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   printpassorfail(wlt.isEqualTo(wlt2, debug=debugPrintAlot))
   
   #############################################################################
   print '\n(2)Testing unencrypted wallet import-address'
   wlt.importExternalAddressData(privKey=privKey2)
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)
   
   print '\n(2) Re-reading wallet from file, compare the two wallets'
   wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   printpassorfail(wlt.isEqualTo(wlt2, debug=debugPrintAlot))

   print '\n(2a)Testing deleteImportedAddress'
   print '\nWallet size before delete:',  os.path.getsize(wlt.walletPath)
   print '\n#Addresses before delete:', len(wlt.linearAddr160List)
   toDelete160 = convertKeyDataToAddress(privKey2)
   wlt.deleteImportedAddress(toDelete160)
   print '\nWallet size after delete:',  os.path.getsize(wlt.walletPath)
   print '\n(2a) #Addresses after delete:', len(wlt.linearAddr160List)
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(2a) Reimporting address for remaining tests'
   print '\nWallet size before reimport:',  os.path.getsize(wlt.walletPath)
   wlt.importExternalAddressData(privKey=privKey2)
   print '\nWallet size after  reimport:',  os.path.getsize(wlt.walletPath)
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)


   print '\n(2b)Testing ENCRYPTED wallet import-address'
   privKey3  = SecureBinaryData('\xbb'*32)
   privKey4  = SecureBinaryData('\x44'*32)
   chainstr2  = SecureBinaryData('\xdd'*32)
   theIV2     = SecureBinaryData(hex_to_binary('66'*16))
   passphrase2= SecureBinaryData('hello')
   wltE = PyBtcWallet().createNewWallet(withEncrypt=True, \
                                       plainRootKey=privKey3, \
                                       securePassphrase=passphrase2, \
                                       chaincode=chainstr2,   \
                                       IV=theIV2, \
                                       shortLabel=shortlabel)

   try:
      wltE.importExternalAddressData(privKey=privKey2)
      wltE.pprint(indent=' '*5, allAddrInfo=debugPrint)
      printpassorfail(False)
      print 'FAILED!  We should have thrown an error about importing into a '
      print '         locked wallet...'
   except:
      printpassorfail(True)


   wltE.unlock(securePassphrase=passphrase2)
   wltE.importExternalAddressData(privKey=privKey2)
   wltE.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(2b) Re-reading wallet from file, compare the two wallets'
   wlt2 = PyBtcWallet().readWalletFile(wltE.walletPath)
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   printpassorfail(wltE.isEqualTo(wlt2, debug=debugPrintAlot))
   

   print '\n(2b) Unlocking wlt2 after re-reading locked-import-wallet'
   wlt2.unlock(securePassphrase=passphrase2)



   #############################################################################
   # Now play with encrypted wallets
   print '\n\n'
   print '*********************************************************************'
   print '\n(3)Testing conversion to encrypted wallet'

   kdfParams = wlt.computeSystemSpecificKdfParams(0.1)
   wlt.changeKdfParams(*kdfParams)

   print '\n(3)New KDF takes', wlt.testKdfComputeTime(), 'seconds to compute'
   wlt.kdf.printKdfParams()
   wlt.changeWalletEncryption( securePassphrase=passphrase )
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)
   
   print '\n(3) Re-reading wallet from file, compare the two wallets'
   wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   printpassorfail(wlt.isEqualTo(wlt2, debug=debugPrintAlot))
   # NOTE:  this isEqual operation compares the serializations
   #        of the wallet addresses, which only contains the 
   #        encrypted versions of the private keys.  However,
   #        wlt is unlocked and contains the plaintext keys, too
   #        while wlt2 does not.

   print '\n(3)Look at wlt again, before we lock it'
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)
   wlt.lock()
   print '\n(3)And now it should be locked...'
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)


   #############################################################################
   print '\n(4)Testing changing passphrase on encrypted wallet',

   wlt.unlock( securePassphrase=passphrase )
   print '...to same passphrase'
   wlt.changeWalletEncryption( securePassphrase=passphrase )

   print '\n(4)And now testing new passphrase...'
   wlt.changeWalletEncryption( securePassphrase=passphrase2 )
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)
   
   print '\n(4) Re-reading wallet from file, compare the two wallets'
   wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   printpassorfail(wlt.isEqualTo(wlt2, debug=debugPrintAlot))

   #############################################################################
   print '\n(5)Testing changing KDF on encrypted wallet'

   wlt.unlock( securePassphrase=passphrase2 )
   print '\n(5)Before kdf change:'
   wlt.kdf.printKdfParams()
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)

   wlt.changeKdfParams(1024, 999, hex_to_binary('00'*32), passphrase2)
   print '\n(5)After kdf change:'
   wlt.kdf.printKdfParams()
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(5) And now changing the encryption to the same, again'
   wlt.changeWalletEncryption( securePassphrase=passphrase2 )
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(5) Get new address from locked wallet'
   print 'Locking wallet'
   wlt.lock()
   for i in range(10):
      wlt.getNextUnusedAddress()
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)
   
   print '\n(5) Re-reading wallet from file, compare the two wallets'
   wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   printpassorfail(wlt.isEqualTo(wlt2, debug=debugPrintAlot))

   #############################################################################
   # !!!  #forkOnlineWallet()
   print '\n(6)Testing forking encrypted wallet for online mode'
   wlt.forkOnlineWallet('OnlineVersionOfEncryptedWallet.bin')
   wlt2.readWalletFile('OnlineVersionOfEncryptedWallet.bin')
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(6)Getting a new addresses from both wallets'
   for i in range(wlt.addrPoolSize*2):
      wlt.getNextUnusedAddress()
      wlt2.getNextUnusedAddress()

   newaddr1 = wlt.getNextUnusedAddress()
   print 'New address (reg):   ', newaddr1.getAddrStr()
   newaddr2 = wlt2.getNextUnusedAddress()
   print 'New address (online):', newaddr2.getAddrStr()

   printpassorfail(newaddr1.getAddr160() == newaddr2.getAddr160())

   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(6) Re-reading wallet from file, compare the two wallets'
   wlt3 = PyBtcWallet().readWalletFile('OnlineVersionOfEncryptedWallet.bin')
   wlt3.pprint(indent=' '*5, allAddrInfo=debugPrint)


   #############################################################################
   print '\n(7)Testing removing wallet encryption'
   print 'Wallet is locked?  ', wlt.isLocked
   wlt.unlock(securePassphrase=passphrase2)
   wlt.changeWalletEncryption( None )
   wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)

   print '\n(7) Re-reading wallet from file, compare the two wallets'
   wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   printpassorfail(wlt.isEqualTo(wlt2, debug=debugPrintAlot))

   #############################################################################
   print '\n\n'
   print '*********************************************************************'
   print '\n(8)Doing interrupt tests to test wallet-file-update recovery'
   def hashfile(fn):
      f = open(fn,'r')
      d = hash256(f.read())
      f.close()
      return binary_to_hex(d[:8])
   
   def printfilestatus(fn):
      if os.path.exists(fn):
         print '   ', hashfile(fn), '   ', fn.split('/')[-1]
      else:
         print '   ', 'No file:'.ljust(16), '   ', fn.split('/')[-1]

   def printstat():
      printfilestatus(fileA)
      printfilestatus(fileB)
      printfilestatus(fileAupd)
      printfilestatus(fileBupd)

   print '\n(8a)Starting test with the unencrypted wallet from part (6)'
   printstat()
   correctMainHash = hashfile(fileA)

   try:
      wlt.interruptTest1 = True
      wlt.getNextUnusedAddress()
   except InterruptTestError:
      print 'Interrupted!'
      pass
   wlt.interruptTest1 = False

   print '\n(8a)Interrupted getNextUnusedAddress on primary file update'
   printstat()
   print '\n(8a)Do consistency check on the wallet'
   wlt.doWalletFileConsistencyCheck()
   printstat()
   printpassorfail(correctMainHash==hashfile(fileA))
   
   print '\n(8b) Try interrupting at state 2'
   printstat()

   try:
      wlt.interruptTest2 = True
      wlt.getNextUnusedAddress()
   except InterruptTestError:
      print 'Interrupted!'
      pass
   wlt.interruptTest2 = False

   print '\n(8b)Interrupted getNextUnusedAddress on between primary/backup update'
   printstat()
   print '\n(8b)Do consistency check on the wallet'
   wlt.doWalletFileConsistencyCheck()
   printstat()
   printpassorfail(hashfile(fileA)==hashfile(fileB))



   print '\n(8c) Try interrupting at state 3'
   printstat()

   try:
      wlt.interruptTest3 = True
      wlt.getNextUnusedAddress()
   except InterruptTestError:
      print 'Interrupted!'
      pass
   wlt.interruptTest3 = False

   print '\n(8c)Interrupted getNextUnusedAddress on backup file update'
   printstat()
   print '\n(8c)Do consistency check on the wallet'
   wlt.doWalletFileConsistencyCheck()
   printstat()
   printpassorfail(hashfile(fileA)==hashfile(fileB))


   #############################################################################
   print '\n\n'
   print '*********************************************************************'
   print '\n(9)Checksum-based byte-error correction tests!'
   print '\n(9)Start with a good primary and backup file...'
   printstat()

   print '\n(9a)Open primary wallet, change second byte in KDF'
   wltfile = open(wlt.walletPath,'r+b')
   wltfile.seek(326)
   wltfile.write('\xff')
   wltfile.close()
   print '\n(9a)Byte changed, file hashes:'
   printstat()

   print '\n(9a)Try to read wallet from file, should correct KDF error, write fix'
   wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
   printstat()
   printpassorfail(hashfile(fileA)==hashfile(fileB))

   print '\n\n'
   print '*********************************************************************'
   print '\n(9b)Change a byte in each checksummed field in root addr'
   wltfile = open(wlt.walletPath,'r+b')
   wltfile.seek(838);  wltfile.write('\xff')
   wltfile.seek(885);  wltfile.write('\xff')
   wltfile.seek(929);  wltfile.write('\xff')
   wltfile.seek(954);  wltfile.write('\xff')
   wltfile.seek(1000);  wltfile.write('\xff')
   wltfile.close()
   print '\n(9b) New file hashes...'
   printstat()

   print '\n(9b)Try to read wallet from file, should correct address errors'
   wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
   printstat()
   printpassorfail(hashfile(fileA)==hashfile(fileB))
   
   print '\n\n'
   print '*********************************************************************'
   print '\n(9c)Change a byte in each checksummed field, of first non-root addr'
   wltfile = open(wlt.walletPath,'r+b')
   wltfile.seek(1261+21+838);  wltfile.write('\xff')
   wltfile.seek(1261+21+885);  wltfile.write('\xff')
   wltfile.seek(1261+21+929);  wltfile.write('\xff')
   wltfile.seek(1261+21+954);  wltfile.write('\xff')
   wltfile.seek(1261+21+1000);  wltfile.write('\xff')
   wltfile.close()
   print '\n(9c) New file hashes...'
   printstat()

   print '\n(9c)Try to read wallet from file, should correct address errors'
   wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
   printstat()
   printpassorfail(hashfile(fileA)==hashfile(fileB))

   print '\n\n'
   print '*********************************************************************'
   print '\n(9d)Now butcher the CHECKSUM, see if correction works'
   wltfile = open(wlt.walletPath,'r+b')
   wltfile.seek(977); wltfile.write('\xff')
   wltfile.close()
   print '\n(9d) New file hashes...'
   printstat()

   print '\n(9d)Try to read wallet from file, should correct address errors'
   wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
   printstat()
   printpassorfail(hashfile(fileA)==hashfile(fileB))


   print '*******'
   print '\n(9z) Test comment I/O'
   comment1 = 'This is my normal unit-testing address.'
   comment2 = 'This is fake tx... no tx has this hash.'
   comment3 = comment1 + '  Corrected!'
   hash1 = '\x1f'*20  # address160
   hash2 = '\x2f'*32  # tx hash
   wlt.setComment(hash1, comment1)
   wlt.setComment(hash2, comment2)
   wlt.setComment(hash1, comment3)

   wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
   c3 = wlt2.getComment(hash1)
   c2 = wlt2.getComment(hash2)
   print c3
   print c2
   printpassorfail(c3==comment3)
   printpassorfail(c2==comment2)

   

   #############################################################################
   print '\n\n'
   print '*********************************************************************'
   print '\n(10) Finally!  Start the wallet tests involving the blockchain!'

   print '\n(10) Add an address with some money to this wallet'
   binPrivKey = hex_to_binary('a47a7e263f9ec17d7fbb4a649541001e8bb1266917aa77f5773810d7d81f00a5')
   newAddr20 = wlt.importExternalAddressData( privKey=binPrivKey )
   if debugPrint: wlt.pprint(indent=' '*5, allAddrInfo=debugPrint)
   


   print '\n(10) Make sure C++ has all the addresses:'
   cppwlt = wlt.cppWallet
   naddr = cppwlt.getNumAddr()
   for i in range(naddr):
      print '   Address:', hash160_to_addrStr(cppwlt.getAddrByIndex(i).getAddrStr20())

   
   print '\n(10) Loading blockchain from blk0001.dat'
   BDM_LoadBlockchainFile()  # looks for blk0001.dat in satoshi client location

   print '\n(10) Now syncing this wallet with the blockchain'
   # While using the blk0001.dat maintained by satoshi client, never write data
   wlt.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
   wlt.syncWithBlockchain()

   utxoList = wlt.getUnspentTxOutList()
   pprintUnspentTxOutList(utxoList, 'Unspent TxOuts for your wallet: ')

   nBTC = 1.4*ONE_BTC
   print '\n(10) Select inputs for a', coin2str(nBTC), 'BTC tx to myself'
   prelimSelection = PySelectCoins(utxoList, nBTC, minFee=0)
   feeRecommended = calcMinSuggestedFees(prelimSelection, nBTC, 0)
   pprintUnspentTxOutList(prelimSelection, 'Selected TxOuts for (tgt,fee)=(%s,%s)' % \
                           (coin2str(nBTC), coin2str(0)))
   print '*Recommended fees:  AbsMin=%s, Suggest=%s' % tuple([coin2str(f) for f in feeRecommended])
   recip = addrStr_to_hash160('1F7G4aq9fbAhqGb9jcnsVn6CRm6dqJf3sD')

   theSum = sumTxOutList(prelimSelection)
   recipPairs = [ \
         [recip, nBTC], \
         [newAddr20, theSum-nBTC] ]

   if theSum==0:
      print 'Not enough funds.  Skipping TxDP construction'
   else:
      print '\n\n(10)Creating TxDistProposal:'
      txdp = PyTxDistProposal().createFromTxOutSelection(prelimSelection, recipPairs)
      if debugPrint: txdp.pprint('   ')
      print '\n\n(10)Signing the TxDP:'
      wlt.signTxDistProposal(txdp)
      if debugPrint: txdp.pprint('   ')
   
      txToBroadcast = txdp.prepareFinalTx()
      print ''
      txToBroadcast.pprint()
      print ''

      print binary_to_hex(txToBroadcast.serialize())
      pprintHex(binary_to_hex(txToBroadcast.serialize()))




   #############################################################################
   print '\n\n'
   print '*********************************************************************'
   print '\n(11) One more blockchain test, this time with online/watching-only'
   wlt2.readWalletFile('OnlineVersionOfEncryptedWallet.bin')
   wlt2.doBlockchainSync=BLOCKCHAIN_READONLY  
   wlt2.syncWithBlockchain()
   wlt2.pprint(indent=' '*5, allAddrInfo=debugPrint)
   
   print '\n(11) Search for unspent TxOuts for this online wallet'
   utxoList = wlt2.getUnspentTxOutList()
   pprintUnspentTxOutList(utxoList, 'Unspent TxOuts for your wallet: ')

   nBTC = 1.4*ONE_BTC
   print '\n(11) Select inputs for a', coin2str(nBTC), 'BTC tx to myself'
   prelimSelection = PySelectCoins(utxoList, nBTC, minFee=0)
   feeRecommended = calcMinSuggestedFees(prelimSelection, nBTC, 0)
   pprintUnspentTxOutList(prelimSelection, 'Selected TxOuts for (tgt,fee)=(%s,%s)' % \
                           (coin2str(nBTC), coin2str(0)))
   print '*Recommended fees:  AbsMin=%s, Suggest=%s' % tuple([coin2str(f) for f in feeRecommended])
   recip = addrStr_to_hash160('1F7G4aq9fbAhqGb9jcnsVn6CRm6dqJf3sD')

   theSum = sumTxOutList(prelimSelection)
   recipPairs = [ \
         [recip, nBTC], \
         [recip, theSum-nBTC] ]

   if theSum == 0:
      print 'Not enough funds.... skipping tx construction'
   else:
      print '\n\n(11)Creating TxDistProposal:'
      txdp = PyTxDistProposal().createFromTxOutSelection(prelimSelection, recipPairs)
      if debugPrint: txdp.pytxObj.pprint()
      print '\n\n(11) Attempting to sign TxDP with online wallet'
      wlt2.signTxDistProposal(txdp)

   os.remove('OnlineVersionOfEncryptedWallet.bin')
   os.remove('OnlineVersionOfEncryptedWalletbackup.bin')




################################################################################
################################################################################
if Test_TxDistProposals:
   print ''
   print '*********************************************************************'
   print 'Testing Tx Distribution Proposals for offline signatures'
   print '*********************************************************************'
   print ''
   print 'Create a valid tx, serialize it, unserialize it, sign it'

   debugPrint = True

   print '\n(1) Create a wallet, add our address'
   privKey = SecureBinaryData(hex_to_binary('aa'*32))
   pubKey  = CryptoECDSA().ComputePublicKey(privKey)
   addr20  = pubKey.getHash160()
   wlt = PyBtcWallet().createNewWallet(withEncrypt=False)


   binPrivKey = hex_to_binary('a47a7e263f9ec17d7fbb4a649541001e8bb1266917aa77f5773810d7d81f00a5')
   myOwnAddr160 = wlt.importExternalAddressData( privKey=binPrivKey )
   wlt.pprint(indent=' '*5, allAddrInfo=False)
   
   BDM_LoadBlockchainFile()  # looks for blk0001.dat in satoshi client location
   wlt.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)

   # Get all the unspent TxOuts for this addr
   wlt.syncWithBlockchain()
   utxoList = wlt.getTxOutList('Spendable')
   pprintUnspentTxOutList(utxoList, 'Unspent TxOuts for your wallet: ')

   nBTC = 0.05*ONE_BTC
   print '\n(1) Select inputs for a', coin2str(nBTC), 'BTC tx to myself'
   prelimSelection = PySelectCoins(utxoList, nBTC, minFee=0)
   pprintUnspentTxOutList(prelimSelection, 'Selected TxOuts for (tgt,fee)=(%s,%s)' % \
                                                   (coin2str(nBTC), coin2str(0)))
   recip160 = addrStr_to_hash160('1F7G4aq9fbAhqGb9jcnsVn6CRm6dqJf3sD')

   theSum = sumTxOutList(prelimSelection)
   recipPairs = [  [recip160,     nBTC], \
                   [myOwnAddr160, theSum-nBTC] ]

   print '\n(1)Creating TxDistProposal:'
   txdp = PyTxDistProposal().createFromTxOutSelection(prelimSelection, recipPairs)

   print '\n(1)Serializing:'
   asciiBlock = txdp.serializeAscii()
   for l in asciiBlock.split('\n'):
      print '   ', l

   print '\n(1)Unserializing'
   txdp2 = PyTxDistProposal().unserializeAscii(asciiBlock)
   print '\n(1) TxDP has enough signatures?', txdp.checkTxHasEnoughSignatures()
      
   txdp2.pprint()
   print '\n(1)Sign it, now'
   txdpSigned = wlt.signTxDistProposal(txdp2)
   print '\n(1) Signed enough inputs?', txdpSigned.checkTxHasEnoughSignatures()
   print '\n(1) Verified?', txdpSigned.checkTxHasEnoughSignatures(alsoVerify=True)

   print '\n(1) Re-serialized signed txdp'
   asciiBlock = txdpSigned.serializeAscii()
   for l in asciiBlock.split('\n'):
      print '   ', l
   
   print '\n(1) Preparing TxDP for broadcast'
   txdp3 = PyTxDistProposal().unserializeAscii(asciiBlock)
   txToBroadcast = txdpSigned.prepareFinalTx()
   print '\n(1) Final tx to broadcast!'
   print binary_to_hex(txToBroadcast.serialize())
   print ''
   pprintHex(binary_to_hex(txToBroadcast.serialize()))

   # TODO: test a multisig TxDP


################################################################################
################################################################################
if Test_SelectCoins:
   print ''
   print '*********************************************************************'
   print 'Testing SelectCoins'
   print '*********************************************************************'
   print ''

   addrs = [ch*20 for ch in ['\xaa','\xbb','\xcc','\xdd','\xee']]
   utxo3s = [ [addrs[0], ONE_BTC*1.0,     5  ], \
              [addrs[0], ONE_BTC*1.5,     130], \
              [addrs[0], ONE_BTC*0.0005,  200], \
              [addrs[0], ONE_BTC*2.1,     130], \
              [addrs[0], ONE_BTC*0.0001,  130], \
              [addrs[0], ONE_BTC*5.5,       0], \
              [addrs[0], ONE_BTC*0.3,       0], \
              [addrs[0], ONE_BTC*10.1,    130], \
              #[addrs[1], ONE_BTC*22.3331, 130], \
              [addrs[1], ONE_BTC*0.0004, 1000], \
              [addrs[1], ONE_BTC*1.1,     100], \
              [addrs[1], ONE_BTC*3.3,     130], \
              [addrs[2], ONE_BTC*5.2,     130], \
              [addrs[3], ONE_BTC*5.3,     130], \
              [addrs[4], ONE_BTC*5.4,     130] ]
   utxolist = []
   for trip in utxo3s:
      utxo = PyUnspentTxOut() 
      utxo.addr = trip[0]
      utxo.val  = trip[1]
      utxo.conf = trip[2]
      utxo.binScript = '\x76\xa9\x14' + utxo.addr + '\x88\xac'
      utxolist.append(utxo)
   

   targetOutVal = 10*ONE_BTC
   minFee = 0
   
   
   pprintUnspentTxOutList(utxolist, 'Test set of UTXOs')

   testTargs = [t*ONE_BTC for t in [0.001, 0.01, 0.0005, 0.1, 1.0, 2.5, 5.0, 1.3928, 10.0, 22.32221, 50, 60, 90]]
   testFees  = [f*ONE_BTC for f in [0, 0.0001, 0.0005, 0.01, 0.1]]

   for targ in testTargs:
      for fee in testFees:
         selected = PySelectCoins(utxolist, targ, fee)
         pprintUnspentTxOutList(selected, '(Targ,Fee) = (%s,%s)' % (coin2str(targ).strip(), coin2str(fee).strip()))

   



################################################################################
################################################################################
if Test_CryptoTiming:
   print ''
   print '*********************************************************************'
   print 'Testing Crypto++ Methods via SWIG'
   print '*********************************************************************'
   print ''
   print 'Testing key-derivation function - timings and memory usage:'

   testPass1 = SecureBinaryData('This is my password ')
   testPass2 = SecureBinaryData('This is my password.')

   # Key-derivation function 1 -- default time/mem
   print '   ***KDF 1:  Default params***'
   kdf1 = Cpp.KdfRomix()
   kdf1.computeKdfParams()

   # Key-derivation function 2 
   print '   ***KDF 2:  0.5s-1.0s timing, default mem***'
   kdf2 = Cpp.KdfRomix()
   kdf2.computeKdfParams(1.0)

   # Key-derivation function 3
   print '   ***KDF 3:  0.25s-0.5s timing, 256kB max***'
   kdf3 = Cpp.KdfRomix()
   kdf3.computeKdfParams(0.5, 256*1024)

   for i,kdf in enumerate([kdf1, kdf2, kdf3]):
      memStr = kdf.getMemoryReqtBytes()
      if memStr>1024*1024:
         memStr = '%0.1f'%(memStr/(1024.*1024.)) + ' MB'
      elif memStr>1024:
         memStr = '%0.1f'%(memStr/1024.) + ' kB'
      else:
         memStr = '%0.1f'%(memStr) + ' bytes'
      print '   Testing KDF(' + str(i+1) + ')'
      print '      Hash Function:'.ljust(24), kdf.getHashFunctionName()
      print '      Mem Required :'.ljust(24), memStr
      print '      Num Iteration:'.ljust(24), kdf.getNumIterations();
      print '      Hex Salt Used:'.ljust(24), kdf.getSalt().toHexStr()[:29] + '...'
      for pswd in [testPass1, testPass2, testPass1]:
         start=time.time()
         key = kdf.DeriveKey(pswd)
         
         print '      Pass: "%s" --> Key: %s (%0.6f sec)' %  \
                                                      (pswd.toBinStr().ljust(20), \
                                                      key.toHexStr()[:32],  \
                                                      time.time()-start)

   print ''
   print ''
   print 'Testing Crypto++::AES timings'
   keyAES  = SecureBinaryData( hex_to_binary('aa'*32) )
   secret  = SecureBinaryData( hex_to_binary('aa'*32) )
   withIV  = SecureBinaryData( hex_to_binary('bb'*16) )
   noIV    = SecureBinaryData('')
   cipher  = SecureBinaryData()
   plain   = SecureBinaryData()
   
   nTest = 10000

   """
   # Test with no initialization vector
   start = time.time()
   for i in range(nTest):
      cipher = CryptoAES().EncryptCFB(secret, keyAES, noIV)
   end = time.time()
   print '    AES Encryption with IV generation: %0.1f/sec' % (nTest/(end-start))
   """

   # Now using an IV
   start = time.time()
   for i in range(nTest):
      cipher = CryptoAES().EncryptCFB(secret, keyAES, withIV)
   end = time.time()
   print '    AES Encryption with supplied IV  : %0.1f/sec' % (nTest/(end-start))
      

   # Test decryption speed
   start = time.time()
   for i in range(nTest):
      plain = CryptoAES().DecryptCFB(cipher, keyAES, withIV)
   end = time.time()
   print '    AES Decryption with supplied IV  : %0.1f/sec' % (nTest/(end-start))

   print '    AES roundtrip, compare results:'
   print '       Secret : ', secret.toHexStr()
   print '       Cipher : ', cipher.toHexStr()
   print '       Decrypt: ', plain.toHexStr()
   print '       Result : ',
   printpassorfail(plain==secret)


   print '\n'
   print 'Testing Crypto++::ECDSA timings'
   privKey = SecureBinaryData(hex_to_binary('aa'*32))
   pubKey  = SecureBinaryData()
   nTest = 100

   # Test Conversion from PrivKey to PubKey
   start = time.time()
   for i in range(nTest):
      pubKey = CryptoECDSA().ComputePublicKey(privKey)
   end = time.time()
   print '   PrivateKey --> PublicKey'.ljust(36),
   print ':  %0.1f/sec' % (nTest/(end-start))

   # Check keypair match
   start = time.time()
   for i in range(nTest):
      match = CryptoECDSA().CheckPubPrivKeyMatch(privKey, pubKey)
   end = time.time()
   print '   PubPrivPair--> CheckMatch'.ljust(36),
   print ':  %0.1f/sec' % (nTest/(end-start))

   # Test signing speed
   msg = SecureBinaryData( hex_to_binary('ff'*32) )
   sig = SecureBinaryData()
   start = time.time()
   for i in range(nTest):
      sig = CryptoECDSA().SignData(msg, privKey)
   end = time.time()
   print '   PrivateKey --> Signature'.ljust(36),
   print ':  %0.1f/sec' % (nTest/(end-start))

   # Test ECDSA verification speed
   start = time.time()
   for i in range(nTest):
      isValid = CryptoECDSA().VerifyData(msg, sig, pubKey)
   end = time.time()
   print '   PublicKey  --> VerifySig'.ljust(36),
   print ':  %0.1f/sec' % (nTest/(end-start))


   # Deterministic wallet chain computation
   chainedPrivKey = SecureBinaryData()
   chainedPubKey  = SecureBinaryData()
   chaincode      = SecureBinaryData( hex_to_binary('45'*32))

   start = time.time()
   for i in range(nTest):
      chainedPubKey = CryptoECDSA().ComputeChainedPrivateKey(privKey, chaincode)
   end = time.time()
   print '   PrivateKey --> NextInChain'.ljust(36),
   print ':  %0.1f/sec' % (nTest/(end-start))

   start = time.time()
   for i in range(nTest):
      chainedPubKey = CryptoECDSA().ComputeChainedPublicKey(pubKey, chaincode)
   end = time.time()
   print '   PublicKey  --> NextInChain'.ljust(36),
   print ':  %0.1f/sec' % (nTest/(end-start))




if Test_SettingsFile:
   print ''
   print '*********************************************************************'
   print 'Testing Settings-file operations'
   print '*********************************************************************'
   print ''
   
   testFile1 = 'settingsFile1.txt'
   testFile2 = 'settingsFile2.txt'
   settings = SettingsFile(testFile1)
   settings.set('TestKey1', 32) 
   settings.set('TestKey2', 12.3) 
   settings.set('TestKey3', 'hello settings file')
   settings.set('TestKey4', (1,2,3))
   settings.set('TestKey5', [1,2,3])
   settings.set('Test Key 6', 12)
   settings.set('Test Key 7', ['str1', 'str2'])
   settings.set('TestKey8', False)
   settings.set('TestKey9', True)
   settings.set('TestKey10', [True, True, False])

   
   settings.pprint()

   settings.extend('TestKey2', 1.1)
   settings.extend('TestKey4', 6)
   settings.extend('TestKey11', 'astring')
   settings.extend('TestKey12', 83)

   print 'Reading in'
   newSettings = SettingsFile(testFile1)
   newSettings.pprint()

   print 'Expect list:'
   print '   ',settings.get('Test Key 6')
   print '   ',settings.get('Test Key 6', expectList=True)
   print '   ',settings.get('Test Key 7', expectList=False)
   print '   ',settings.get('Test Key 7', expectList=True)

   print 'Writing new settings file'
   newSettings.writeSettingsFile(testFile2)

   with  open(testFile1, 'r') as f:
      f1 = f.read()
   with open(testFile2, 'r') as f:
      f2 = f.read()

   os.remove(testFile1)
   os.remove(testFile2)


if Test_WalletMigrate:

   import getpass
   p = '/home/alan/winlinshare/wallet_plain.dat'
   print 'Encrypted? ', checkSatoshiEncrypted(p)
   plain = extractSatoshiKeys(p)

   print len(plain)
   print sum([1 if p[2] else 0 for p in plain])
   print sum([0 if p[2] else 1 for p in plain])

   p = '/home/alan/.bitcoin/wallet.dat'
   print 'Encrypted? ', checkSatoshiEncrypted(p)
   k = getpass.getpass('decrypt passphrase:')
   crypt = extractSatoshiKeys(p, k)


   print len(crypt)
   print sum([1 if p[2] else 0 for p in crypt])
   print sum([0 if p[2] else 1 for p in crypt])






if Test_AddressBooks:

      
   cppWlt = Cpp.BtcWallet()
   cppWlt.addAddress_1_(hex_to_binary("0c6b92101c7025643c346d9c3e23034a8a843e21"))
   cppWlt.addAddress_1_(hex_to_binary("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"))
   cppWlt.addAddress_1_(hex_to_binary("34c9f8dc91dfe1ae1c59e76cbe1aa39d0b7fc041"))
   cppWlt.addAddress_1_(hex_to_binary("d77561813ca968270d5f63794ddb6aab3493605e"))
   cppWlt.addAddress_1_(hex_to_binary("0e0aec36fe2545fb31a41164fb6954adcd96b342"))
   cppWlt.addAddress_1_(hex_to_binary("6c27c8e67b7376f3ab63553fe37a4481c4f951cf"))

   TheBDM.registerWallet(cppWlt)
   
   print '\n\nLoading Blockchain from:', BLK0001_PATH
   BDM_LoadBlockchainFile(BLK0001_PATH)
   print 'Done!'

   TheBDM.scanBlockchainForTx(cppWlt)
   cppWlt.pprintLedger()


   AddrBook = cppWlt.createAddressBook()
   print "AB  ", len(AddrBook)
   print "Lst ", len(list(AddrBook))
   print "[:] ", len(AddrBook[:])

   for abe in AddrBook:
      print binary_to_hex(abe.getAddr160()),
      print len(abe.getTxList())
      for rtx in abe.getTxList():
         print '\t', binary_to_hex(rtx.getTxHash()), rtx.getBlkNum(), rtx.getTxIndex()


if Test_URIParse:

   print 'Testing percent-encoding:'
   test = []
   test.append('regularmessage')
   test.append('regular_message')
   test.append('regular%message')
   test.append('regular&message')
   test.append('regular message~')

   for t in test:
      t1 = uriReservedToPercent(t)
      t2 = uriPercentToReserved(t1)
      passStr = 'PASS' if t==t2 else '***FAIL***'
      print '\t',
      print ('"%s"'%t).ljust(20),
      print ('"%s"'%t1).ljust(20),
      print ('"%s"'%t2).ljust(20),
      print ('(%s)'%passStr)
      


   print 'Testing URI parsing'
   test = []
   test.append('notavaliduristring')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L;version=1.0')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L?amount=20.3')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L;version=1.0?amount=20.3')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L?amount=0.00003&label=Luke-Jr')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L;version=1.0?amount=20.3&label=Luke-Jr')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L;version=1.0?amount=203&label=Luke-Jr')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L?amount=203&message=Donation%20for%20proj')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L?amount=203&label=Alan%27s%20key&message=Donation%20for%20proj')
   test.append('bitcoin:1NS17iag9jJgTHD1VXjvLCEnZuQ3rJED9L?amount=2f03&label=invalid')

   for t in test:
      print 'URI:', t
      outputdict = parseBitcoinURI(t)
      if len(outputdict)==0:
         print '\t<empty>'
         continue

      for key,val in outputdict.iteritems():
         print '\t', key.ljust(12), '=', val
      

if Test_BkgdThread:
   import math

   def longFuncA(a,b,c):
      print 'FuncA', a,b,c
      nIter = 10**7
      start = RightNow()
      for i in xrange(nIter):
         math.log(float(i)+1)
      print 'Finished %d log() calculations'%nIter,
      print '...in', RightNow() - start, 'seconds'


   def longFuncB(a,b,c):
      print 'FuncB', a,b,c
      nIter = 10**7
      start = RightNow()
      for i in xrange(nIter):
         math.sqrt(float(i)+1)
      print 'Finished %d sqrt() calculations'%nIter,
      print '...in', RightNow() - start, 'seconds'


   def longFuncC(a,b,c):
      print 'FuncC', a,b,c
      nIter = 10**7
      start = RightNow()
      for i in xrange(nIter):
         math.sin(float(i)+1)
      print 'Finished %d sin() calculations'%nIter,
      print '...in', RightNow() - start, 'seconds'


   print 'Creating Thread'
   thr = PyBackgroundThread()
   thr.setPreThreadFunction(longFuncA, 1, '2', 3.0)
   thr.setThreadFunction(longFuncB, *(5, '6', 8.0))
   thr.setPostThreadFunction(longFuncC, a=50, b='90', c=12.0)
   print 'Starting thread...'
   thr.start()
   print 'Print statement right after thread.start()... waiting'
   print 'Run longFuncC again just for fun, while we wait...'
   longFuncC(0,0,0)




if Test_AsyncBDM:

   print '***********************************************************************'
   print 'Testing asynchronous BlockDataManager'
   print '***********************************************************************'

   def printBDMStuff():
      print 'BlkMode:   ', TheBDM.getBDMState()
      print 'IsScanning:', TheBDM.isScanning()
      print 'IsInit:    ', TheBDM.isInitialized()
      print 'doBlock:   ', TheBDM.alwaysBlock
      print 'ScanAllow: ', TheBDM.allowRescan
      print 'isDirty:   ', TheBDM.isDirty
      print 'NumAddr:   ', TheBDM.masterCppWallet.getNumAddr()
      print 'NumPyWlt:  ', len(TheBDM.pyWltList) 
      print 'NumCppWlt: ', len(TheBDM.cppWltList)
      print 'NumInputs: ', TheBDM.inputQueue.qsize()
      print 'NumOutput: ', TheBDM.outputQueue.qsize()

   try:
      print 'Starting AsyncBDM Test'
      printBDMStuff()
   
   
      print '\n\n(Async) Loading Blockchain from:', BTC_HOME_DIR
      TheBDM.setSatoshiDir(BTC_HOME_DIR)
   
      start = RightNow()
      TheBDM.loadBlockchain(wait=False)
      print RightNow()-start, 'seconds'
   
      print TheBDM.getBDMState()
      while TheBDM.isScanning():
         print 'Still waiting for scan to finish...'
         time.sleep(1)
      printBDMStuff()
      print 'Thread done!'
   
      print '\n\nGetting top block information'
      head = TheBDM.getTopBlockHeader()
      head.pprint()
   
      print '\n\nGetting genesis block information'
      head = TheBDM.getHeaderByHeight(0)
      head.pprint()
   
      # Do the same thing, but with blocking
      print '\n\n(Async) Resetting'
      TheBDM.Reset(wait=True)
      print 'Done resetting BDM.'
      printBDMStuff()
   
      print '\n\n(Blocking) Loading Blockchain from:', BTC_HOME_DIR
      TheBDM.setBlocking(True)
      TheBDM.setSatoshiDir(BTC_HOME_DIR)
   
      start = RightNow()
      TheBDM.loadBlockchain()
      print RightNow()-start, 'seconds'
   
      printBDMStuff()
      print 'Done!'
   
      
   
      print 'Start testing blockchain with wallets, now'
      print 'Resetting BDM'
      TheBDM.Reset(wait=True)
   
      print 'Setting blocking=False'
      TheBDM.setBlocking(False)
      TheBDM.setSatoshiDir(BTC_HOME_DIR)
   
      cppWlt = Cpp.BtcWallet()
   
      if not USE_TESTNET:
         cppWlt.addAddress_1_(hex_to_binary("604875c897a079f4db88e5d71145be2093cae194"))
         cppWlt.addAddress_1_(hex_to_binary("8996182392d6f05e732410de4fc3fa273bac7ee6"))
         cppWlt.addAddress_1_(hex_to_binary("b5e2331304bc6c541ffe81a66ab664159979125b"))
         cppWlt.addAddress_1_(hex_to_binary("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"))
      else:
         # Test-network addresses
         cppWlt.addAddress_1_(hex_to_binary("5aa2b7e93537198ef969ad5fb63bea5e098ab0cc"))
         cppWlt.addAddress_1_(hex_to_binary("28b2eb2dc53cd15ab3dc6abf6c8ea3978523f948"))
         cppWlt.addAddress_1_(hex_to_binary("720fbde315f371f62c158b7353b3629e7fb071a8"))
         cppWlt.addAddress_1_(hex_to_binary("0cc51a562976a075b984c7215968d41af43be98f"))
   
      cppWltEmpty = Cpp.BtcWallet()
   
      print 'Registering cppWallet:'
      TheBDM.registerWallet(cppWlt)
      TheBDM.registerWallet(cppWltEmpty)
       
      print 'Loading blockchain with wallet already registered',
      start = RightNow()
      TheBDM.loadBlockchain()
      while TheBDM.getBDMState()=='Scanning':
         time.sleep(0.1)
         print '.',
      print (RightNow() - start), ' seconds'
   
      print '\n\nUpdating registered wallets with blockchain info'
      start = RightNow()
      TheBDM.updateWalletsAfterScan()
      while TheBDM.getBDMState()=='Scanning':
         time.sleep(0.1)
         print '.',
      print (RightNow() - start), ' seconds'
   
      #nAddr = cppWlt.getNumAddr()
      #print 'Address Balances:'
      #for i in range(nAddr):
         #cppAddr = cppWlt.getAddrByIndex(i)
         #bal = cppAddr.getSpendableBalance()
         #print '   %s %s' % (hash160_to_addrStr(cppAddr.getAddrStr20())[:12], coin2str(bal))
   
      printBDMStuff()
      nAddr = cppWlt.getNumAddr()
      print 'Address Balances:'
      for i in range(nAddr):
         cppAddr = cppWlt.getAddrByIndex(i)
         bal = cppAddr.getSpendableBalance()
         print '   %s %s' % (hash160_to_addrStr(cppAddr.getAddrStr20())[:12], coin2str(bal))
   
   
      if not USE_TESTNET:
         cppWltEmpty.addAddress_1_(hex_to_binary("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"))
      else:
         cppWltEmpty.addAddress_1_(hex_to_binary("57ac7bfb77b1f678043ac6ea0fa67b4686c271e5"))
         cppWltEmpty.addAddress_1_(hex_to_binary("b11bdcd6371e5b567b439cd95d928e869d1f546a"))
         cppWltEmpty.addAddress_1_(hex_to_binary("2bb0974f6d43e3baa03d82610aac2b6ed017967d"))
         cppWltEmpty.addAddress_1_(hex_to_binary("61d62799e52bc8ee514976a19d67478f25df2bb1"))
   
      # In practice, we won't be adding the addresses directly to the C++ wallets
      # We will add them to the python wallets, which will absorb them into the 
      # python code AND register them with the BDM
      # But working with the C++ wallets directly, need to re-register them
      print 'Re-registering cppWallets:'
      TheBDM.registerWallet(cppWlt)
      TheBDM.registerWallet(cppWltEmpty)
   
      print 'Need to rescan %d blocks (Wlt1)' % TheBDM.numBlocksToRescan(cppWlt)
      print 'Need to rescan %d blocks (Wlt2)' % TheBDM.numBlocksToRescan(cppWltEmpty)
      TheBDM.rescanBlockchain()
      start = RightNow()
      while TheBDM.getBDMState()=='Scanning':
         time.sleep(0.1)
         print '.',
      print (RightNow() - start), ' seconds'
      
      start = RightNow()
      print 'Update wallets after scan'
      TheBDM.updateWalletsAfterScan()
      print (RightNow() - start), ' seconds'

      printBDMStuff()
      nAddr = cppWltEmpty.getNumAddr()
      print 'Address Balances:'
      for i in range(nAddr):
         cppAddr = cppWltEmpty.getAddrByIndex(i)
         bal = cppAddr.getSpendableBalance()
         print '   %s %s' % (hash160_to_addrStr(cppAddr.getAddrStr20())[:12], coin2str(bal))



      # Test pybtcwallets:
      # Include a test wallet with a tiny amount of BTC

      # Since the BDM is already loaded, want to skip the scan until we're ready
      if USE_TESTNET:
         pywlt = PyBtcWallet().readWalletFile('armory.testnet.watchonly.wallet')
      else:
         pywlt = PyBtcWallet().readWalletFile('armory.mainnet.watchonly.wallet')

      TheBDM.registerWallet(pywlt, isFresh=False, wait=True)
      print 'NumToRescan: ', TheBDM.numBlocksToRescan(pywlt.cppWallet, wait=True)
      TheBDM.rescanBlockchain(wait=False)
      start = RightNow()
      while TheBDM.getBDMState()=='Scanning':
         time.sleep(0.1)
         print '.',
      print (RightNow() - start), ' seconds'

   except:
      print 'CRASH' 
      raise
   finally: 
      TheBDM.execCleanShutdown()
   
   

################################################################################
################################################################################
if Test_Timers:
   print '***********************************************************************'
   print 'Testing Timer Objects'
   print '***********************************************************************'
   
   n=100000

   TimerStart('Coin2Str10000x1')
   for i in xrange(n):
      j = coin2str(10002300000, maxZeros=2)
   TimerStop('Coin2Str10000x1')


   for i in xrange(n):
      TimerStart('Coin2Str1x10000')
      j = coin2str(10002300000, maxZeros=2)
      TimerStop('Coin2Str1x10000')


   TimerStart('LoopOnly')
   for i in xrange(n):
      pass
   TimerStop('LoopOnly')

   TimerStart('StartStopCycle')
   for i in xrange(n):
      TimerStart('MetaTimer')
      TimerStop('MetaTimer')
   TimerStop('StartStopCycle')

   print ''
   PrintTimings()
   SaveTimingsCSV('testtimings.csv')
   print ''



   
################################################################################
################################################################################
if Test_PyBkgdThread:
   print '***********************************************************************'
   print 'Testing Background Threading'
   print '***********************************************************************'
   from random import uniform
 
   # Will run the ComputePublicKey function a bunch of times in the background
   def compute(N, threadID):
      s = RightNow()
      for i in range(N):
         key = int_to_binary(long(uniform(0,2**32)), widthBytes=32)
         k = CryptoECDSA().ComputePublicKey(SecureBinaryData(key))
      ns = (RightNow() - s)
      #print 'Thread %d: %d keys in %0.2f sec,  %0.2f key/sec' % (threadID, N, ns, N/ns)
 
 
   # Figure out how many aggregate keys/sec we get with threading
   def test_N_threads(NThr):
      NPer = 1000

      # Test All
      thr = []
      for i in range(NThr):
         thr.append( PyBackgroundThread(compute, NPer, i))
   
      startTime = RightNow()
      for i in range(NThr):
         thr[i].start()
      
      for i in range(NThr):
         thr[i].join()
      
      total = (RightNow() - startTime)
      NC = NThr*NPer
      return NC, total

   for i in range(1,10):
      n,s = test_N_threads(i)
      print 'NThreads: %02d,  %0.2f keys/sec' % (i, n/s)

