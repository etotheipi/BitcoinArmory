################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import sys
sys.path.append('..')
import tempfile
import unittest

from armoryengine.ALL import *


class MockPeer:
    def __init__(self):
        self.host = '100.100.100.100'
        self.port = 10010

class MockTransport:
    def __init__(self):
        self.lastMsg = ''

    def write(self, msg):
        self.lastMsg = msg

    def getPeer(self):
        return MockPeer()

    def getHost(self):
        return MockPeer()


versionMsg = hex_to_binary(
    '76657273696f6e00000000006200000085fc82fb409c00000000000'
    '0000000007ff065550000000000000000000000000000000000000000000000'
    '0064646464271a0000000000000000000000000000000000000000646464642'
    '71a3b23da7e634e9add0d41726d6f72793a302e39372e39ffffffff')

verAckMsg = hex_to_binary('76657261636b000000000000000000005df6e0e2')

block1raw = hex_to_binary(
    '03000000fd1bc6371eae1a73fcd78f8ef3f9b273b4224d570711e68351cdf80'
    '200000000f6761ed9e05ff18af3b14c5049f223814c2d9ab00a6fe30871268d'
    'aae9b80a28302a5755ffff001dadba32c002010000000100000000000000000'
    '00000000000000000000000000000000000000000000000ffffffff0c02fb00'
    '0105062f503253482fffffffff0100f2052a010000002321035af4eb9e7d0d7'
    'ab0a75d7e497798c107cb36a30a089a1d3b8ac605dac78080d4ac0000000001'
    '000000017857ac1e96312b3a189b21a5276e0e7c6ac713b457439be00456f33'
    'bdd3efbd1010000006c493046022100b1c5b3e3e0f00fe2fa675675260572b3'
    '6a0a0a9b1f450468c9bd6b73f1adc212022100c29c7ccf2666ca27aa3eda322'
    'd2282a0600d0f103a2d7894ab49dc99b7aef387012103d2b0ebef17c3edf886'
    'a761b08241918631bc31f44a733e2ae3a52884df0a71a7ffffffff02002375e'
    'e140000001976a914c148d5517e76e71b9c9f9b5e3c40d183606e4b1d88ac00'
    'e1f505000000001976a914e3ce52a2077f0543f361f0a2d730be3a6820a09f8'
    '8ac00000000')

tx1raw = hex_to_binary( \
   '01000000016290dce984203b6a5032e543e9e272d8bce934c7de4d15fa0fe44d'
   'd49ae4ece9010000008b48304502204f2fa458d439f957308bca264689aa175e'
   '3b7c5f78a901cb450ebd20936b2c500221008ea3883a5b80128e55c9c6070aa6'
   '264e1e0ce3d18b7cd7e85108ce3d18b7419a0141044202550a5a6d3bb81549c4'
   'a7803b1ad59cdbba4770439a4923624a8acfc7d34900beb54a24188f7f0a4068'
   '9d905d4847cc7d6c8d808a457d833c2d44ef83f76bffffffff0242582c0a0000'
   '00001976a914c1b4695d53b6ee57a28647ce63e45665df6762c288ac80d1f008'
   '000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00000000')


class NetworkingTest(unittest.TestCase):

    def setUp(self):
        useMainnet()
        self.tmpdir = tempfile.mkdtemp("armory_networking")
        initializeOptions()
        setNetLogFlag(True)
        reloadBDM()
        self.versionMsg = getMagicBytes() + versionMsg
        self.verAckMsg = getMagicBytes() + verAckMsg

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def testArmoryClientFactory(self):
        self.handshakeFinished = False
        def post_handshake(proto):
            self.handshakeFinished = True

        ac = ArmoryClient()
        transport = MockTransport()
        ac.transport = transport
        acf = ArmoryClientFactory(getBDM(), post_handshake)
        ac.factory = acf
        self.assertRaises(ConnectionError, acf.sendTx, None)
        self.assertRaises(ConnectionError, acf.sendMessage, None)
        self.assertEqual(acf.getProto(), None)

        ac.connectionMade()
        self.assertEqual(transport.lastMsg[:20], self.versionMsg[:20])
        self.assertEqual(transport.lastMsg[-14:], self.versionMsg[-14:])

        ac.dataReceived(self.versionMsg)
        ac.dataReceived(self.verAckMsg)

        self.assertEqual(acf.getProto(), ac)
        self.assertTrue(self.handshakeFinished)

        tx = PyTx().unserialize(tx1raw)
        acf.sendTx(tx)
        self.assertEqual(tx1raw, ac.transport.lastMsg[24:])
        payload = PayloadTx().unserialize(tx1raw)
        acf.sendMessage(payload)
        self.assertEqual(tx1raw, ac.transport.lastMsg[24:])
        message = PyMessage().unserialize(ac.transport.lastMsg)
        message.pprint()
        acf.sendMessage(message)
        self.assertEqual(message.serialize(), ac.transport.lastMsg)
        acf.sendTx(tx1raw)
        ac.dataReceived(ac.transport.lastMsg)
        payload2 = PayloadInv([(MSG_INV_TX, 'a' * 32),
                               (MSG_INV_BLOCK, '\x00' * 32)])
        message2 = PyMessage('inv', payload2)
        ac.dataReceived(message2.serialize())
        payload3 = PayloadBlock().unserialize(block1raw)
        message3 = PyMessage('block',payload3)
        ac.dataReceived(message3.serialize())
        payload4 = PayloadAlert()
        message4 = PyMessage('alert',payload4)
        ac.dataReceived(message4.serialize())

        message.magic = '\xfa\xbf\xb5\xda'
        ac.dataReceived(message.serialize())
        

        
