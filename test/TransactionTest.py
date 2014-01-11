'''
Created on Jan 10, 2014

@author: Alan
'''
import sys
import unittest

from armoryengine.ALL import *

sys.argv.append('--nologging')


# Unserialize an reserialize

class TransactionTest(unittest.TestCase):

   
   def setUp(self):
      pass
   
   
   def tearDown(self):
      pass
   

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

      expected = ['x21' + '\x3a'*33 + '\xac', \
                  'x41' + '\x3a'*65 + '\xac']

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

     

   #############################################################################
   
   def test(self):
      self.assertRaises(InvalidHashError, 
      multiTx1  = PyTx().unserialize(multiTx1raw)
      paddingMinimizedMulti1, newTxMulti1 = multiTx1.minimizeDERSignaturePadding()
      self.assertEqual(multiTx1.inputs[0].binScript, newTxMulti1.inputs[0].binScript)
      self.assertEqual(multiTx1.inputs[1].binScript, newTxMulti1.inputs[1].binScript)
      self.assertEqual(multiTx1.inputs[2].binScript, newTxMulti1.inputs[2].binScript)
      self.assertEqual(multiTx1.inputs[3].binScript, newTxMulti1.inputs[3].binScript)
      self.assertFalse(paddingMinimizedMulti1)
      
      txString = multiTx1.toString()
      self.assertTrue(len(txString)> 0)
      
      multiTx2  = PyTx().unserialize(multiTx2raw)
      paddingMinimizedMulti2, newTxMulti2 = multiTx2.minimizeDERSignaturePadding()
      self.assertEqual(multiTx2.inputs[0].binScript, newTxMulti2.inputs[0].binScript)
      self.assertEqual(multiTx2.inputs[1].binScript, newTxMulti2.inputs[1].binScript)
      self.assertEqual(multiTx2.inputs[2].binScript, newTxMulti2.inputs[2].binScript)
      # Added 1 extra byte of padding
      self.assertEqual(len(multiTx2.inputs[3].binScript)-1, len(newTxMulti2.inputs[3].binScript))
      self.assertTrue(paddingMinimizedMulti2)
      
      tx1  = PyTx().unserialize(tx1raw)
      paddingMinimized1, newTx1 = tx1.minimizeDERSignaturePadding()
      self.assertEqual(tx1.inputs[0].binScript, newTx1.inputs[0].binScript)
      self.assertFalse(paddingMinimized1)
      tx2  = PyTx().unserialize(tx2raw)
      paddingMinimized2, newTx2 = tx2.minimizeDERSignaturePadding()
      # Old tx had 2 extra bytes of padding one each on the r and s
      self.assertEqual(len(tx2.inputs[0].binScript)-2, len(newTx2.inputs[0].binScript))
      self.assertTrue(paddingMinimized2)
      
      
   def testSerializeUnserialize(self):
      tx1 = PyTx().unserialize(tx1raw)
      tx2 = PyTx().unserialize(BinaryUnpacker(tx2raw))
      tx1again = tx1.serialize()
      tx2again = tx2.serialize()
      self.assertEqual(tx1again, tx1raw)
      self.assertEqual(tx2again, tx2raw)
      blk = PyBlock().unserialize( hex_to_binary(hexBlock) )
      blockReHex = binary_to_hex(blk.serialize())
      self.assertEqual(hexBlock, blockReHex)
      binRoot = blk.blockData.getMerkleRoot()
      self.assertEqual(blk.blockHeader.merkleRoot, blk.blockData.merkleRoot)
   
   def testCreateTx(self):
      addrA = PyBtcAddress().createFromPrivateKey(hex_to_int('aa' * 32))
      addrB = PyBtcAddress().createFromPrivateKey(hex_to_int('bb' * 32)) 

      # This TxIn will be completely ignored, so it can contain garbage
      txinA = PyTxIn()
      txinA.outpoint  = PyOutPoint().unserialize(hex_to_binary('00'*36))
      txinA.binScript = hex_to_binary('99'*4)
      txinA.intSeq  = hex_to_int('ff'*4)
      # test binary unpacker in unserialize
      testTxIn = PyTxIn().unserialize(txinA.serialize())
      self.assertEqual(txinA.getScript(), testTxIn.getScript())
      self.assertEqual(txinA.intSeq, testTxIn.intSeq)
      self.assertEqual(txinA.outpoint.txHash, testTxIn.outpoint.txHash)
      txoutA = PyTxOut()
      txoutA.value = 50 * ONE_BTC
      txoutA.binScript = '\x76\xa9\x14' + addrA.getAddr160() + '\x88\xac'
      # Test pprint
      print '\nTest pretty print PyTxIn, expect PrevTXHash all 0s'
      testTxIn.pprint()
   
      # test binary unpacker in unserialize
      testTxOut = PyTxOut().unserialize(txoutA.serialize())
      self.assertEqual(txoutA.getScript(), testTxOut.getScript())
      self.assertEqual(txoutA.value, testTxOut.getValue())
      # Test pprint
      print '\nTest pretty print PyTxOut'
      testTxOut.pprint()
      
      tx1 = PyTx()
      tx1.version    = 1
      tx1.numInputs  = 1
      tx1.inputs     = [txinA]
      tx1.numOutputs = 1
      tx1.outputs    = [txoutA]
      tx1.locktime   = 0
      tx1hash = tx1.getHash()
      recipientList = tx1.makeRecipientsList()
      self.assertEqual(len(recipientList), 1)
      self.assertEqual(recipientList[0][0], TXOUT_SCRIPT_STANDARD)
      self.assertEqual(recipientList[0][1], 50 * ONE_BTC)
      
      self.assertEqual(tx1.getHashHex(), binary_to_hex(tx1hash))
      # Creating transaction to send coins from A to B
      tx2 = PyCreateAndSignTx( [[ addrA, tx1, 0 ]],  [[addrB, 50*(10**8)]])
      psp = PyScriptProcessor()
      psp.setTxObjects(tx1, tx2, 0)
      self.assertTrue(psp.verifyTransactionValid())
      
   
   def testVerifyTxFromFakeBlockChain(self):
      psp = PyScriptProcessor()
      psp.setTxObjects(tx1Fake, tx2Fake, 0)
      self.assertTrue(psp.verifyTransactionValid())
      
   def test2of2MultiSigTx(self):
      tx1 = PyTx().unserialize(hex_to_binary('010000000189a0022c8291b4328338ec95179612b8ebf72067051de019a6084fb97eae0ebe000000004a4930460221009627882154854e3de066943ba96faba02bb8b80c1670a0a30d0408caa49f03df022100b625414510a2a66ebb43fffa3f4023744695380847ee1073117ec90cb60f2c8301ffffffff0210c18d0000000000434104a701496f10db6aa8acbb6a7aa14d62f4925f8da03de7f0262010025945f6ebcc3efd55b6aa4bc6f811a0dc1bbdd2644bdd81c8a63766aa11f650cd7736bbcaf8ac001bb7000000000043526b006b7dac7ca914fc1243972b59c1726735d3c5cca40e415039dce9879a6c936b7dac7ca914375dd72e03e7b5dbb49f7e843b7bef4a2cc2ce9e879a6c936b6c6ca200000000'))
      tx2 = PyTx().unserialize(hex_to_binary('01000000011c9608650a912be7fa88eecec664e6fbfa4b676708697fa99c28b3370005f32d01000000fd1701483045022017462c29efc9158cf26f2070d444bb2b087b8a0e6287a9274fa36fad30c46485022100c6d4cc6cd504f768389637df71c1ccd452e0691348d0f418130c31da8cc2a6e8014104e83c1d4079a1b36417f0544063eadbc44833a992b9667ab29b4ff252d8287687bad7581581ae385854d4e5f1fcedce7de12b1aec1cb004cabb2ec1f3de9b2e60493046022100fdc7beb27de0c3a53fbf96df7ccf9518c5fe7873eeed413ce17e4c0e8bf9c06e022100cc15103b3c2e1f49d066897fe681a12e397e87ed7ee39f1c8c4a5fef30f4c2c60141047cf315904fcc2e3e2465153d39019e0d66a8aaec1cec1178feb10d46537427239fd64b81e41651e89b89fefe6a23561d25dddc835395dd3542f83b32a1906aebffffffff01c0d8a700000000001976a914fc1243972b59c1726735d3c5cca40e415039dce988ac00000000'))
      # Verify 2-of-2 tx from Testnet
      psp = PyScriptProcessor()
      psp.setTxObjects(tx1, tx2, 0)
      self.assertTrue(psp.verifyTransactionValid())
      
   def test2of3MultiSigTx(self):
      tx1 = PyTx().unserialize(hex_to_binary('010000000371c06e0639dbe6bc35e6f948da4874ae69d9d91934ec7c5366292d0cbd5f97b0010000008a47304402200117cdd3ec6259af29acea44db354a6f57ac10d8496782033f5fe0febfd77f1b02202ceb02d60dbb43e6d4e03e5b5fbadc031f8bbb3c6c34ad307939947987f600bf01410452d63c092209529ca2c75e056e947bc95f9daffb371e601b46d24377aaa3d004ab3c6be2d6d262b34d736b95f3b0ef6876826c93c4077d619c02ebd974c7facdffffffffa65aa866aa7743ec05ba61418015fc32ecabd99886732056f1d4454c8f762bf8000000008c493046022100ea0a9b41c9372837e52898205c7bebf86b28936a3ee725672d0ca8f434f876f0022100beb7243a51fbc0997e55cb519d3b9cbd59f7aba68d80ba1e8adbb53443cda3c00141043efd1ca3cffc50638031281d227ff347a3a27bc145e2f846891d29f87bc068c27710559c4d9cd71f7e9e763d6e2753172406eb1ed1fadcaf9a8972b4270f05b4ffffffffd866d14151ee1b733a2a7273f155ecb25c18303c31b2c4de5aa6080aef2e0006000000008b483045022052210f95f6b413c74ce12cfc1b14a36cb267f9fa3919fa6e20dade1cd570439f022100b9e5b325f312904804f043d06c6ebc8e4b1c6cd272856c48ab1736b9d562e10c01410423fdddfe7e4d70d762dd6596771e035f4b43d54d28c2231be1102056f81f067914fe4fb6fd6e3381228ee5587ddd2028c846025741e963d9b1d6cf2c2dea0dbcffffffff0210ef3200000000004341048a33e9fd2de28137574cc69fe5620199abe37b7d08a51c528876fe6c5fa7fc28535f5a667244445e79fffc9df85ec3d79d77693b1f37af0e2d7c1fa2e7113a48acc0d454070000000061526b006b7dac7ca9143cd1def404e12a85ead2b4d3f5f9f817fb0d46ef879a6c936b7dac7ca9146a4e7d5f798e90e84db9244d4805459f87275943879a6c936b7dac7ca914486efdd300987a054510b4ce1148d4ad290d911e879a6c936b6c6ca200000000'))
      tx2 = PyTx().unserialize(hex_to_binary('01000000012f654d4d1d7246d1a824c5b6c5177c0b5a1983864579aabb88cabd5d05e032e201000000fda0014730440220151ad44e7f78f9e0c4a3f2135c19ca3de8dbbb7c58893db096c0c5f1573d5dec02200724a78c3fa5f153103cb46816df46eb6cfac3718038607ddec344310066161e01410459fd82189b81772258a3fc723fdda900eb8193057d4a573ee5ad39e26b58b5c12c4a51b0edd01769f96ed1998221daf0df89634a7137a8fa312d5ccc95ed8925483045022100ca34834ece5925cff6c3d63e2bda6b0ce0685b18f481c32e70de9a971e85f12f0220572d0b5de0cf7b8d4e28f4914a955e301faaaa42f05feaa1cc63b45f938d75d9014104ce6242d72ee67e867e6f8ec434b95fcb1889c5b485ec3414df407e11194a7ce012eda021b68f1dd124598a9b677d6e7d7c95b1b7347f5c5a08efa628ef0204e1483045022074e01e8225e8c4f9d0b3f86908d42a61e611f406e13817d16240f94f52f49359022100f4c768dd89c6435afd3834ae2c882465ade92d7e1cc5c2c2c3d8d25c41b3ea61014104ce66c9f5068b715b62cc1622572cd98a08812d8ca01563045263c3e7af6b997e603e8e62041c4eb82dfd386a3412c34c334c34eb3c76fb0e37483fc72323f807ffffffff01b0ad5407000000001976a9146a4e7d5f798e90e84db9244d4805459f8727594388ac00000000'))
      # Verify 2-of-3 tx from Testnet
      psp = PyScriptProcessor()
      psp.setTxObjects(tx1, tx2, 0)
      self.assertTrue(psp.verifyTransactionValid())
            
   def testMultiSig(self):
      tx1 = PyTx().unserialize(hex_to_binary('0100000001845ad165bdc0f9b5829cf5a594c4148dfd89e24756303f3a8dabeb597afa589b010000008b483045022063c233df8efa3d1885e069e375a8eabf16b23475ef21bdc9628a513ee4caceb702210090a102c7b602043e72b34a154d495ac19b3b9e42acb962c399451f2baead8f4c014104b38f79037ad25b84a564eaf53ede93dec70b35216e6682aa71a47cefa2996ec49acfbb0a8730577c62ef9a7cc20c740aaaaee75419bef9640a4216c2b49c42d3ffffffff02000c022900000000434104c08c0a71ccbe838403e3870aa1ab871b0ab3a6014b0ba41f6df2b9aefea73134ecaa0b27797620e402a33799e9047f86519d9e43bbd504cf753c293752933f4fac406f40010000000062537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953ae00000000'))
      tx2 = PyTx().unserialize(hex_to_binary('0100000001bb664ff716b9dfc831bcc666c1767f362ad467fcfbaf4961de92e45547daab8701000000fd190100493046022100d73f633f114e0e0b324d87d38d34f22966a03b072803afa99c9408201f6d6dc6022100900e85be52ad2278d24e7edbb7269367f5f2d6f1bd338d017ca460008776614401473044022071fef8ac0aa6318817dbd242bf51fb5b75be312aa31ecb44a0afe7b49fcf840302204c223179a383bb6fcb80312ac66e473345065f7d9136f9662d867acf96c12a42015241048c006ff0d2cfde86455086af5a25b88c2b81858aab67f6a3132c885a2cb9ec38e700576fd46c7d72d7d22555eee3a14e2876c643cd70b1b0a77fbf46e62331ac4104b68ef7d8f24d45e1771101e269c0aacf8d3ed7ebe12b65521712bba768ef53e1e84fff3afbee360acea0d1f461c013557f71d426ac17a293c5eebf06e468253e00ffffffff0280969800000000001976a9140817482d2e97e4be877efe59f4bae108564549f188ac7015a7000000000062537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953ae00000000'))
      # OP_CHECKMULTISIG from Testnet
      psp = PyScriptProcessor()
      psp.setTxObjects(tx1, tx2, 0)
      self.assertTrue(psp.verifyTransactionValid())
      
   def testMultiSigAddrExtraction(self):
      script1 = hex_to_binary('4104b54b5fc1917945fff64785d4baaca66a9704e9ed26002f51f53763499643321fbc047683a62be16e114e25404ce6ffdcf625a928002403402bf9f01e5cbd5f3dad4104f576e534f9bbf6d7c5f186ff4c6e0c5442c2755314bdee62fbc656f94d6cbf32c5eb3522da21cf9f954133000ffccb20dbfec030737640cc3315ce09619210d0ac')
      expectedBtcAddrList1 = ['1KmV9FdKJEFFCHydZUZGdBL9uKq2T9JUm8','13maaQeK5qSPjHwnHhwNUtNKruK3qYLwvv']              
      self.verifyMultiSigAddrExtraction(script1, expectedBtcAddrList1)
      
      script2 = hex_to_binary('537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953ae')
      expectedBtcAddrList2 = ['1ChwTs5Dmh6y9iDh4pjWyu2X6nAhjre7SV','1G2i31fxRqaoXBfYMuE4YKb9x96uYcHeQ','12Tg96ZPSYc3P2g5c9c4znFFH2whriN9NQ']
      self.verifyMultiSigAddrExtraction(script2, expectedBtcAddrList2)

      script3 = hex_to_binary('527a7651a269527a829178a914731cdb75c88a01cbb96729888f726b3b9f29277a879b69527a829178a914e9b4261c6122f8957683636548923acc069e8141879b6952ae')
      expectedBtcAddrList3 = ['1BVfH6iKT1s8fYEVSj39QkJrPqCKN4hv2m','1NJiFfFPZ177Pv96Yt4FCNZFEumyL2eKmt']
      self.verifyMultiSigAddrExtraction(script3, expectedBtcAddrList3)
   
   def verifyMultiSigAddrExtraction(self, scr, expectedBtcAddrList):
      addrList = getTxOutMultiSigInfo(scr)[1]
      btcAddrList = []
      for a in addrList:
         btcAddrList.append(PyBtcAddress().createFromPublicKeyHash160(a).getAddrStr())
      self.assertEqual(btcAddrList, expectedBtcAddrList)

   def testUnpackUnserializePyOutPoint(self):
      outpoint = PyOutPoint().unserialize(BinaryUnpacker(ALL_ZERO_OUTPOINT))
      self.assertEqual(outpoint.txHash, hex_to_binary('00'*32))
      self.assertEqual(outpoint.txOutIndex, 0)
   
   def testCopyPyOutPoint(self):
      outpoint = PyOutPoint().unserialize(BinaryUnpacker(ALL_ZERO_OUTPOINT))
      outpointCopy = outpoint.copy()
      self.assertEqual(outpoint.txHash, outpointCopy.txHash)
      self.assertEqual(outpoint.txOutIndex, outpointCopy.txOutIndex)
   
   def testPPrintPyOutPoint(self):
      # No return value - Should just print 0s
      outpoint = PyOutPoint().unserialize(BinaryUnpacker(ALL_ZERO_OUTPOINT))
      print "PyOutPoint PPrint Test. Expect all 0s: "
      outpoint.pprint()
   
   '''
   Does not pass because fromCpp is missing
   def testCreateCppFromCppPyOutPoint(self):
      outpoint = PyOutPoint().unserialize(BinaryUnpacker(ALL_ZERO_OUTPOINT))
      outpointFromCpp = PyOutPoint().fromCpp(outpoint.createCpp())
      self.assertEqual(outpoint.txHash, outpointFromCpp.txHash)
      self.assertEqual(outpoint.txOutIndex, outpointFromCpp.txOutIndex)
   '''
   def testBogusBlockComponent(self):
      class TestBlockComponent(BlockComponent):
         pass
      testBlkComp =  TestBlockComponent()
      self.assertRaises(NotImplementedError, testBlkComp.serialize)  
      self.assertRaises(NotImplementedError, testBlkComp.unserialize)  
   
   # TODO:  Add some tests for the OP_CHECKMULTISIG support in TxDP
   
   
if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()
