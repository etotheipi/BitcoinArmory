import sys
sys.path.append('..')
import base64
import unittest

import jasvet
from armoryengine.ALL import *
from BIP32TestVectors import *

RECEIVED = """
    sntuoeh


-----BEGIN BITCOIN SIGNED MESSAGE-----
Comment: Signed by Bitcoin Armory v0.97.9

hello world
\t-now
h
whatever
- --now

-----BEGIN BITCOIN SIGNATURE-----

\t \n
    \n

IETQbFdmXlOvDyTx9Eg7BiS9grMTdyDx3LTnU6t50EwdxaYPhWlV1PwfBThjCkwS
2SSPhmLa44GzNk9yQK6Uuaw=
=EQy4

   \r\n
\r
-----END BITCOIN SIGNATURE-----
\r\n


"""



class SignTest(unittest.TestCase):

    def setUp(self):
        useMainnet()
        self.akp = ABEK_Generic()
        self.privKey = BIP32TestVectors[1]['seedKey'].toBinStr()[1:]
        sbdPriv  = SecureBinaryData(self.privKey)
        sbdPubk  = BIP32TestVectors[1]['seedCompPubKey']
        sbdChain = BIP32TestVectors[1]['seedCC']
        self.akp.isWatchOnly = False
        self.akp.sbdPrivKeyData = sbdPriv.copy()
        self.akp.sbdPublicKey33 = sbdPubk.copy()
        self.akp.sbdChaincode   = sbdChain.copy()
        self.akp.useCompressPub = True
        self.akp.privKeyNextUnlock = False
        self.networkNumber = binary_to_int(getAddrByte())


    def testClear(self):
        msg = "hello world\n\t-now\nh\t\nwhatever                 \n--now\r\n"
        addr = self.akp.getAddrStr(True)
        result1 = jasvet.ASv1CS(self.akp.getSerializedPrivKey('bin'), msg)
        sig1, msg1 = jasvet.readSigBlock(result1)
        self.assertEqual(
            jasvet.verifySignature(sig1, msg1, 'v1', self.networkNumber), addr)
        self.assertEqual(verifySignedMessage(result1)['address'], addr)
        result2 = self.akp.clearSignMessage(msg)
        self.assertEqual(result1[:137], result2[:137])
        sig2, msg2 = jasvet.readSigBlock(result2)
        self.assertEqual(msg1, msg2)
        self.assertEqual(len(sig1), len(sig2))
        self.assertEqual(
            jasvet.verifySignature(sig2, msg2, 'v1', self.networkNumber), addr)
        self.assertEqual(verifySignedMessage(result2)['address'], addr)
        sig3, msg3 = jasvet.readSigBlock(RECEIVED)
        self.assertEqual(
            jasvet.verifySignature(sig3, msg3, 'v1', self.networkNumber), addr)
        self.assertEqual(verifySignedMessage(RECEIVED)['address'], addr)


    def testBase64(self):
        msg = "hello world\n\t-now\nh\t\nwhatever                 \n--now\r\n"
        addr = self.akp.getAddrStr()
        result1 = jasvet.ASv1B64(self.akp.getSerializedPrivKey('bin'), msg)
        sig1, msg1 = jasvet.readSigBlock(result1)
        self.assertEqual(
            jasvet.verifySignature(sig1, msg1, 'v1', self.networkNumber), addr)
        self.assertEqual(verifySignedMessage(result1)['address'], addr)
        result2 = self.akp.b64SignMessage(msg)
        sig2, msg2 = jasvet.readSigBlock(result2)
        self.assertEqual(msg1, msg2)
        self.assertEqual(len(sig1), len(sig2))
        self.assertEqual(
            jasvet.verifySignature(sig2, msg2, 'v1', self.networkNumber), addr)
        self.assertEqual(verifySignedMessage(result2)['address'], addr)
        sig3, msg3 = jasvet.readSigBlock(RECEIVED)
        self.assertEqual(
            jasvet.verifySignature(sig3, msg3, 'v1', self.networkNumber), addr)
        self.assertEqual(verifySignedMessage(RECEIVED)['address'], addr)
