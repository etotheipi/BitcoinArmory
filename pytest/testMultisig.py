'''
Created on Aug 4, 2013

@author: Andy
'''
import sys
import textwrap
sys.path.append('..')
#from pytest.Tiab import TiabTest
import unittest
from armoryengine.ArmoryUtils import *
from armoryengine.Transaction import PyTx, UnsignedTxInput, DecoratedTxOut,\
   UnsignedTransaction, TXIN_SIGSTAT, NullAuthData
from armoryengine.Script import convertScriptToOpStrings
from armoryengine.MultiSigUtils import calcLockboxID, computePromissoryID, \
   MultiSigLockbox, MultiSigPromissoryNote, DecoratedPublicKey



def normalizeAddrStr(astr):
   """
   This extracts the addr160 from the address string (which is network-
   independent), and then recreates the addrStr which will use the
   currently-enabled network byte (mainnet, testnet, whatevernet)
   """
   if checkAddrType==-1:
      raise BadAddressError('Invalid address string (bad checksum)')

   return hash160_to_addrStr(base58_to_binary(astr)[1:21])


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

class MSUtilsTest(unittest.TestCase):

   
   def setUp(self):
      self.tx1 = PyTx().unserialize(tx1raw)
      self.tx2 = PyTx().unserialize(tx2raw)
      self.tx1hash = hex_to_binary( \
         'aa739836a44451be555f74a02f088b50a867b1d3a2c917ee863d708ec2db58f6', BIGENDIAN)
      self.tx2hash = hex_to_binary( \
         '9072559e9e2772cd6ac88683531a512cba6c2fee82b2476ed5e84c24abe5f526', BIGENDIAN)
   
      self.pubKey = hex_to_binary( \
         '048d103d81ac9691cf13f3fc94e44968ef67b27f58b27372c13108552d24a6ee04'
           '785838f34624b294afee83749b64478bb8480c20b242c376e77eea2b3dc48b4b')
      self.sigStr  = hex_to_binary( \
         '304602210041e1186ca9a41fdfe1569d5d807ca7ff'
         '6c5ffd19d2ad1be42f7f2a20cdc8f1cc0221003366b5d64fe81e53910e156914'
         '091d12646bc0d1d662b7a65ead3ebe4ab8f6c4' + '01')


      # Specify the target addresses as testnet addrStrs, but the "normalize"
      # method will convert it to the correct addrStr for mainnet or testnet
      self.addrStr1 = normalizeAddrStr('mhyjJTq9RsDfhNdjTkga1CKhTiL5VFw85J')
      self.addrStr2 = normalizeAddrStr('mgoCqfR25kZVApAGFK3Tx5CTNcCppmKwfb')

   
   def tearDown(self):
      pass
   

   def testUSTXI_serialize_roundtrip(self):
      ustxi = UnsignedTxInput(tx1raw, 1,  None, self.pubKey)

      serUSTXI = ustxi.serialize()
      ustxi2 = UnsignedTxInput().unserialize(serUSTXI)
      self.assertEqual(serUSTXI, ustxi2.serialize())


   def testUSTXI_addSignature(self):
      # We can check all the signature handling stuff without the private key,
      # because Tx2 is a full tx with a valid signature.  So we can pretende 
      # Tx2 is unsigned, and that we are supplying sigStr as one of (the only)
      # signature that will be needed to finish the UnsignedTransaction
      ustxi = UnsignedTxInput(tx1raw, 1,  None, self.pubKey)

      # Try once with provided pub key
      self.assertTrue(ustxi.verifyTxSignature(self.tx2, self.sigStr, self.pubKey))

      # Try the recursive method
      self.assertTrue(ustxi.verifyTxSignature(self.tx2, self.sigStr))

      # Try inserting the signature into USTXI then verify all
      ustxi.setSignature(0, self.sigStr)
      self.assertTrue(ustxi.verifyAllSignatures(self.tx2))

      # Try a bad signature
      badSig = self.sigStr[:16] + '\x00'*8 + self.sigStr[24:]
      self.assertFalse(ustxi.verifyTxSignature(self.tx2, badSig))
      


   def testDTXO(self):
      a160_1 = addrStr_to_hash160(self.addrStr1)[1]
      a160_2 = addrStr_to_hash160(self.addrStr2)[1]
      dtxo1 = DecoratedTxOut(hash160_to_p2pkhash_script(a160_1), long(1.00*ONE_BTC))
      dtxo2 = DecoratedTxOut(hash160_to_p2pkhash_script(a160_2), long(0.49*ONE_BTC))

      serDTXO1 = dtxo1.serialize()
      dtxo1_dup = DecoratedTxOut().unserialize(serDTXO1)
      self.assertEqual(serDTXO1,  dtxo1_dup.serialize())

      serDTXO2 = dtxo2.serialize()
      dtxo2_dup = DecoratedTxOut().unserialize(serDTXO2)
      self.assertEqual(serDTXO2,  dtxo2_dup.serialize())


   # not a real test
   """
   def testPprintTxInSignStat(self):
      ustxi = UnsignedTxInput(tx1raw, 1,  None, self.pubKey)
      sigstat = ustxi.evaluateSigningStatus()
      sigstat.pprint()
   """
      

   # not a real test
   def testUnsignedTx(self):
      ustxi = UnsignedTxInput(tx1raw, 1,  None, self.pubKey)
      a160_1 = addrStr_to_hash160(self.addrStr1)[1]
      a160_2 = addrStr_to_hash160(self.addrStr2)[1]
      dtxo1 = DecoratedTxOut(hash160_to_p2pkhash_script(a160_1), long(1.00*ONE_BTC))
      dtxo2 = DecoratedTxOut(hash160_to_p2pkhash_script(a160_2), long(0.49*ONE_BTC))

      ustx = UnsignedTransaction().createFromUnsignedTxIO([ustxi], [dtxo1,dtxo2])

      self.assertEqual(len(ustx.ustxInputs),  1)
      self.assertEqual(len(ustx.decorTxOuts), 2)
      self.assertEqual(ustx.lockTime, 0)
      self.assertEqual(ustx.uniqueIDB58,  'J2mRenD7')

      serUstx = ustx.serialize()
      ustx2 = UnsignedTransaction().unserialize(serUstx)
      self.assertEqual(serUstx, ustx2.serialize())

      serUstxASCII = ustx.serializeAscii()
      ustx2 = UnsignedTransaction().unserializeAscii(serUstxASCII)
      self.assertEqual(serUstx, ustx2.serialize())
      #print '' 
      #print 'Sample TxSigCollect Block:'
      #print serUstxASCII
      #ustx.pprint()
      #print '\n'
      #ustx.evaluateSigningStatus().pprint()

   def testAddSigToUSTX(self):
      ustxi = UnsignedTxInput(tx1raw, 1,  None, self.pubKey)
      a160_1 = addrStr_to_hash160(self.addrStr1)[1]
      a160_2 = addrStr_to_hash160(self.addrStr2)[1]
      dtxo1 = DecoratedTxOut(hash160_to_p2pkhash_script(a160_1), long(1.00*ONE_BTC))
      dtxo2 = DecoratedTxOut(hash160_to_p2pkhash_script(a160_2), long(0.49*ONE_BTC))

      ustx = UnsignedTransaction().createFromUnsignedTxIO([ustxi], [dtxo1,dtxo2])

      msIndex = ustx.insertSignatureForInput(0, self.sigStr, self.pubKey)
      self.assertEqual(msIndex, 0)

      msIndex = ustx.insertSignatureForInput(0, self.sigStr)
      self.assertEqual(msIndex, 0)

      badSig = self.sigStr[:16] + '\x00'*8 + self.sigStr[24:]
      msIndex = ustx.insertSignatureForInput(0, badSig)
      self.assertEqual(msIndex, -1)



   def testCreateMultisigTests(self):
      '''
      This is used solely to generate some multi-sig scripts, using known
      public/private keys, that we can then use to test signing, etc.  This
      test doesn't actually test anything, but could be tweaked and then 
      reenabled to produce new data for new tests
      '''


      asc_nosig = textwrap.dedent("""
         =====TXSIGCOLLECT-5JxmLy4T======================================================
         AQAAAAsRCQcAAAAAAf19AQEAAAALEQkH/XsoFKgwJMVZsviXpv+aOun4BQHRm+Cuvs/X7O/J3n8BAAAA
         /QMBAQAAAAGcgxlJ0d+ZHi+MzG+laL4qTx/jVH/lPbbKmrGLA1oc8AAAAACMSTBGAiEArOklwdcihg72
         fMu+GvnKF+AdFiMmeT7CWV4KMZmA3kcCIQDyjBMqkI6tFVXMG/yhbBhVg7TNYsAGLjM5UWLfVx57WgFB
         BLmTMVBhjWo901GrcZzZMNBUectdX4ZsVyHhMNjZpaAJxlpQqnjiK9PAvrNqOIgMq8itz9S3KDaOs/Kh
         W6/lJNL/////AsAOFgIAAAAAGXapFInbjSGPxqYLm35NTXhzcAkVf8h8iKwwq98DAAAAABl2qRSBj0Gs
         NlhCyvZkoRO2iRw54544foisAAAAAAAA/////wFBBJ6i78WXHp6ywhTupFpF7A0V2jwQEjE9pWO1+7wZ
         qS+IM59Dur1Ut5OC+yUycjeFHQdqemkBDFT97zMCJalmtXwAAALiAQAAAAsRCQfJUkEEagSrmNnkd0rY
         BuMC3d62O+oWtctfIj7ndHjoYbtYPrM2tvvLYLWz1PFVGsReX/xJNkZufZj2x8Dsc2U590aRpkEEaGgH
         N8dtq7gByyIE9X2+TkV55PcQzWfcG0InWSyB6bXPArWsnotMn0m+UlEFa2ptAR5MN/a20X7ea1X6ojUZ
         4kEEuVwknYT0F+PjlaEnQlQotUBnHMFYgeuCjBe3IqU/xZniHKXlbJDzQJiNOTOsx2vrgy/WTKsHjd88
         5zKSMDHRqFOuoH+IAgAAAAAAAAROT05FADIBAAAACxEJBxl2qRRs7kd5CHIvdApqfOmMDp1dyrD6Mois
         gARXAQAAAAAAAAROT05FAA==
         ================================================================================
         """.strip())


      asc_sig = textwrap.dedent("""
         =====TXSIGCOLLECT-5JxmLy4T======================================================
         AQAAAAsRCQcAAAAAAf3EAQEAAAALEQkH/XsoFKgwJMVZsviXpv+aOun4BQHRm+Cuvs/X7O/J3n8BAAAA
         /QMBAQAAAAGcgxlJ0d+ZHi+MzG+laL4qTx/jVH/lPbbKmrGLA1oc8AAAAACMSTBGAiEArOklwdcihg72
         fMu+GvnKF+AdFiMmeT7CWV4KMZmA3kcCIQDyjBMqkI6tFVXMG/yhbBhVg7TNYsAGLjM5UWLfVx57WgFB
         BLmTMVBhjWo901GrcZzZMNBUectdX4ZsVyHhMNjZpaAJxlpQqnjiK9PAvrNqOIgMq8itz9S3KDaOs/Kh
         W6/lJNL/////AsAOFgIAAAAAGXapFInbjSGPxqYLm35NTXhzcAkVf8h8iKwwq98DAAAAABl2qRSBj0Gs
         NlhCyvZkoRO2iRw54544foisAAAAAAAA/////wFBBJ6i78WXHp6ywhTupFpF7A0V2jwQEjE9pWO1+7wZ
         qS+IM59Dur1Ut5OC+yUycjeFHQdqemkBDFT97zMCJalmtXxHMEQCIF12j4Vj1Shf49BkDWwVzf1kRgYr
         4EIPObgRTVPQz2KkAiAQ28gOniv2A5ozeBCk/rpWHTw2DqqkraEUDYLAPr83NQEAAuIBAAAACxEJB8lS
         QQRqBKuY2eR3StgG4wLd3rY76ha1y18iPud0eOhhu1g+sza2+8tgtbPU8VUaxF5f/Ek2Rm59mPbHwOxz
         ZTn3RpGmQQRoaAc3x22ruAHLIgT1fb5ORXnk9xDNZ9wbQidZLIHptc8Ctayei0yfSb5SUQVram0BHkw3
         9rbRft5rVfqiNRniQQS5XCSdhPQX4+OVoSdCVCi1QGccwViB64KMF7cipT/FmeIcpeVskPNAmI05M6zH
         a+uDL9ZMqweN3zznMpIwMdGoU66gf4gCAAAAAAAABE5PTkUAMgEAAAALEQkHGXapFGzuR3kIci90Cmp8
         6YwOnV3KsPoyiKyABFcBAAAAAAAABE5PTkUA
         ================================================================================
         """.strip())


      # For this manual construction to work, I had to save the signed funding
      # transaction
      signedFundMS = hex_to_binary( \
         '0100000001fd7b2814a83024c559b2f897a6ff9a3ae9f80501d19be0aebecfd7'
         'ecefc9de7f010000008a47304402205d768f8563d5285fe3d0640d6c15cdfd64'
         '46062be0420f39b8114d53d0cf62a4022010dbc80e9e2bf6039a337810a4feba'
         '561d3c360eaaa4ada1140d82c03ebf37350141049ea2efc5971e9eb2c214eea4'
         '5a45ec0d15da3c1012313da563b5fbbc19a92f88339f43babd54b79382fb2532'
         '7237851d076a7a69010c54fdef330225a966b57cffffffff02a07f8802000000'
         '00c95241046a04ab98d9e4774ad806e302dddeb63bea16b5cb5f223ee77478e8'
         '61bb583eb336b6fbcb60b5b3d4f1551ac45e5ffc4936466e7d98f6c7c0ec7365'
         '39f74691a6410468680737c76dabb801cb2204f57dbe4e4579e4f710cd67dc1b'
         '4227592c81e9b5cf02b5ac9e8b4c9f49be5251056b6a6d011e4c37f6b6d17ede'
         '6b55faa23519e24104b95c249d84f417e3e395a127425428b540671cc15881eb'
         '828c17b722a53fc599e21ca5e56c90f340988d3933acc76beb832fd64cab078d'
         'df3ce732923031d1a853ae80045701000000001976a9146cee477908722f740a'
         '6a7ce98c0e9d5dcab0fa3288ac00000000')
     
      #UnsignedTransaction().unserializeAscii(asc_nosig).evaluateSigningStatus().pprint()
      #UnsignedTransaction().unserializeAscii(asc_sig).evaluateSigningStatus().pprint()

   
      privKeys = [SecureBinaryData(a*32) for a in ['\xaa','\xbb','\xcc']]
      pubKeys  = [CryptoECDSA().ComputePublicKey(prv) for prv in privKeys]
      pubStrs  = [pubk.toBinStr() for pubk in pubKeys]

      #for i,prv in enumerate(privKeys):
         #print 'PrivKey %d:', prv.toHexStr()

      msScript = pubkeylist_to_multisig_script(pubStrs, 2)
      msScriptReverse = pubkeylist_to_multisig_script(pubStrs[::-1], 2)
      self.assertEqual(msScript, msScriptReverse)
      
      #for opStr in convertScriptToOpStrings(msScript):
         #print '   ', opStr

      dtxo = DecoratedTxOut(msScript, 1.0*ONE_BTC)

   
      ustxi = UnsignedTxInput(signedFundMS, 0)
      #ustxi.pprint()

      refund1 = addrStr_to_scrAddr(normalizeAddrStr('mqSvihZRtKt1J3EBbwBJSHeAYVjdxUnpvf'))
      refund2 = addrStr_to_scrAddr(normalizeAddrStr('mjAauu6jzmYaE7jrfFgKqLxtvpStmPxcb7'))
      dtxo1 = DecoratedTxOut(scrAddr_to_script(refund1), long(0.223*ONE_BTC))
      dtxo2 = DecoratedTxOut(scrAddr_to_script(refund2), long(0.200*ONE_BTC))

      ustx = UnsignedTransaction().createFromUnsignedTxIO([ustxi], [dtxo1, dtxo2])
      #ustx.pprint()
      #ustx.evaluateSigningStatus().pprint()


      # Need a candidate tx to test signing
      txObj = ustx.pytxObj
      
      # Test signing on the individual USTXI
      NOSIG = TXIN_SIGSTAT.NO_SIGNATURE
      SIG   = TXIN_SIGSTAT.ALREADY_SIGNED
      for i in [0,1]:
         for j in [0,1]:
            for k in [0,1]:
               ustxiCopy = UnsignedTxInput().unserialize(ustxi.serialize())
               if i>0: ustxiCopy.createAndInsertSignature(txObj, privKeys[0])
               if j>0: ustxiCopy.createAndInsertSignature(txObj, privKeys[1])
               if k>0: ustxiCopy.createAndInsertSignature(txObj, privKeys[2])
               sstat = ustxiCopy.evaluateSigningStatus()
               #sstat.pprint()
               self.assertEqual(sstat.allSigned, (i+j+k)>1)
               self.assertEqual(sstat.statusM[0], NOSIG if i+j+k==0 else SIG)
               self.assertEqual(sstat.statusM[1], NOSIG if i+j+k<2  else SIG)
                  
      
      # Now try all this on the full USTX (not just the input
      for i in [0,1]:
         for j in [0,1]:
            for k in [0,1]:
               ustxCopy = UnsignedTransaction().unserialize(ustx.serialize())
               if i>0: ustxCopy.createAndInsertSignatureForInput(0, privKeys[0])
               if j>0: ustxCopy.createAndInsertSignatureForInput(0, privKeys[1])
               if k>0: ustxCopy.createAndInsertSignatureForInput(0, privKeys[2])
               sstat = ustxCopy.evaluateSigningStatus()
               #sstat.pprint()
               self.assertEqual(sstat.canBroadcast, (i+j+k)>1)
               #self.assertEqual(sstat.statusM[0], NOSIG if i+j+k==0 else SIG)
               #self.assertEqual(sstat.statusM[1], NOSIG if i+j+k<2  else SIG)
      
      # Now actually sign it and dump out a raw signed tx!
      ustx.createAndInsertSignatureForInput(0, privKeys[0])
      ustx.createAndInsertSignatureForInput(0, privKeys[2])

      #print ustx.serializeAscii()
      #print binary_to_hex(ustx.getPyTxSignedIfPossible().serialize())
      

