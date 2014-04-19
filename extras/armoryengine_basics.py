#! /usr/bin/python
import sys
sys.path.append('..')
from armoryengine import *

# Integer/Hex/Binary/Base58 Conversions
print '\nInteger/Hex/Binary/Base58 Conversions'
print  1, hex_to_int('0f33')
print  2, hex_to_int('0f33', BIGENDIAN)
print  3, int_to_hex(13071)
print  4, int_to_hex(13071, widthBytes=4)
print  5, int_to_hex( 3891, widthBytes=4, endOut=BIGENDIAN)
print  6, [int_to_binary(65535, widthBytes=4)]
print  7, binary_to_int('ffff')
print  8, binary_to_hex('\x00\xff\xe3\x4f')
print  9, [hex_to_binary('00ffe34f')]
print 10, binary_to_base58('\x00\xff\xe3\x4f')
print 11, [base58_to_binary('12Ux6i')]

print '\nHash functions:'
print 12, binary_to_hex(  sha256('Single-SHA256') )
print 13, binary_to_hex( hash256('Double-SHA256') )
print 14, binary_to_hex( hash160('ripemd160(sha256(X))') )
print 15, binary_to_hex( HMAC512('secret', 'MsgAuthCode') )[:24]

print '\nMay need to switch endian to match online tools'
addr160Hex = binary_to_hex( hash160('\x00'*65) )
print 16, hex_switchEndian( addr160Hex )
print 17, binary_to_hex( hash160('\x00'*65), BIGENDIAN )

print '\nAddress Conversions:'
donateStr  = '1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv'
donate160  = addrStr_to_hash160(donateStr)
donateStr2 = hash160_to_addrStr(donate160)
print 18, binary_to_hex(donate160)
print 19, binary_to_hex(donate160, BIGENDIAN)
print 20, donateStr2

print '\nBuiltin Constants and magic numbers:'
print 21, 'BITCOIN_PORT:    ', BITCOIN_PORT
print 22, 'BITCOIN_RPC_PORT:', BITCOIN_RPC_PORT
print 23, 'ARMORY_RPC_PORT: ', ARMORY_RPC_PORT
print 24, 'MAGIC_BYTES:     ', binary_to_hex(MAGIC_BYTES)
print 25, 'GENESIS_BLK_HASH:', GENESIS_BLOCK_HASH_HEX 
print 26, 'GENESIS_TX_HASH: ', GENESIS_TX_HASH_HEX    
print 27, 'ADDRBYTE:        ', binary_to_hex(ADDRBYTE)
print 28, 'NETWORK:         ', NETWORKS[ADDRBYTE]
print 29, 'P2SHBYTE:        ', binary_to_hex(P2SHBYTE)
print 30, 'PRIVKEYBYTE:     ', binary_to_hex(PRIVKEYBYTE)

print '\nDetected values and CLI_OPTIONS:'
print 31, '   Operating System      :', OS_NAME
print 32, '   OS Variant            :', OS_VARIANT
print 33, '   User home-directory   :', USER_HOME_DIR
print 34, '   Satoshi BTC directory :', BTC_HOME_DIR
print 35, '   Armory home dir       :', ARMORY_HOME_DIR
print 36, '   LevelDB directory     :', LEVELDB_DIR
print 37, '   Armory settings file  :', SETTINGS_PATH
print 38, '   Armory log file       :', ARMORY_LOG_FILE

print '\nSystem Specs:'
print 39, '   Total Available RAM   : %0.2f GB' % SystemSpecs.Memory
print 40, '   CPU ID string         :', SystemSpecs.CpuStr
print 41, '   Number of CPU cores   : %d cores' % SystemSpecs.NumCores
print 42, '   System is 64-bit      :', str(SystemSpecs.IsX64)
print 43, '   Preferred Encoding    :', locale.getpreferredencoding()

print '\nRandom other utilities'
print 44, '   Curr unix time        :', RightNow()
print 45, '   Curr formatted time   :', unixTimeToFormatStr(RightNow())
print 46, '   123456 seconds is     :', secondsToHumanTime(123456)
print 47, '   123456 bytes is       :', bytesToHumanSize(123456)

print '\nCoin2Str functions align the decimal point'
print 48, '   coin2str(0.01 BTC)    :', coin2str(0.01 * ONE_BTC)
print 49, '   coin2str(0.01 BTC)    :', coin2str(1000000, maxZeros=4)
print 50, '   coin2str(0.01 BTC)    :', coin2str(1000000, maxZeros=0)
print 51, '   coin2str(0.01 BTC)    :', coin2str(2300500000, maxZeros=0)
print 51, '   coin2str(0.01 BTC)    :', coin2str(160400000000, maxZeros=0)
print 51, '   coin2str(0.01 BTC)    :', coin2str(10000000, maxZeros=0)


print '\nRaw crypto operations:'
privKey = SecureBinaryData('\xa3'*32)
pubKey  = CryptoECDSA().ComputePublicKey(privKey)
addrStr = hash160_to_addrStr( hash160(pubKey.toBinStr()) )
print 'Raw Private Key:', privKey.toHexStr()
print 'Raw Public Key: ', pubKey.toHexStr()
print 'Raw Address Str:', addrStr
print 'Encoded PrivKey:', encodePrivKeyBase58(privKey.toBinStr())

print '\nPyBtcAddress Operations'
addrObj  = PyBtcAddress().createFromPlainKeyData(privKey)
privKey  = addrObj.serializePlainPrivateKey()
pubKey   = addrObj.serializePublicKey()
addrStr  = addrObj.getAddrStr()
addr160  = addrObj.getAddr160()
binSig   = addrObj.generateDERSignature('A msg to be signed!')
verified = addrObj.verifyDERSignature('A msg to be signed!', binSig)
print 'Obj Private Key:', binary_to_hex(privKey)
print 'Obj Public Key: ', binary_to_hex(pubKey)
print 'Obj Address Str:', addrStr
print 'Obj Address 160:', hex_switchEndian( binary_to_hex(addr160) )
print 'Obj Signature:  ', binary_to_hex(binSig)
print 'Obj SigVerifies:', verified

print '\nUse .pprint() members of objects for debugging'
addrObj.pprint()

print '\nUse pprintHex to visually break up large blocks of hex'
pprintHex( binary_to_hex( sha256('a')[:13] * 12 ) )



