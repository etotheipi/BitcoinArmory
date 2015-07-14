'''
Created on Aug 4, 2013

@author: Andy
'''
import sys
sys.path.append('..')
import unittest
from armoryengine.ALL import *
from armoryengine.Block import PyBlock


# Unserialize an reserialize
tx1raw = hex_to_binary(
   '01000000016290dce984203b6a5032e543e9e272d8bce934c7de4d15fa0fe44d'
   'd49ae4ece9010000008b48304502204f2fa458d439f957308bca264689aa175e'
   '3b7c5f78a901cb450ebd20936b2c500221008ea3883a5b80128e55c9c6070aa6'
   '264e1e0ce3d18b7cd7e85108ce3d18b7419a0141044202550a5a6d3bb81549c4'
   'a7803b1ad59cdbba4770439a4923624a8acfc7d34900beb54a24188f7f0a4068'
   '9d905d4847cc7d6c8d808a457d833c2d44ef83f76bffffffff0242582c0a0000'
   '00001976a914c1b4695d53b6ee57a28647ce63e45665df6762c288ac80d1f008'
   '000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00000000')
tx2raw = hex_to_binary(
   '0100000001f658dbc28e703d86ee17c9a2d3b167a8508b082fa0745f55be5144'
   'a4369873aa010000008c49304602210041e1186ca9a41fdfe1569d5d807ca7ff'
   '6c5ffd19d2ad1be42f7f2a20cdc8f1cc0221003366b5d64fe81e53910e156914'
   '091d12646bc0d1d662b7a65ead3ebe4ab8f6c40141048d103d81ac9691cf13f3'
   'fc94e44968ef67b27f58b27372c13108552d24a6ee04785838f34624b294afee'
   '83749b64478bb8480c20b242c376e77eea2b3dc48b4bffffffff0200e1f50500'
   '0000001976a9141b00a2f6899335366f04b277e19d777559c35bc888ac40aeeb'
   '02000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00000000')

multiTx1raw = hex_to_binary(
   '0100000004a14fd232f045f0c9f28c6848a22fee393152e901eaa61a9f18438b3ba05c6035010000008a47304402201b19808aa145dbebf775ed11a15d763eaa2'
   'b5df92b20f9835f62c72404918b1b02205aea3e816ac6ac7545254b9c34a00c37f20024793bbe0a64958934343f3c577b014104c0f3d0a4920bb6825769dd6ae1'
   'e36b0ac36581639d605241cdd548c4ef5d46cda5ac21723d478041a63118f192fdb730c4cf76106789824cd68879a7afeb5288ffffffffa14fd232f045f0c9f28'
   'c6848a22fee393152e901eaa61a9f18438b3ba05c6035000000008b4830450220796307d9787b892c8b1ada8511d99e855ea3099e1a76ce0f7aa783ed352a6e59'
   '022100fc38d05d7dfbe51e28c36d854dd0dcc938d60a3e406573c3dc39253694d14a12014104630aaf9d5c8d757cb5759428d4075911a2b2ff13dd7208ad7ea1d'
   '1682738a7138be93ee526c9d774e0dea03fa2a5fbb68043259ddfb942c0763f9b636b40c43fffffffffa14fd232f045f0c9f28c6848a22fee393152e901eaa61a'
   '9f18438b3ba05c6035020000008c493046022100cb423b63197ef3cdbfaed69f61aac59755f0025bd6d7a9d3c78024d897ebcf94022100f3ad14804a3c8042387'
   'eca9b9053abe99e12651a795cae7f546b08e1c08c6464014104649694df12dcd7fdb5a8c54c376b904bd7337891d865b8d306beb5d2e5d8fdf2a537d6f9df65ff'
   '44eb0b6042ebfdf9e338bff7f4afacb359dd6c71aea7b9b92dffffffffa14fd232f045f0c9f28c6848a22fee393152e901eaa61a9f18438b3ba05c60350300000'
   '08b483045022100fb9f4ddc68497a266362d489abf05184909a2b99aa64803061c88597b725877802207f39cf5a90a305aee45f365cf9e2d258e37cab4da6c123'
   'aa287635cd1fd40dd001410438252055130f3dd242201684931550c4065efc1b87c48192f75868f747e2a9df9a700fed7e90068bd395c58680bd593780c8119e7'
   '981dae08c345588f120fcb4ffffffff02e069f902000000001976a914ad00cf2b893e132c33a79a22ae938d6309c780a488ac80f0fa02000000001976a9143155'
   '18b646ea65ad148ee1e2f0360233617447e288ac00000000')