class PayloadTests(unittest.TestCase):

    def setUp(self):
        useMainnet()
        self.now = int(time.time())
        self.bits = '0'*16
        self.addr1 = PyNetAddress(self.now, self.bits, '1.1.1.1', 11111)
        self.addr2 = PyNetAddress(self.now, self.bits, '\x02'*4, 22222)
        self.tx = PyTx().unserialize(tx1raw)
        self.tx1 = 'a' * 32
        self.blockHeader = PyBlockHeader().unserialize(block1raw)
        self.block1 = 'k' * 32
        self.block2 = 'j' * 32
        self.invList = [(MSG_INV_TX, self.tx1), (MSG_INV_BLOCK, self.block1)]

    def testPyNetAddr(self):
        ser = self.addr1.serialize()
        addr = PyNetAddress().unserialize(ser)
        self.assertEqual(ser, addr.serialize())

    def testAddr(self):
        self.addr1.pprint()
        msg = PayloadAddr([self.addr1])
        ser = msg.serialize()
        msg1 = PayloadAddr().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadAddr().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()
        msg.pprintShort()

    def testAlert(self):
        msg = PayloadAlert()
        msg.cancelSet = [1,2,3]
        msg.subVerSet = ['a','b','c']
        ser = msg.serialize()
        msg2 = PayloadAlert().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testBlock(self):
        msg = PayloadBlock(self.blockHeader, [self.tx])
        ser = msg.serialize()
        msg1 = PayloadBlock().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadBlock().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testGetBlocks(self):
        msg = PayloadGetBlocks(100, 200, [self.block1, self.block2])
        ser = msg.serialize()
        msg1 = PayloadGetBlocks().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadGetBlocks().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testGetData(self):
        msg = PayloadGetData(self.invList)
        ser = msg.serialize()
        msg1 = PayloadGetData().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadGetData().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testGetHeaders(self):
        msg = PayloadGetHeaders([self.block1, self.block2])
        ser = msg.serialize()
        msg1 = PayloadGetHeaders().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadGetHeaders().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testHeaders(self):
        msg = PayloadHeaders(self.blockHeader, [self.blockHeader])
        ser = msg.serialize()
        msg1 = PayloadHeaders().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadHeaders().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()
        
    def testInv(self):
        msg = PayloadInv(self.invList)
        ser = msg.serialize()
        msg1 = PayloadInv().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadInv().unserialize(ser)
        ser2 = msg1.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()
        
    def testPing(self):
        msg = PayloadPing()
        ser = msg.serialize()
        msg1 = PayloadPing().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadPing().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testReject(self):
        bp = BinaryPacker()
        bp.put(VAR_STR, 'sometype')
        bp.put(INT8, REJECT_DUPLICATE_CODE)
        bp.put(VAR_STR, 'hello')
        bp.put(VAR_STR, 'somerandomjunk'*10)
        ser = bp.getBinaryString()

        msg = PayloadReject().unserialize(ser)
        ser2 = msg.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testTx(self):
        msg = PayloadTx(self.tx)
        ser = msg.serialize()
        msg1 = PayloadTx().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadTx().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testVerAck(self):
        msg = PayloadVerack()
        ser = msg.serialize()
        msg1 = PayloadVerack().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadVerack().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()

    def testVersion(self):
        msg = PayloadVersion(100, self.bits, self.now, self.addr1, self.addr2,
                             999,'200',100)
        ser = msg.serialize()
        msg1 = PayloadVersion().unserialize(BinaryUnpacker(ser))
        ser1 = msg1.serialize()
        self.assertEqual(ser, ser1)
        msg2 = PayloadVersion().unserialize(ser)
        ser2 = msg2.serialize()
        self.assertEqual(ser, ser2)
        msg.pprint()
