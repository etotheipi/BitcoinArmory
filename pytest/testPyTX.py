'''
Created on Aug 4, 2013

@author: Andy
'''
import sys
sys.path.append('..')
import unittest
from armoryengine.ArmoryUtils import hex_to_binary, binary_to_hex, hex_to_int, \
   ONE_BTC
from armoryengine.BinaryUnpacker import BinaryUnpacker
from armoryengine.Block import PyBlock
from armoryengine.PyBtcAddress import PyBtcAddress
from armoryengine.Script import PyScriptProcessor
from armoryengine.Transaction import PyTx, PyTxIn, PyOutPoint, PyTxOut, \
   PyCreateAndSignTx, getMultisigScriptInfo, BlockComponent,\
   PyCreateAndSignTx_old
from pytest.Tiab import TiabTest



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

multiTx1raw = hex_to_binary( \
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

multiTx2raw = hex_to_binary( \
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
hexBlock = ( \
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

class PyTXTest(TiabTest):
   
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
      self.assertEqual(recipientList[0][0], 0)
      self.assertEqual(recipientList[0][1], 50 * ONE_BTC)
      
      self.assertEqual(tx1.getHashHex(), binary_to_hex(tx1hash))
      # Creating transaction to send coins from A to B
      tx2 = PyCreateAndSignTx_old( [[ addrA, tx1, 0 ]],  [[addrB, 50*ONE_BTC]])
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
      
   '''
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
   '''
   
   def verifyMultiSigAddrExtraction(self, scr, expectedBtcAddrList):
      addrList = getMultisigScriptInfo(scr)[2]
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

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()
