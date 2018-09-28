#! /usr/bin/python
import sys
from armoryengine.ConstructedScript import *
from armoryengine.BinaryPacker import *
from armoryengine.ArmoryUtils import *

# Create a script
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

scriptStr = getP2PKHStr(True, finalPubHash)
bp1 = BinaryPacker()
bp1.put(VAR_STR, scriptStr)

# Create a record name (SHA224)
# For now, assume record name is an email address. Use the SMIME record format,
# where the username is hashed using SHA224.
# sha224(chris) = 3f51f4663b2b798560c5b9e16d6069a28727f62518c3a1b33f7f5214
dummyStr = 'chris@payments.verisignlabs.com'
recordUser, recordDomain = dummyStr.split('@', 1)
sha224Res = sha224(recordUser)
daneReqName = sha224Res + '._pmta.' + recordDomain
bp2 = BinaryPacker()
bp2.put(VAR_STR, daneReqName)

# Create a PKRP (make multipliers)
pkrpItem = PublicKeyRelationshipProof()
pkrpItem.initialize(multProof.rawMultList)
pkrpList = []
pkrpList.append(pkrpItem)
srpItem = ScriptRelationshipProof()
srpItem.initialize(pkrpList)
bp3 = BinaryPacker()
bp3.put(VAR_STR, srpItem.serialize())

prItem = PaymentRequest()
bp1List = []
bp1List.append(bp1.getBinaryString())
bp2List = []
bp2List.append(bp2.getBinaryString())
bp3List = []
bp3List.append(bp3.getBinaryString())
prItem.initialize(bp1List, bp2List, bp3List)

# Write to file
daneReqBinFile = open('daneReq.bin','wb')
daneReqTxtFile = open('daneReq.txt','wb')
daneReqBinFile.write(prItem.serialize())
daneReqTxtFile.write(prettyHex(binary_to_hex(prItem.serialize()), \
                              indent=' '*6, withAddr=False) + '\n')
daneReqBinFile.close()
daneReqTxtFile.close()