################################################################################
# This class tests all Round Trip operations, plus other tests that involve
# Lockbox Related Objects
# There are 6 objects that are tested for at least round trip operations
#    Decorated Public Key
#    Lockbox
#    Promisory Note
#    Unsigned Transaction
#    Unsigned Transaction Input
#    Decorated Transaction Output
class LockboxRelatedObjectsTest(unittest.TestCase):
   @classmethod
   def setUpClass(self):
      global serMap
      # We have 6 classes to test, but USTXI and DTXO can use the USTX data
      serMap = {}
      serMap['dpk']      = {}
      serMap['lockbox']  = {}
      serMap['promnote'] = {}
      serMap['ustx']     = {}

      
      serMap['dpk']['nocomment'] = textwrap.dedent("""
         =====PUBLICKEY-mqQQMsTsUyGJ=====================================================
         AQAAAAsRCQdBBPXISLf5jl7LafjFYbMVfb+OqjzMD8XGVyBauZ1kNA/tMGoZn5lHdfZRVcNN8D9+9vG9
         GpvTn9PUWZ1uETTewPIAAAAA
         ================================================================================
         """.strip())

      serMap['dpk']['wcomment'] = textwrap.dedent("""
         =====PUBLICKEY-mqjMCZC4BFRm=====================================================
         AQAAAAsRCQdBBCMhT2Hr0mjRkNu+VR+JFRczrwE+E+Fbzd5l/XNCHJC6i62liVEVRnasthYQCjiFsv2y
         Yw9HN6LxwO6+eQeBKQEcdGhpcyBpcyBhIHVzZWxlc3MgY29tbWVudCFAIQAAAA==
         ================================================================================
         """.strip())

      serMap['lockbox']['nocomments'] = textwrap.dedent("""
         =====LOCKBOX-7mtvkCTa===========================================================
         AQAAAAsRCQclhKNTAAAAAAtTYW1wbGUgMm9mMwACA04BAAAACxEJB0EEIyFPYevSaNGQ275VH4kVFzOv
         AT4T4VvN3mX9c0IckLqLraWJURVGdqy2FhAKOIWy/bJjD0c3ovHA7r55B4EpAQAAAABOAQAAAAsRCQdB
         BMWU5+Df9QeQfI0i+TRNXiImnOGzoIAyVGKhEpa20uN95t7eEN+gOaippJmGbFxQew0C1LTqlUn4C4oa
         NIwDkroAAAAATgEAAAALEQkHQQTOFdjRK/2+hr00V4iRFlzDXMS0Ll3fT+qJ9YSH519IUTsIvhQenODR
         MReXXbfJmcCxUPg3N2TQvLX7iI2GRo2jAAAAAA==
         ================================================================================
         """.strip())

      serMap['lockbox']['nometadata'] = textwrap.dedent("""
         =====LOCKBOX-7mtvkCTa===========================================================
         AQAAAAsRCQclhKNTAAAAAAtTYW1wbGUgMm9mMwACA2ABAAAACxEJB0EEIyFPYevSaNGQ275VH4kVFzOv
         AT4T4VvN3mX9c0IckLqLraWJURVGdqy2FhAKOIWy/bJjD0c3ovHA7r55B4EpARJLZXkgIzEgaW4gdGhl
         IGxpc3QAAABWAQAAAAsRCQdBBMWU5+Df9QeQfI0i+TRNXiImnOGzoIAyVGKhEpa20uN95t7eEN+gOaip
         pJmGbFxQew0C1LTqlUn4C4oaNIwDkroIS2V5ICMyISAAAABkAQAAAAsRCQdBBM4V2NEr/b6GvTRXiJEW
         XMNcxLQuXd9P6on1hIfnX0hROwi+FB6c4NExF5ddt8mZwLFQ+Dc3ZNC8tfuIjYZGjaMWS2V5IHdpdGgg
         dW5pY29kZSBkYXRhIQAAAA==
         ================================================================================
         """.strip())



      serMap['promnote']['regular'] = textwrap.dedent("""
         =====PROMISSORY-CerrVYjD========================================================
         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
         IHRlc3RpbmcgY29tbWVudAA=
         ================================================================================
         """.strip())


      serMap['promnote']['regular'] = textwrap.dedent("""
         =====PROMISSORY-GVfKYBqK========================================================
         AQAAAAsRCQcyAQAAAAsRCQcXqRSUFt7Fp83rejuvC6FPeHUyzH6RQodQNHQCAAAAAAAABE5PTkUAAAAA
         AAAAAAAAAAAB/YMBAQAAAAsRCQdKjCQZ04S5mekJ7FSvGyohppsRllgQ1lF0D/ewX9Ls6AAAAAD9AAEB
         AAAAATS/9KXacFYJPYQCoSkRSIKYDIIgQ6wZzEdgiipEAVbuAAAAAItIMEUCIE9MTdfNrRrMW8BFe8uC
         N34DMz3wYa+KL6bPkxNpgDUnAiEAnfZxXXfhAdF435vRb1kWxg65NbMAHfbX/bDh9iXQNKYBQQRBul/I
         mA3bgs0PGSJFd3KeQPBPp9LYuduFgnfA+kEKf1GZI4s+EGuxDHvjZoNBwYvWPEgtqYVxvybEXWHwhhou
         /////wJQNHQCAAAAABl2qRSSFcygbZulF1EFISvxCYhFoLBf44isAC0xAQAAAAAXqRSUFt7Fp83rejuv
         C6FPeHUyzH6RQocAAAAAAAhHVmZLWUJxSwD/////AUEEBgLRFKodcJB0fSX3gNeaAM7uNQNM/tL8RcBZ
         4+5P1i6RbjURO9yt34sF0flB8XbiR/T/cUqkn66p/S/Ww3FKEwAAJkR1bXBpbmcgYWxsIG15IGNhc2gg
         aW50byB0aGlzIGRvbmF0aW9uAA==
         ================================================================================
         """.strip())
         

      # These will be used for all USTX, USTXI and DTXO
      serMap['ustx']['regular'] = textwrap.dedent("""
         =====TXSIGCOLLECT-8rgLHcFg======================================================
         AQAAAAsRCQcAAAAAAv3EAQEAAAALEQkHc4uuUlna6Cw/HRowBY70IQ52kRVtRw8FNAIkl8SsT7kBAAAA
         /QIBAQAAAAEXA5J+qKVnY8IE4dDBE58Pyp+q1uA/RBkeol1FLLoZFQAAAACLSDBFAiEA0dB7emFmICZD
         NecZeg7eRzjjOKTmg+EZLXca14dg1uYCIBDnAgPWPSMmwaK5ZWpTeCuhn86qDh1KyP87cglKYhWdAUEE
         UtPQusiUYHM/ECQT0yg2oqwdYUsUmer4RyxxD0lxRei8AceGdrnDC5uL/Y6kzW3rQxynEVXBGJI01Qkk
         1frDLP////8CMBsPAAAAAAAZdqkUOW5GJnPKcmK1r9T5oiPKqWm0HSGIrICWmAAAAAAAGXapFHAJXqNd
         6fuLln4Tkl6tDx7sbO/giKwAAAAAAAAA/////wFBBCMhT2Hr0mjRkNu+VR+JFRczrwE+E+Fbzd5l/XNC
         HJC6i62liVEVRnasthYQCjiFsv2yYw9HN6LxwO6+eQeBKQFHMEQCIFlfw+VSIaBS6vDXbs093+fNaFJb
         3GidWizy+UUAhHXZAiAXwqBQPrg2zXMo/VOkEpKlHAHccv2/laZJdwRCE+BnAgEA/ZoCAQAAAAsRCQcR
         yZHa7iCRLwdDH0oHdiOvbDVj5cDoexX5HK0fFh8RvAIAAAD91wEBAAAAAqSzhO8p2UlTYZbBtnV3nyrq
         rfShMZfzDpIdLcm6AQPzAQAAAItIMEUCIQCREoEDVTRz2WqLHbLnDYKpTUhgufQ7je76GxYCyppdGAIg
         HEhwzPsLCdraLY/mBMqotfTE6SPowHeo6LFuH9GYX00BQQRWZgMKp8HBmppMCu35YERTSJSu4EO99s/R
         Q3+jtZINL8XO1XY1S8UM7/ajjM6Wv3g45bGjATcKtGwqhAlIWl1e/////yvlXmEhjTLSBnhishefOy0R
         ldxN3AlytJ2VYlYq1inMAQAAAIxJMEYCIQDqUpfjjR1xuMh2/7cXzSh7cZXOBM0IxpKEaSrXDKvdEgIh
         AKwM/OsjuRcgq6KXyZ0swmVx8o/dGgbCPYCkj2ZI4wweAUEEzhXY0Sv9voa9NFeIkRZcw1zEtC5d30/q
         ifWEh+dfSFE7CL4UHpzg0TEXl123yZnAsVD4Nzdk0Ly1+4iNhkaNo/////8DQIr3AQAAAAAXqRSRUUn/
         7EjvozN4YtftMtBnm438H4fArNgAAAAAABl2qRSfOjzmZuGGa8CNGDprHfriVETn2IisICkbAAAAAAAZ
         dqkUbZs27Nt1uzK2C61o8v2KMbWTJx6IrAAAAAAAAAD/////AUEEId3cF/ZIV3rHris7l19HJqGvR4ED
         HTttl5rxyll0y92LflGgmMdMKHnX6CqOKYS0KJljBV0WaFD0gCcdnaUodkgwRQIgI0xQLY+qnQKi8f65
         5OEAPEv/r0rZnLB/h7qd5LF6hm8CIQCOPpmt1Jr6o1b43VEYg0PNKYzRekLppI3gpVFh0zlM2AEAAjQB
         AAAACxEJBxl2qRQWtJ1IcK7dFugwnF1pwaCGOsMI1oisgJaYAAAAAAAAAAROT05FAAAANAEAAAALEQkH
         GXapFFwtg57h8JGhIbsJLXk23+KqzOo9iKwQAhsAAAAAAAAABE5PTkUAAAA=
         ================================================================================
         """.strip())


      serMap['ustx']['multispend_unsigned'] = textwrap.dedent("""
         =====TXSIGCOLLECT-7oXWAFds======================================================
         AQAAAAsRCQcAAAAAAf3UAgEAAAALEQkHSowkGdOEuZnpCexUrxsqIaabEZZYENZRdA/3sF/S7OgBAAAA
         /QABAQAAAAE0v/Sl2nBWCT2EAqEpEUiCmAyCIEOsGcxHYIoqRAFW7gAAAACLSDBFAiBPTE3Xza0azFvA
         RXvLgjd+AzM98GGvii+mz5MTaYA1JwIhAJ32cV134QHReN+b0W9ZFsYOuTWzAB321/2w4fYl0DSmAUEE
         QbpfyJgN24LNDxkiRXdynkDwT6fS2LnbhYJ3wPpBCn9RmSOLPhBrsQx742aDQcGL1jxILamFcb8mxF1h
         8IYaLv////8CUDR0AgAAAAAZdqkUkhXMoG2bpRdRBSEr8QmIRaCwX+OIrAAtMQEAAAAAF6kUlBbexafN
         63o7rwuhT3h1Msx+kUKHAAAAAMlSQQQjIU9h69Jo0ZDbvlUfiRUXM68BPhPhW83eZf1zQhyQuoutpYlR
         FUZ2rLYWEAo4hbL9smMPRzei8cDuvnkHgSkBQQTFlOfg3/UHkHyNIvk0TV4iJpzhs6CAMlRioRKWttLj
         febe3hDfoDmoqaSZhmxcUHsNAtS06pVJ+AuKGjSMA5K6QQTOFdjRK/2+hr00V4iRFlzDXMS0Ll3fT+qJ
         9YSH519IUTsIvhQenODRMReXXbfJmcCxUPg3N2TQvLX7iI2GRo2jU64IN210dmtDVGEA/////wNBBCMh
         T2Hr0mjRkNu+VR+JFRczrwE+E+Fbzd5l/XNCHJC6i62liVEVRnasthYQCjiFsv2yYw9HN6LxwO6+eQeB
         KQEAAEEExZTn4N/1B5B8jSL5NE1eIiac4bOggDJUYqESlrbS433m3t4Q36A5qKmkmYZsXFB7DQLUtOqV
         SfgLiho0jAOSugAAQQTOFdjRK/2+hr00V4iRFlzDXMS0Ll3fT+qJ9YSH519IUTsIvhQenODRMReXXbfJ
         mcCxUPg3N2TQvLX7iI2GRo2jAAACNAEAAAALEQkHGXapFCd8VsRZVBUqMoQpIAAPglG9VyAiiKxwb5gA
         AAAAAAAABE5PTkUAAAAyAQAAAAsRCQcXqRSUFt7Fp83rejuvC6FPeHUyzH6RQoeAlpgAAAAAAAAABE5P
         TkUAAAA=
         ================================================================================
         """.strip())

      serMap['ustx']['multispend_partsign'] = textwrap.dedent("""
         =====TXSIGCOLLECT-7oXWAFds======================================================
         AQAAAAsRCQcAAAAAAf0bAwEAAAALEQkHSowkGdOEuZnpCexUrxsqIaabEZZYENZRdA/3sF/S7OgBAAAA
         /QABAQAAAAE0v/Sl2nBWCT2EAqEpEUiCmAyCIEOsGcxHYIoqRAFW7gAAAACLSDBFAiBPTE3Xza0azFvA
         RXvLgjd+AzM98GGvii+mz5MTaYA1JwIhAJ32cV134QHReN+b0W9ZFsYOuTWzAB321/2w4fYl0DSmAUEE
         QbpfyJgN24LNDxkiRXdynkDwT6fS2LnbhYJ3wPpBCn9RmSOLPhBrsQx742aDQcGL1jxILamFcb8mxF1h
         8IYaLv////8CUDR0AgAAAAAZdqkUkhXMoG2bpRdRBSEr8QmIRaCwX+OIrAAtMQEAAAAAF6kUlBbexafN
         63o7rwuhT3h1Msx+kUKHAAAAAMlSQQQjIU9h69Jo0ZDbvlUfiRUXM68BPhPhW83eZf1zQhyQuoutpYlR
         FUZ2rLYWEAo4hbL9smMPRzei8cDuvnkHgSkBQQTFlOfg3/UHkHyNIvk0TV4iJpzhs6CAMlRioRKWttLj
         febe3hDfoDmoqaSZhmxcUHsNAtS06pVJ+AuKGjSMA5K6QQTOFdjRK/2+hr00V4iRFlzDXMS0Ll3fT+qJ
         9YSH519IUTsIvhQenODRMReXXbfJmcCxUPg3N2TQvLX7iI2GRo2jU64IN210dmtDVGEA/////wNBBCMh
         T2Hr0mjRkNu+VR+JFRczrwE+E+Fbzd5l/XNCHJC6i62liVEVRnasthYQCjiFsv2yYw9HN6LxwO6+eQeB
         KQEAAEEExZTn4N/1B5B8jSL5NE1eIiac4bOggDJUYqESlrbS433m3t4Q36A5qKmkmYZsXFB7DQLUtOqV
         SfgLiho0jAOSukcwRAIgK0UqQSZCBtaE6vQIQzd2cux7lCYz5F9WOsStmXuAy/4CIBogV6OLRM/W8Ia4
         nc8m+JpnnQgVh+/LtO8OaNW4ev8+AQBBBM4V2NEr/b6GvTRXiJEWXMNcxLQuXd9P6on1hIfnX0hROwi+
         FB6c4NExF5ddt8mZwLFQ+Dc3ZNC8tfuIjYZGjaMAAAI0AQAAAAsRCQcZdqkUJ3xWxFlUFSoyhCkgAA+C
         Ub1XICKIrHBvmAAAAAAAAAAETk9ORQAAADIBAAAACxEJBxepFJQW3sWnzet6O68LoU94dTLMfpFCh4CW
         mAAAAAAAAAAETk9ORQAAAA==
         ================================================================================
         """.strip())

      serMap['ustx']['multispend_enoughsign'] = textwrap.dedent("""
         =====TXSIGCOLLECT-7oXWAFds======================================================
         AQAAAAsRCQcAAAAAAf1jAwEAAAALEQkHSowkGdOEuZnpCexUrxsqIaabEZZYENZRdA/3sF/S7OgBAAAA
         /QABAQAAAAE0v/Sl2nBWCT2EAqEpEUiCmAyCIEOsGcxHYIoqRAFW7gAAAACLSDBFAiBPTE3Xza0azFvA
         RXvLgjd+AzM98GGvii+mz5MTaYA1JwIhAJ32cV134QHReN+b0W9ZFsYOuTWzAB321/2w4fYl0DSmAUEE
         QbpfyJgN24LNDxkiRXdynkDwT6fS2LnbhYJ3wPpBCn9RmSOLPhBrsQx742aDQcGL1jxILamFcb8mxF1h
         8IYaLv////8CUDR0AgAAAAAZdqkUkhXMoG2bpRdRBSEr8QmIRaCwX+OIrAAtMQEAAAAAF6kUlBbexafN
         63o7rwuhT3h1Msx+kUKHAAAAAMlSQQQjIU9h69Jo0ZDbvlUfiRUXM68BPhPhW83eZf1zQhyQuoutpYlR
         FUZ2rLYWEAo4hbL9smMPRzei8cDuvnkHgSkBQQTFlOfg3/UHkHyNIvk0TV4iJpzhs6CAMlRioRKWttLj
         febe3hDfoDmoqaSZhmxcUHsNAtS06pVJ+AuKGjSMA5K6QQTOFdjRK/2+hr00V4iRFlzDXMS0Ll3fT+qJ
         9YSH519IUTsIvhQenODRMReXXbfJmcCxUPg3N2TQvLX7iI2GRo2jU64IN210dmtDVGEA/////wNBBCMh
         T2Hr0mjRkNu+VR+JFRczrwE+E+Fbzd5l/XNCHJC6i62liVEVRnasthYQCjiFsv2yYw9HN6LxwO6+eQeB
         KQEAAEEExZTn4N/1B5B8jSL5NE1eIiac4bOggDJUYqESlrbS433m3t4Q36A5qKmkmYZsXFB7DQLUtOqV
         SfgLiho0jAOSukcwRAIgK0UqQSZCBtaE6vQIQzd2cux7lCYz5F9WOsStmXuAy/4CIBogV6OLRM/W8Ia4
         nc8m+JpnnQgVh+/LtO8OaNW4ev8+AQBBBM4V2NEr/b6GvTRXiJEWXMNcxLQuXd9P6on1hIfnX0hROwi+
         FB6c4NExF5ddt8mZwLFQ+Dc3ZNC8tfuIjYZGjaNIMEUCIQC5OkpGv/UnK/ih2GiUf9zHhBeJjYJG7YVM
         ZvaRfXiZTgIgPsSob1XTyyX6i4HrKut4N+BjCQIoFT2xjFxwzXPcxGgBAAI0AQAAAAsRCQcZdqkUJ3xW
         xFlUFSoyhCkgAA+CUb1XICKIrHBvmAAAAAAAAAAETk9ORQAAADIBAAAACxEJBxepFJQW3sWnzet6O68L
         oU94dTLMfpFCh4CWmAAAAAAAAAAETk9ORQAAAA==
         ================================================================================ 
         """.strip())
      
      serMap['ustx']['multispend_oversign'] = textwrap.dedent("""
         =====TXSIGCOLLECT-7oXWAFds======================================================
         AQAAAAsRCQcAAAAAAf2rAwEAAAALEQkHSowkGdOEuZnpCexUrxsqIaabEZZYENZRdA/3sF/S7OgBAAAA
         /QABAQAAAAE0v/Sl2nBWCT2EAqEpEUiCmAyCIEOsGcxHYIoqRAFW7gAAAACLSDBFAiBPTE3Xza0azFvA
         RXvLgjd+AzM98GGvii+mz5MTaYA1JwIhAJ32cV134QHReN+b0W9ZFsYOuTWzAB321/2w4fYl0DSmAUEE
         QbpfyJgN24LNDxkiRXdynkDwT6fS2LnbhYJ3wPpBCn9RmSOLPhBrsQx742aDQcGL1jxILamFcb8mxF1h
         8IYaLv////8CUDR0AgAAAAAZdqkUkhXMoG2bpRdRBSEr8QmIRaCwX+OIrAAtMQEAAAAAF6kUlBbexafN
         63o7rwuhT3h1Msx+kUKHAAAAAMlSQQQjIU9h69Jo0ZDbvlUfiRUXM68BPhPhW83eZf1zQhyQuoutpYlR
         FUZ2rLYWEAo4hbL9smMPRzei8cDuvnkHgSkBQQTFlOfg3/UHkHyNIvk0TV4iJpzhs6CAMlRioRKWttLj
         febe3hDfoDmoqaSZhmxcUHsNAtS06pVJ+AuKGjSMA5K6QQTOFdjRK/2+hr00V4iRFlzDXMS0Ll3fT+qJ
         9YSH519IUTsIvhQenODRMReXXbfJmcCxUPg3N2TQvLX7iI2GRo2jU64IN210dmtDVGEA/////wNBBCMh
         T2Hr0mjRkNu+VR+JFRczrwE+E+Fbzd5l/XNCHJC6i62liVEVRnasthYQCjiFsv2yYw9HN6LxwO6+eQeB
         KQFIMEUCIEp1ufpfgI5z1XwcZ9i8B7x7XwJ3mkUyCq56bOcuPTmqAiEA4V68y5iExV7VZbPqcdIxWS/w
         WA8PpFqbkdqw/kJQNb4BAEEExZTn4N/1B5B8jSL5NE1eIiac4bOggDJUYqESlrbS433m3t4Q36A5qKmk
         mYZsXFB7DQLUtOqVSfgLiho0jAOSukcwRAIgK0UqQSZCBtaE6vQIQzd2cux7lCYz5F9WOsStmXuAy/4C
         IBogV6OLRM/W8Ia4nc8m+JpnnQgVh+/LtO8OaNW4ev8+AQBBBM4V2NEr/b6GvTRXiJEWXMNcxLQuXd9P
         6on1hIfnX0hROwi+FB6c4NExF5ddt8mZwLFQ+Dc3ZNC8tfuIjYZGjaNIMEUCIQC5OkpGv/UnK/ih2GiU
         f9zHhBeJjYJG7YVMZvaRfXiZTgIgPsSob1XTyyX6i4HrKut4N+BjCQIoFT2xjFxwzXPcxGgBAAI0AQAA
         AAsRCQcZdqkUJ3xWxFlUFSoyhCkgAA+CUb1XICKIrHBvmAAAAAAAAAAETk9ORQAAADIBAAAACxEJBxep
         FJQW3sWnzet6O68LoU94dTLMfpFCh4CWmAAAAAAAAAAETk9ORQAAAA==
         ================================================================================
         """.strip())

      serMap['ustx']['ss2ms_unsigned'] = textwrap.dedent("""
         =====TXSIGCOLLECT-HJqTvsXR======================================================
         AQAAAAsRCQcAAAAAAf17AQEAAAALEQkH0yTdj/1epai7+ozi6P+QAGb7SC7heN8KKd7MXaylqCEBAAAA
         /QABAQAAAAFzi65SWdroLD8dGjAFjvQhDnaRFW1HDwU0AiSXxKxPuQEAAACLSDBFAiEAkbFWoFx5lKs+
         Q0OY3TL3lo1ckIeiZOPWB0giLsMvrP0CICJ26+e5IB8l20Luaj2+zxWCu7bxYpyFqB8AaPXBaB7/AUEE
         IyFPYevSaNGQ275VH4kVFzOvAT4T4VvN3mX9c0IckLqLraWJURVGdqy2FhAKOIWy/bJjD0c3ovHA7r55
         B4EpAf////8CQEtMAAAAAAAXqRTlgY0MJP3lDak826GfCJM965UHXIcwJEwAAAAAABl2qRRdhR54M5b6
         KlxBD4fX4V7mP5EOKoisAAAAAAAAAP////8BQQT8+7E+Bne+Y73xPhAyqyWhlR4GNkYQsKcZvrWzNd/u
         IHyxhCAOyWMdec+GFKDLijYgqVTXkF41k6cJCQtRMbvhAAACMgEAAAALEQkHF6kUlBbexafN63o7rwuh
         T3h1Msx+kUKHAAk9AAAAAAAAAAROT05FAAAANAEAAAALEQkHGXapFLJqoSyMxawfCdRd3e5nFzk56v3l
         iKwg9A4AAAAAAAAABE5PTkUAAAA=
         ================================================================================
      """.strip())

      serMap['ustx']['ss2ms_signed'] = textwrap.dedent("""
         =====TXSIGCOLLECT-HJqTvsXR======================================================
         AQAAAAsRCQcAAAAAAf3CAQEAAAALEQkH0yTdj/1epai7+ozi6P+QAGb7SC7heN8KKd7MXaylqCEBAAAA
         /QABAQAAAAFzi65SWdroLD8dGjAFjvQhDnaRFW1HDwU0AiSXxKxPuQEAAACLSDBFAiEAkbFWoFx5lKs+
         Q0OY3TL3lo1ckIeiZOPWB0giLsMvrP0CICJ26+e5IB8l20Luaj2+zxWCu7bxYpyFqB8AaPXBaB7/AUEE
         IyFPYevSaNGQ275VH4kVFzOvAT4T4VvN3mX9c0IckLqLraWJURVGdqy2FhAKOIWy/bJjD0c3ovHA7r55
         B4EpAf////8CQEtMAAAAAAAXqRTlgY0MJP3lDak826GfCJM965UHXIcwJEwAAAAAABl2qRRdhR54M5b6
         KlxBD4fX4V7mP5EOKoisAAAAAAAAAP////8BQQT8+7E+Bne+Y73xPhAyqyWhlR4GNkYQsKcZvrWzNd/u
         IHyxhCAOyWMdec+GFKDLijYgqVTXkF41k6cJCQtRMbvhRzBEAiARp54CUAAnSuKOwadJpeh1krlJyEGX
         ZqTV9KP4J8/1VwIgCI8MOAE4lIynyJ7aOSkIJ7KUjMn6aMCJTolck+gwXX8BAAIyAQAAAAsRCQcXqRSU
         Ft7Fp83rejuvC6FPeHUyzH6RQocACT0AAAAAAAAABE5PTkUAAAA0AQAAAAsRCQcZdqkUsmqhLIzFrB8J
         1F3d7mcXOTnq/eWIrCD0DgAAAAAAAAAETk9ORQAAAA==
         ================================================================================
         """.strip())

   #############################################################################
   def doRoundTrip(self, classObj, serMethod, unserMethod):
      # Test two round-trips with just the serialize methods
      def serialize(a):
         return getattr(a, serMethod)()
      
      def unserialize(obj, classType, skipMagicCheck=False):
         tempObj = classType() 
         getattr(tempObj, unserMethod)(obj, skipMagicCheck=skipMagicCheck)
         return tempObj

      ser  = serialize(classObj);  
      classObj2 = unserialize(ser,  classObj.__class__, skipMagicCheck=True)

      ser2 = serialize(classObj2); 
      classObj3 = unserialize(ser2, classObj.__class__, skipMagicCheck=True)

      self.assertEqual(classObj,  classObj2)
      self.assertEqual(classObj2, classObj3)


   # We could do all three of these in one swing with an extra loop, and even
   # test all the different classes by nesting one more layer, but it will look
   # look like there's only one test even though there's really 36, and we have 
   # to go digging to figure out which one failed.... kinda.  Maybe we should 
   # do it anyway...

   #############################################################################
   ##### UnsignedTxInput
   #############################################################################
   def testUSTXI_serialize_roundtrip(self):
      for comment,asciiUstx in serMap['ustx'].iteritems():
         ustx = UnsignedTransaction().unserializeAscii(asciiUstx, skipMagicCheck=True) 
         for ustxi in ustx.ustxInputs:
            self.doRoundTrip(ustxi, 'serialize', 'unserialize')

   #############################################################################
   def testUSTXI_JSON_roundtrip(self):
      for comment,asciiUstx in serMap['ustx'].iteritems():
         ustx = UnsignedTransaction().unserializeAscii(asciiUstx, skipMagicCheck=True) 
         for ustxi in ustx.ustxInputs:
            self.doRoundTrip(ustxi, 'toJSONMap', 'fromJSONMap')


   #############################################################################
   ##### DecoratedTxOut
   #############################################################################
   def testDTXO_serialize_roundtrip(self):
      for comment,asciiUstx in serMap['ustx'].iteritems():
         ustx = UnsignedTransaction().unserializeAscii(asciiUstx, skipMagicCheck=True) 
         for dtxo in ustx.decorTxOuts:
            self.doRoundTrip(dtxo, 'serialize', 'unserialize')

   #############################################################################
   def testDTXO_JSON_roundtrip(self):
      for comment,asciiUstx in serMap['ustx'].iteritems():
         ustx = UnsignedTransaction().unserializeAscii(asciiUstx, skipMagicCheck=True) 
         for dtxo in ustx.decorTxOuts:
            self.doRoundTrip(dtxo, 'toJSONMap', 'fromJSONMap')


   #############################################################################
   ##### UnsignedTransaction
   #############################################################################
   def testUSTX_serialize_roundtrip(self):
      for comment,asciiUstx in serMap['ustx'].iteritems():
         ustx = UnsignedTransaction().unserializeAscii(asciiUstx, skipMagicCheck=True) 
         self.doRoundTrip(ustx, 'serialize', 'unserialize')

   #############################################################################
   def testUSTX_serializeAscii_roundtrip(self):
      for comment,asciiUstx in serMap['ustx'].iteritems():
         ustx = UnsignedTransaction().unserializeAscii(asciiUstx, skipMagicCheck=True) 
         self.doRoundTrip(ustx, 'serializeAscii', 'unserializeAscii')

   #############################################################################
   def testUSTX_JSON_roundtrip(self):
      for comment,asciiUstx in serMap['ustx'].iteritems():
         ustx = UnsignedTransaction().unserializeAscii(asciiUstx, skipMagicCheck=True) 
         self.doRoundTrip(ustx, 'toJSONMap', 'fromJSONMap')



   #############################################################################
   ##### Lockbox
   #############################################################################
   def testLockbox_serialize_roundtrip(self):
      for comment,asciiLockbox in serMap['lockbox'].iteritems():
         lbox = MultiSigLockbox().unserializeAscii(asciiLockbox, skipMagicCheck=True)
         # Cannot verify that pprint or pprintOneLine does the correct thing,
         # but at least this will verify that it doesn't crash
         # and the output can be examined for manual verification.
         #lbox.pprintOneLine()
         #lbox.pprint()

   #############################################################################
   def testLockbox_serializeAscii_roundtrip(self):
      for comment,asciiLockbox in serMap['lockbox'].iteritems():
         lbox = MultiSigLockbox().unserializeAscii(asciiLockbox, skipMagicCheck=True) 
         self.doRoundTrip(lbox, 'serializeAscii', 'unserializeAscii')

   #############################################################################
   def testLockbox_JSON_roundtrip(self):
      for comment,asciiLockbox in serMap['lockbox'].iteritems():
         lbox = MultiSigLockbox().unserializeAscii(asciiLockbox, skipMagicCheck=True) 
         self.doRoundTrip(lbox, 'toJSONMap', 'fromJSONMap')

   def testLockboxDisplayInformation(self):
      lbox = MultiSigLockbox().unserializeAscii(serMap['lockbox'].values()[0], skipMagicCheck=True)
      # Cannot verify that pprint or pprintOneLine does the correct thing,
      # but at least this will verify that it doesn't crash
      #lbox.pprintOneLine()
      #lbox.pprint()
      
      self.assertTrue(binScript_to_p2shAddrStr(lbox.binScript))
   
   
   def testCreateDecoratedTxOut(self):
      lbox = MultiSigLockbox().unserializeAscii(serMap['lockbox'].values()[0], skipMagicCheck=True)
      expectedValue = 1000
      decoratedTxOutMultiSig = lbox.createDecoratedTxOut(expectedValue)
      expectedBinScriptMultiSig = hex_to_binary('52410423214f61ebd268d190dbbe551f89151733af013e13e15bcdde65fd73421c90ba8bada58951154676acb616100a3885b2fdb2630f4737a2f1c0eebe79078129014104c594e7e0dff507907c8d22f9344d5e22269ce1b3a080325462a11296b6d2e37de6dede10dfa039a8a9a499866c5c507b0d02d4b4ea9549f80b8a1a348c0392ba4104ce15d8d12bfdbe86bd34578891165cc35cc4b42e5ddf4fea89f58487e75f48513b08be141e9ce0d13117975db7c999c0b150f8373764d0bcb5fb888d86468da353ae')
      self.assertEquals(decoratedTxOutMultiSig.binScript, expectedBinScriptMultiSig)
      self.assertEquals(decoratedTxOutMultiSig.value, expectedValue)
      self.assertEquals(decoratedTxOutMultiSig.scriptType, CPP_TXOUT_MULTISIG)
      
      decoratedTxOutP2SH = lbox.createDecoratedTxOut(expectedValue, asP2SH=True)
      expectedBinScriptP2SH = hex_to_binary('a9149416dec5a7cdeb7a3baf0ba14f787532cc7e914287')
      self.assertEquals(decoratedTxOutP2SH.binScript, expectedBinScriptP2SH)
      self.assertEquals(decoratedTxOutP2SH.value, expectedValue)
      # self.scriptType is the CPP_TXOUT_TYPE of the txoScript *UNLESS* that
      # script is P2SH -- then it will be the type of the P2SH subscript,
      # and that subscript will be stored in self.p2shScript
      self.assertEquals(decoratedTxOutP2SH.scriptType, CPP_TXOUT_MULTISIG)
      
   #############################################################################
   ##### Promissory Note
   #############################################################################
   def testPromNote_serialize_roundtrip(self):
      for comment,asciiPromNote in serMap['promnote'].iteritems():
         prom = MultiSigPromissoryNote().unserializeAscii(asciiPromNote, skipMagicCheck=True) 
         self.doRoundTrip(prom, 'serialize', 'unserialize')

   #############################################################################
   def testPromNote_serializeAscii_roundtrip(self):
      for comment,asciiPromNote in serMap['promnote'].iteritems():
         prom = MultiSigPromissoryNote().unserializeAscii(asciiPromNote, skipMagicCheck=True) 
         self.doRoundTrip(prom, 'serializeAscii', 'unserializeAscii')

   #############################################################################
   def testPromNote_JSON_roundtrip(self):
      for comment,asciiPromNote in serMap['promnote'].iteritems():
         prom = MultiSigPromissoryNote().unserializeAscii(asciiPromNote, skipMagicCheck=True) 
         self.doRoundTrip(prom, 'toJSONMap', 'fromJSONMap')

   def testMakeFundingTxFromPromNotes(self):
      promNote = MultiSigPromissoryNote().unserializeAscii(
            serMap['promnote'].values()[0], skipMagicCheck=True) 
      lbox = MultiSigLockbox().unserializeAscii(serMap['lockbox'].values()[0], skipMagicCheck=True)
      result = lbox.makeFundingTxFromPromNotes([promNote])
      # 1 promisory note and no change means 1 input and 1 output
      self.assertEqual(len(result.ustxInputs), 1)
      self.assertEqual(len(result.decorTxOuts), 1)
      self.assertEqual(result.uniqueIDB58, 'NaVk9y4Y')