multiTx2raw = hex_to_binary(
   '0100000004a14fd232f045f0c9f28c6848a22fee393152e901eaa61a9f18438b3ba05c6035010000008a47304402201b19808aa145dbebf775ed11a15d763eaa2'
   'b5df92b20f9835f62c72404918b1b02205aea3e816ac6ac7545254b9c34a00c37f20024793bbe0a64958934343f3c577b014104c0f3d0a4920bb6825769dd6ae1'
   'e36b0ac36581639d605241cdd548c4ef5d46cda5ac21723d478041a63118f192fdb730c4cf76106789824cd68879a7afeb5288ffffffffa14fd232f045f0c9f28'
   'c6848a22fee393152e901eaa61a9f18438b3ba05c6035000000008b4830450220796307d9787b892c8b1ada8511d99e855ea3099e1a76ce0f7aa783ed352a6e59'
   '022100fc38d05d7dfbe51e28c36d854dd0dcc938d60a3e406573c3dc39253694d14a12014104630aaf9d5c8d757cb5759428d4075911a2b2ff13dd7208ad7ea1d'
   '1682738a7138be93ee526c9d774e0dea03fa2a5fbb68043259ddfb942c0763f9b636b40c43fffffffffa14fd232f045f0c9f28c6848a22fee393152e901eaa61a'
   '9f18438b3ba05c6035020000008c493046022100cb423b63197ef3cdbfaed69f61aac59755f0025bd6d7a9d3c78024d897ebcf94022100f3ad14804a3c8042387'
   'eca9b9053abe99e12651a795cae7f546b08e1c08c6464014104649694df12dcd7fdb5a8c54c376b904bd7337891d865b8d306beb5d2e5d8fdf2a537d6f9df65ff'
   '44eb0b6042ebfdf9e338bff7f4afacb359dd6c71aea7b9b92dffffffffa14fd232f045f0c9f28c6848a22fee393152e901eaa61a9f18438b3ba05c60350300000'
   '08c49304602220000fb9f4ddc68497a266362d489abf05184909a2b99aa64803061c88597b725877802207f39cf5a90a305aee45f365cf9e2d258e37cab4da6c123'
   'aa287635cd1fd40dd001410438252055130f3dd242201684931550c4065efc1b87c48192f75868f747e2a9df9a700fed7e90068bd395c58680bd593780c8119e7'
   '981dae08c345588f120fcb4ffffffff02e069f902000000001976a914ad00cf2b893e132c33a79a22ae938d6309c780a488ac80f0fa02000000001976a9143155'
   '18b646ea65ad148ee1e2f0360233617447e288ac00000000')

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

# I made these two tx in a fake blockchain... but they should still work
tx1Fake = PyTx().unserialize(hex_to_binary( (
   '01000000 0163451d 1002611c 1388d5ba 4ddfdf99 196a86b5 990fb5b0 dc786207'
   '4fdcb8ee d2000000 004a4930 46022100 cb02fb5a 910e7554 85e3578e 6e9be315'
   'a161540a 73f84ee6 f5d68641 925c59ac 0221007e 530a1826 30b50e2c 12dd09cd'
   'ebfd809f 038be982 bdc2c7e9 d4cbf634 9e088d01 ffffffff 0200ca9a 3b000000'
   '001976a9 14cb2abd e8bccacc 32e893df 3a054b9e f7f227a4 ce88ac00 286bee00'
   '00000019 76a914ee 26c56fc1 d942be8d 7a24b2a1 001dd894 69398088 ac000000'
   '00'                                                                     ).replace(' ','')))

tx2Fake = PyTx().unserialize(hex_to_binary( (
   '01000000 01a5b837 da38b64a 6297862c ba8210d0 21ac59e1 2b7c6d7e 70c355f6'
   '972ee7a8 6e010000 008c4930 46022100 89e47100 d88d5f8c 8f62a796 dac3afb8'
   'f090c6fc 2eb0c4af ac7b7567 3a364c01 0221002b f40e554d ae51264b 0a86df17'
   '3e45756a 89bbd302 4f166cc4 2cfd1874 13636901 41046868 0737c76d abb801cb'
   '2204f57d be4e4579 e4f710cd 67dc1b42 27592c81 e9b5cf02 b5ac9e8b 4c9f49be'
   '5251056b 6a6d011e 4c37f6b6 d17ede6b 55faa235 19e2ffff ffff0100 286bee00'
   '00000019 76a914c5 22664fb0 e55cdc5c 0cea73b4 aad97ec8 34323288 ac000000'
   '00'                                                                     ).replace(' ','')))

ALL_ZERO_OUTPOINT = hex_to_binary('00' * 36)

class mockUTXO(object):

   def __init__(self, txhash, outindex):
      self.txhash = hex_to_binary(txhash)
      self.outindex = outindex

   def getTxHash(self):
      return self.txhash

   def getTxOutIndex(self):
      return self.outindex


