#! /usr/bin/python
import sys
from armoryengine.ConstructedScript import *
from armoryengine.BinaryPacker import *
from armoryengine.ArmoryUtils import *

#if len(sys.argv) != 101:
#   print 'You need X arguments:\n*PLACE ARGS HERE*'
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

# Build the PKS - Make it static for the demo - Include the checksum
pksScr = PublicKeySource(True, False, False, False, False, finalPubHash, True)

# Write to file
danePKSBinFile = open('danePKS.bin','wb')
danePKSTxtFile = open('danePKS.txt','wb')
danePKSBinFile.write(pksScr.serialize())
danePKSTxtFile.write(prettyHex(binary_to_hex(pksScr.serialize()), \
                     indent=' '*6, withAddr=False))
danePKSBinFile.close()
danePKSTxtFile.close()
