#! /usr/bin/python
import sys
from jasvet import hash_160_to_bc_address
from armoryengine.ConstructedScript import *
from armoryengine.BinaryPacker import *
from armoryengine.ArmoryUtils import *

#if len(sys.argv) < 3:
#   print 'You need a seed and at least one index value'
#   return
#
#for x in sys.argv[1:]:
#   # Get args here
#   pass

# Have data handy before building the request
fakeRootSeed = SecureBinaryData('\xf0'*32)
masterExtPrv = HDWalletCrypto().convertSeedToMasterKey(fakeRootSeed)
sbdPubKey = masterExtPrv.getPublicKey()
sbdChain  = masterExtPrv.getChaincode()

# Get the final pub key and the multiplier proofs, then confirm that we
# can reverse engineer the final key with the proofs and the root pub key.
# Note that the proofs will be based on a compressed root pub key.
finalPub, multProof = DeriveBip32PublicKeyWithProof(sbdPubKey.toBinStr(),
                                                    sbdChain.toBinStr(),
                                                    [92, 912, 937])
finalPubHash = hash160(finalPub)

finalPri = DeriveBip32PrivateKey(masterExtPrv.getKey().toBinStr(),
                                 sbdChain.toBinStr(), [92, 912, 937])

# Build the PKS - Make it static for the demo - Include the checksum
pksScr = PublicKeySource()
pksScr.initialize(True, False, False, False, False, finalPubHash, True)

# Write to file
b58Res = hash_160_to_bc_address(hash160(finalPub), 111)

print 'Final pub key: %s' % binary_to_hex(finalPub)
print 'Final pub key hash: %s' % binary_to_hex(finalPubHash)
print 'Final pub key (Base58): %s' % b58Res
print 'Final pri key: %s' % binary_to_hex(finalPri)
danePKSBinFile = open('danePKS.bin','wb')
danePKSTxtFile = open('danePKS.txt','wb')
danePKSBinPriFile = open('danePKSPriKey.bin','wb')
danePKSTxtPriFile = open('danePKSPriKey.txt','wb')
danePKSBinPubFile = open('danePKSPubKey.bin','wb')
danePKSTxtPubFile = open('danePKSPubKey.txt','wb')
danePKSBinFile.write(pksScr.serialize())
danePKSTxtFile.write(prettyHex(binary_to_hex(pksScr.serialize()), \
                        indent=' '*6, withAddr=False))
danePKSBinPriFile.write(finalPri)
danePKSTxtPriFile.write(prettyHex(binary_to_hex(finalPri), \
                        indent=' '*6, withAddr=False))
danePKSBinPubFile.write(finalPub)
danePKSTxtPubFile.write(prettyHex(binary_to_hex(finalPub), \
                        indent=' '*6, withAddr=False))
danePKSBinFile.close()
danePKSTxtFile.close()
danePKSBinPriFile.close()
danePKSTxtPriFile.close()
danePKSBinPubFile.close()
danePKSTxtPubFile.close()