class PubKeyBlockTest(unittest.TestCase):
   def setUp(self):
      self.binPubKey = hex_to_binary( \
         '048d103d81ac9691cf13f3fc94e44968ef67b27f58b27372c13108552d24a6ee04'
           '785838f34624b294afee83749b64478bb8480c20b242c376e77eea2b3dc48b4b')
      self.comment = 'This is a sample comment!'
   
   def tearDown(self):
      pass
   

   #############################################################################
   def testPubKey_serialize_roundtrip(self):
      wltLoc     = 'Armory3cx8J2n#223'  
      authMethod = 'NullAuthMethod'
      authData   = NullAuthData()
      dpk = DecoratedPublicKey(self.binPubKey, self.comment, wltLoc, authMethod, authData)
      self.assertEqual(self.binPubKey, dpk.binPubKey)
      self.assertEqual(self.comment,   dpk.keyComment)
      self.assertEqual(wltLoc,         dpk.wltLocator)
      self.assertEqual(authMethod,     dpk.authMethod)
      self.assertEqual(authData,       dpk.authData)

      serKey = dpk.serialize()
      dpk2 = DecoratedPublicKey().unserialize(serKey)

      self.assertEqual(dpk.binPubKey,  dpk2.binPubKey)
      self.assertEqual(dpk.keyComment, dpk2.keyComment)
      self.assertEqual(wltLoc,         dpk2.wltLocator)
      self.assertEqual(authMethod,     dpk2.authMethod)
      self.assertEqual(authData,       dpk2.authData)


   #############################################################################
   def testPubKey_serializeAscii_roundtrip(self):
      wltLoc     = 'Armory3cx8J2n#223'  
      authMethod = 'NullAuthMethod'
      authData   = NullAuthData()
      dpk = DecoratedPublicKey(self.binPubKey, self.comment, wltLoc, authMethod, authData)
      self.assertEqual(self.binPubKey, dpk.binPubKey)
      self.assertEqual(self.comment,   dpk.keyComment)
      self.assertEqual(wltLoc,         dpk.wltLocator)
      self.assertEqual(authMethod,     dpk.authMethod)
      self.assertEqual(authData,       dpk.authData)

      ascKey = dpk.serializeAscii()
      dpk2 = DecoratedPublicKey().unserializeAscii(ascKey)

      self.assertEqual(dpk.binPubKey, dpk2.binPubKey)
      self.assertEqual(dpk.keyComment,dpk2.keyComment)
      self.assertEqual(wltLoc,        dpk2.wltLocator)
      self.assertEqual(authMethod,    dpk2.authMethod)
      self.assertEqual(authData,      dpk2.authData)



   """
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
      #print '\nTest pretty print PyTxIn, expect PrevTXHash all 0s'
      #testTxIn.pprint()
   
      # test binary unpacker in unserialize
      testTxOut = PyTxOut().unserialize(txoutA.serialize())
      self.assertEqual(txoutA.getScript(), testTxOut.getScript())
      self.assertEqual(txoutA.value, testTxOut.getValue())
      # Test pprint
      #print '\nTest pretty print PyTxOut'
      #testTxOut.pprint()
      
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
      tx2 = PyCreateAndSignTx( [[ addrA, tx1, 0 ]],  [[addrB, 50*ONE_BTC]])
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
      #print "PyOutPoint PPrint Test. Expect all 0s: "
      #outpoint.pprint()
   
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
   """

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()