class PyTXTest(unittest.TestCase):
   
   def setUp(self):
      useMainnet()

   def testMinimizeDERSignaturePadding(self):
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
      prvA = SecureBinaryData('\xaa' * 32)
      addrA = ArmoryImportedKeyPair()
      addrA.initializeFromPrivKey(prvA)
      prvB = SecureBinaryData('\xbb' * 32)
      addrB = ArmoryImportedKeyPair()
      addrB.initializeFromPrivKey(prvB)

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
      self.assertEqual(recipientList[0][0], 0)
      self.assertEqual(recipientList[0][1], 50 * ONE_BTC)
      
      self.assertEqual(tx1.getHashHex(), binary_to_hex(tx1hash))
      # Creating transaction to send coins from A to B
      pubKeyMap = { addrA.getScrAddr(): addrA.sbdPublicKey33.toBinStr() }
      ustxi = UnsignedTxInput(tx1.serialize(), 0, pubKeyMap=pubKeyMap)
      script = scrAddr_to_script(addrB.getScrAddr())
      dtxo = DecoratedTxOut(script, 50*ONE_BTC)
      tx2 = PyCreateAndSignTx( [ustxi], [dtxo], [addrA])
      psp = PyScriptProcessor()
      psp.setTxObjects(tx1, tx2, 0)
      self.assertTrue(psp.verifyTransactionValid())
      
   
   def testVerifyTxFromFakeBlockChain(self):
      psp = PyScriptProcessor()
      psp.setTxObjects(tx1Fake, tx2Fake, 0)
      self.assertTrue(psp.verifyTransactionValid())
      
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
   
   def testBogusBlockComponent(self):
      class TestBlockComponent(BlockComponent):
         pass
      testBlkComp =  TestBlockComponent()
      self.assertRaises(NotImplementedError, testBlkComp.serialize)  
      self.assertRaises(NotImplementedError, testBlkComp.unserialize)  

   def testDeterministicTxOrdering(self):
      rawIns = [ 
         ("0e53ec5dfb2cb8a71fec32dc9a634a35b7e24799295ddd5278217822e0b31f57",0),
         ("26aa6e6d8b9e49bb0630aac301db6757c02e3619feb4ee0eea81eb1672947024",1),
         ("28e0fdd185542f2c6ea19030b0796051e7772b6026dd5ddccd7a2f93b73e6fc2",0),
         ("381de9b9ae1a94d9c17f6a08ef9d341a5ce29e2e60c36a52d333ff6203e58d5d",1),
         ("3b8b2f8efceb60ba78ca8bba206a137f14cb5ea4035e761ee204302d46b98de2",0),
         ("402b2c02411720bf409eff60d05adad684f135838962823f3614cc657dd7bc0a",1),
         ("54ffff182965ed0957dba1239c27164ace5a73c9b62a660c74b7b7f15ff61e7a",1),
         ("643e5f4e66373a57251fb173151e838ccd27d279aca882997e005016bb53d5aa",0),
         ("6c1d56f31b2de4bfc6aaea28396b333102b1f600da9c6d6149e96ca43f1102b1",1),
         ("7a1de137cbafb5c70405455c49c5104ca3057a1f1243e6563bb9245c9c88c191",0),
         ("7d037ceb2ee0dc03e82f17be7935d238b35d1deabf953a892a4507bfbeeb3ba4",1),
         ("a5e899dddb28776ea9ddac0a502316d53a4a3fca607c72f66c470e0412e34086",0),
         ("b4112b8f900a7ca0c8b0e7c4dfad35c6be5f6be46b3458974988e1cdb2fa61b8",0),
         ("bafd65e3c7f3f9fdfdc1ddb026131b278c3be1af90a4a6ffa78c4658f9ec0c85",0),
         ("de0411a1e97484a2804ff1dbde260ac19de841bebad1880c782941aca883b4e9",1),
         ("f0a130a84912d03c1d284974f563c5949ac13f8342b8112edff52971599e6a45",0),
         ("f320832a9d2e2452af63154bc687493484a0e7745ebd3aaf9ca19eb80834ad60",0),
      ]
      rawOuts = [
         ("76a9144a5fba237213a062f6f57978f796390bdcf8d01588ac", 400057456),
         ("76a9145be32612930b8323add2212a4ec03c1562084f8488ac", 40000000000),
      ]
      ins = [mockUTXO(*x) for x in rawIns]
      outs = [(hex_to_binary(x[0]), x[1]) for x in rawOuts]
      setDeterministicTxOrderingFlag(False)
      reorderInputsAndOutputs(ins, outs)
      for i, inp in enumerate(ins):
         if binary_to_hex(inp.getTxHash()) != rawIns[i][0]:
            break
      else:
         self.assertTrue(False)

      setDeterministicTxOrderingFlag(True)
      reorderInputsAndOutputs(ins, outs)
      for i, inp in enumerate(ins):
         self.assertEqual(binary_to_hex(inp.getTxHash()), rawIns[i][0])
      for i, out in enumerate(outs):
         self.assertEqual(binary_to_hex(out[0]), rawOuts[i][0])
      setDeterministicTxOrderingFlag(False)
   
   # TODO:  Add some tests for the OP_CHECKMULTISIG support in TxDP
