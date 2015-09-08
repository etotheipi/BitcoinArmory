################################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################

# All data that cannot be changed, even in tests, go here.


# This is a sweet trick for create enum-like dictionaries.
# Either automatically numbers (*args), or name-val pairs (**kwargs)
#http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
   enums = dict(zip(sequential, range(len(sequential))), **named)
   return type('Enum', (), enums)

DEFAULT = 'DEFAULT'
LEVELDB_BLKDATA = 'leveldb_blkdata'
LEVELDB_HEADERS = 'leveldb_headers'

# Version Numbers
BTCARMORY_VERSION      = (0, 97,  9, 0)  # (Major, Minor, Bugfix, AutoIncrement)
ARMORY_WALLET_VERSION  = (2,  0,  0, 0)  # (Major, Minor, Bugfix, AutoIncrement)

ARMORY_DONATION_ADDR = '1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv'
ARMORY_DONATION_PUBKEY = ( '04'
      '11d14f8498d11c33d08b0cd7b312fb2e6fc9aebd479f8e9ab62b5333b2c395c5'
      'f7437cab5633b5894c4a5c2132716bc36b7571cbe492a7222442b75df75b9a84')
ARMORY_INFO_SIGN_ADDR = '1NWvhByxfTXPYNT4zMBmEY3VL8QJQtQoei'
ARMORY_INFO_SIGN_PUBLICKEY = ('04'
      'af4abc4b24ef57547dd13a1110e331645f2ad2b99dfe1189abb40a5b24e4ebd8'
      'de0c1c372cc46bbee0ce3d1d49312e416a1fa9c7bb3e32a7eb3867d1c6d1f715')
SATOSHI_PUBLIC_KEY = ( '04'
      'fc9702847840aaf195de8442ebecedf5b095cdbb9bc716bda9110971b28a49e0'
      'ead8564ff0db22209e0374782c093bb899692d524e9d6a6956e7c5ecbcd68284')

# This is a lower-security announce file, fake data, just for testing
ARMORY_TEST_SIGN_PUBLICKEY = (
   '04'
   '601c891a2cbc14a7b2bb1ecc9b6e42e166639ea4c2790703f8e2ed126fce432c'
   '62fe30376497ad3efcd2964aa0be366010c11b8d7fc8209f586eac00bb763015')

# Some useful constants to be used throughout everything
BASE58CHARS  = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
BASE16CHARS  = '0123456789abcdefABCDEF'

LITTLEENDIAN  = '<'
BIGENDIAN     = '>'
NETWORKENDIAN = '!'
ONE_BTC       = long(100000000)
DONATION       = long(5000000)
CENT          = long(1000000)
UNINITIALIZED = None
UNKNOWN       = -2
MIN_TX_FEE    = 10000
MIN_RELAY_TX_FEE = 10000
MT_WAIT_TIMEOUT_SEC = 20;

UINT8_MAX  = 2**8-1
UINT16_MAX = 2**16-1
UINT32_MAX = 2**32-1
UINT64_MAX = 2**64-1
INT8_MAX  = 2**7-1
INT16_MAX = 2**15-1
INT32_MAX = 2**31-1
INT64_MAX = 2**63-1

SECOND   = 1
MINUTE   = 60
HOUR     = 3600
DAY      = 24*HOUR
WEEK     = 7*DAY
MONTH    = 30*DAY
YEAR     = 365*DAY

UNCOMP_PK_LEN = 65
COMP_PK_LEN   = 33

KILOBYTE = 1024.0
MEGABYTE = 1024*KILOBYTE
GIGABYTE = 1024*MEGABYTE
TERABYTE = 1024*GIGABYTE
PETABYTE = 1024*TERABYTE

LB_MAXM = 7
LB_MAXN = 7

MAX_COMMENT_LENGTH = 144

# Set the default-default
DEFAULT_DATE_FORMAT = '%Y-%b-%d %I:%M%p'
FORMAT_SYMBOLS = [
   ['%y', 'year, two digit (00-99)'],
   ['%Y', 'year, four digit'],
   ['%b', 'month name (abbrev)'],
   ['%B', 'month name (full)'],
   ['%m', 'month number (01-12)'],
   ['%d', 'day of month (01-31)'],
   ['%H', 'hour 24h (00-23)'],
   ['%I', 'hour 12h (01-12)'],
   ['%M', 'minute (00-59)'],
   ['%p', 'morning/night (am,pm)'],
   ['%a', 'day of week (abbrev)'],
   ['%A', 'day of week (full)'],
   ['%%', 'percent symbol'] ]

BLOCKCHAINS = {
    '\xf9\xbe\xb4\xd9': b"Main Network",
    '\xfa\xbf\xb5\xda': b"Old Test Network",
    '\x0b\x11\x09\x07': b"Test Network (testnet3)",
}

NETWORKS = {
    b'\x00': b"Main Network",
    b'\x05': b"Main Network",
    b'\x6f': b"Test Network",
    b'\xc4': b"Test Network",
    b'\x34': b"Namecoin Network",
}

# These are the same regardless of network
# They are the way data is stored in the database which is network agnostic
SCRADDR_P2PKH_BYTE    = '\x00'
SCRADDR_P2SH_BYTE     = '\x05'
SCRADDR_MULTISIG_BYTE = '\xfe'
SCRADDR_NONSTD_BYTE   = '\xff'
SCRADDR_BYTE_LIST     = [SCRADDR_P2PKH_BYTE,
                         SCRADDR_P2SH_BYTE,
                         SCRADDR_MULTISIG_BYTE,
                         SCRADDR_NONSTD_BYTE]

# Copied from cppForSwig/BtcUtils.h::getTxInScriptTypeInt(script)
CPP_TXIN_STDUNCOMPR, CPP_TXIN_STDCOMPR, CPP_TXIN_COINBASE, \
    CPP_TXIN_SPENDPUBKEY, CPP_TXIN_SPENDMULTI, CPP_TXIN_SPENDP2SH, \
    CPP_TXIN_NONSTANDARD = range(7)

CPP_TXIN_SCRIPT_NAMES = [
    'Sig + PubKey65', 'Sig + PubKey33', 'Coinbase', 'Plain Signature',
    'Spend Multisig', 'Spend P2SH', 'Non-Standard',]

# Copied from cppForSwig/BtcUtils.h::getTxOutScriptTypeInt(script)
CPP_TXOUT_STDHASH160, CPP_TXOUT_STDPUBKEY65, CPP_TXOUT_STDPUBKEY33, \
    CPP_TXOUT_MULTISIG, CPP_TXOUT_P2SH, CPP_TXOUT_NONSTANDARD = range(6)
CPP_TXOUT_HAS_ADDRSTR  = [CPP_TXOUT_STDHASH160,
                          CPP_TXOUT_STDPUBKEY65,
                          CPP_TXOUT_STDPUBKEY33,
                          CPP_TXOUT_P2SH]
CPP_TXOUT_STDSINGLESIG = [CPP_TXOUT_STDHASH160,
                          CPP_TXOUT_STDPUBKEY65,
                          CPP_TXOUT_STDPUBKEY33]

CPP_TXOUT_SCRIPT_NAMES = [
    'Standard (PKH)', 'Standard (PK65)', 'Standard (PK33)',
    'Multi-Signature', 'Standard (P2SH)', 'Non-Standard',]

indent = ' '*3

################################################################################
NULLKDF   = "IDENTITY"
NULLCRYPT = "IDENTITY"

KNOWN_CRYPTO = { NULLCRYPT: {'blocksize':  1, 'keysize':  0},
                'AE256CFB': {'blocksize': 16, 'keysize': 32},
                'AE256CBC': {'blocksize': 16, 'keysize': 32} }

KNOWN_KDFALGOS = { NULLKDF:   [],
                  'ROMIXOV2': ['memReqd','numIter','salt'],
                  'SCRYPT__': ['N','r','p', 'salt'] } # not actually avail yet

UINT8, UINT16, UINT32, UINT64, INT8, INT16, INT32, INT64, \
    VAR_INT, VAR_STR, VAR_UNICODE, FLOAT, BINARY_CHUNK, BITSET = range(14)

HARDBIT = 0x80000000

DATATYPE = enum("Binary", 'Base58', 'Hex')
INTERNET_STATUS = enum('Available', 'Unavailable', 'DidNotCheck')

#                        0          1             2             3             4
PRIV_KEY_AVAIL = enum('Uninit', 'WatchOnly', 'Available', 'NeedDecrypt', 'NextUnlock')

DEFAULT_COMPUTE_TIME_TARGET  = 0.25
DEFAULT_MAXMEM_LIMIT         = 32*MEGABYTE

# Wallets will have to be regenerated if this is changed
ERRCORR_BYTES   = 16
ERRCORR_PER_DATA = 1024

BDM_OFFLINE = 'Offline'
BDM_UNINITIALIZED = 'Uninitialized'
BDM_BLOCKCHAIN_READY = 'BlockChainReady'
BDM_SCANNING = 'Scanning'

FINISH_LOAD_BLOCKCHAIN_ACTION = 'FinishLoadBlockchain'
NEW_ZC_ACTION = 'newZC'
NEW_BLOCK_ACTION = 'newBlock'
REFRESH_ACTION = 'refresh'
STOPPED_ACTION = 'stopped'
WARNING_ACTION = 'warning'
SCAN_ACTION = 'StartedWalletScan'

# First "official" version is 1. 0 was a prototype version.
BTCAID_CS_VERSION  = 1
BTCAID_PKS_VERSION = 1
BTCAID_PKV_VERSION = 1
BTCAID_PR_VERSION  = 1
BTCAID_RI_VERSION  = 1
BTCAID_PTV_VERSION = 1

BTCAID_PAYLOAD_TYPE = enum('PMTA', 'InvalidRec')
ESCAPECHAR  = '\xff'
ESCESC      = '\x00'

# Use in SignableIDPayload
BTCAID_PAYLOAD_BYTE = {
   BTCAID_PAYLOAD_TYPE.PMTA:       '\x00',
   BTCAID_PAYLOAD_TYPE.InvalidRec: '\xff'
}

################################################################################
# Identify all the codes/strings that are needed for dealing with scripts
################################################################################
# Start list of OP codes
OP_0 = 0
OP_FALSE = 0
OP_PUSHDATA1 = 76
OP_PUSHDATA2 = 77
OP_PUSHDATA4 = 78
OP_1NEGATE = 79
OP_1 = 81
OP_TRUE = 81
OP_2 = 82
OP_3 = 83
OP_4 = 84
OP_5 = 85
OP_6 = 86
OP_7 = 87
OP_8 = 88
OP_9 = 89
OP_10 = 90
OP_11 = 91
OP_12 = 92
OP_13 = 93
OP_14 = 94
OP_15 = 95
OP_16 = 96
OP_NOP = 97
OP_IF = 99
OP_NOTIF = 100
OP_ELSE = 103
OP_ENDIF = 104
OP_VERIFY = 105
OP_RETURN = 106
OP_TOALTSTACK = 107
OP_FROMALTSTACK = 108
OP_IFDUP = 115
OP_DEPTH = 116
OP_DROP = 117
OP_DUP = 118
OP_NIP = 119
OP_OVER = 120
OP_PICK = 121
OP_ROLL = 122
OP_ROT = 123
OP_SWAP = 124
OP_TUCK = 125
OP_2DROP = 109
OP_2DUP = 110
OP_3DUP = 111
OP_2OVER = 112
OP_2ROT = 113
OP_2SWAP = 114
OP_CAT = 126
OP_SUBSTR = 127
OP_LEFT = 128
OP_RIGHT = 129
OP_SIZE = 130
OP_INVERT = 131
OP_AND = 132
OP_OR = 133
OP_XOR = 134
OP_EQUAL = 135
OP_EQUALVERIFY = 136
OP_1ADD = 139
OP_1SUB = 140
OP_2MUL = 141
OP_2DIV = 142
OP_NEGATE = 143
OP_ABS = 144
OP_NOT = 145
OP_0NOTEQUAL = 146
OP_ADD = 147
OP_SUB = 148
OP_MUL = 149
OP_DIV = 150
OP_MOD = 151
OP_LSHIFT = 152
OP_RSHIFT = 153
OP_BOOLAND = 154
OP_BOOLOR = 155
OP_NUMEQUAL = 156
OP_NUMEQUALVERIFY = 157
OP_NUMNOTEQUAL = 158
OP_LESSTHAN = 159
OP_GREATERTHAN = 160
OP_LESSTHANOREQUAL = 161
OP_GREATERTHANOREQUAL = 162
OP_MIN = 163
OP_MAX = 164
OP_WITHIN = 165
OP_RIPEMD160 = 166
OP_SHA1 = 167
OP_SHA256 = 168
OP_HASH160 = 169
OP_HASH256 = 170
OP_CODESEPARATOR = 171
OP_CHECKSIG = 172
OP_CHECKSIGVERIFY = 173
OP_CHECKMULTISIG = 174
OP_CHECKMULTISIGVERIFY = 175

opnames = ['']*256
opnames[0] =     'OP_0'
for i in range(1,76):
   opnames[i] ='OP_PUSHDATA'
opnames[76] =    'OP_PUSHDATA1'
opnames[77] =    'OP_PUSHDATA2'
opnames[78] =    'OP_PUSHDATA4'
opnames[79] =    'OP_1NEGATE'
opnames[81] =    'OP_1'
opnames[81] =    'OP_TRUE'
for i in range(1,17):
   opnames[80+i] = 'OP_' + str(i)
opnames[97] =    'OP_NOP'
opnames[99] =    'OP_IF'
opnames[100] =   'OP_NOTIF'
opnames[103] =   'OP_ELSE'
opnames[104] =   'OP_ENDIF'
opnames[105] =   'OP_VERIFY'
opnames[106] =   'OP_RETURN'
opnames[107] =   'OP_TOALTSTACK'
opnames[108] =   'OP_FROMALTSTACK'
opnames[115] =   'OP_IFDUP'
opnames[116] =   'OP_DEPTH'
opnames[117] =   'OP_DROP'
opnames[118] =   'OP_DUP'
opnames[119] =   'OP_NIP'
opnames[120] =   'OP_OVER'
opnames[121] =   'OP_PICK'
opnames[122] =   'OP_ROLL'
opnames[123] =   'OP_ROT'
opnames[124] =   'OP_SWAP'
opnames[125] =   'OP_TUCK'
opnames[109] =   'OP_2DROP'
opnames[110] =   'OP_2DUP'
opnames[111] =   'OP_3DUP'
opnames[112] =   'OP_2OVER'
opnames[113] =   'OP_2ROT'
opnames[114] =   'OP_2SWAP'
opnames[126] =   'OP_CAT'
opnames[127] =   'OP_SUBSTR'
opnames[128] =   'OP_LEFT'
opnames[129] =   'OP_RIGHT'
opnames[130] =   'OP_SIZE'
opnames[131] =   'OP_INVERT'
opnames[132] =   'OP_AND'
opnames[133] =   'OP_OR'
opnames[134] =   'OP_XOR'
opnames[135] =   'OP_EQUAL'
opnames[136] =   'OP_EQUALVERIFY'
opnames[139] =   'OP_1ADD'
opnames[140] =   'OP_1SUB'
opnames[141] =   'OP_2MUL'
opnames[142] =   'OP_2DIV'
opnames[143] =   'OP_NEGATE'
opnames[144] =   'OP_ABS'
opnames[145] =   'OP_NOT'
opnames[146] =   'OP_0NOTEQUAL'
opnames[147] =   'OP_ADD'
opnames[148] =   'OP_SUB'
opnames[149] =   'OP_MUL'
opnames[150] =   'OP_DIV'
opnames[151] =   'OP_MOD'
opnames[152] =   'OP_LSHIFT'
opnames[153] =   'OP_RSHIFT'
opnames[154] =   'OP_BOOLAND'
opnames[155] =   'OP_BOOLOR'
opnames[156] =   'OP_NUMEQUAL'
opnames[157] =   'OP_NUMEQUALVERIFY'
opnames[158] =   'OP_NUMNOTEQUAL'
opnames[159] =   'OP_LESSTHAN'
opnames[160] =   'OP_GREATERTHAN'
opnames[161] =   'OP_LESSTHANOREQUAL'
opnames[162] =   'OP_GREATERTHANOREQUAL'
opnames[163] =   'OP_MIN'
opnames[164] =   'OP_MAX'
opnames[165] =   'OP_WITHIN'
opnames[166] =   'OP_RIPEMD160'
opnames[167] =   'OP_SHA1'
opnames[168] =   'OP_SHA256'
opnames[169] =   'OP_HASH160'
opnames[170] =   'OP_HASH256'
opnames[171] =   'OP_CODESEPARATOR'
opnames[172] =   'OP_CHECKSIG'
opnames[173] =   'OP_CHECKSIGVERIFY'
opnames[174] =   'OP_CHECKMULTISIG'
opnames[175] =   'OP_CHECKMULTISIGVERIFY'

opCodeLookup = { v:i for i,v in enumerate(opnames)}
opCodeLookup['OP_FALSE'] = 0

SIGNED_BLOCK_HEAD = '-----BEGIN BITCOIN SIGNED MESSAGE-----'
SIGNED_BLOCK_TAIL = '-----BEGIN BITCOIN SIGNATURE-----'

CRYPT_KEY_SRC = enum('PASSWORD', 'MULTIPWD', 'PARCHAIN', 'RAWKEY32', 'EKEY_OBJ')
CRYPT_IV_SRC  = enum('STOREDIV', 'PUBKEY20')

BEGIN_MARKER = '-----BEGIN '
END_MARKER = '-----END '
DASHX5 = '-----'
RN = '\r\n'
RNRN = '\r\n\r\n'
CLEARSIGN_MSG_TYPE_MARKER = 'BITCOIN SIGNED MESSAGE'
BITCOIN_SIG_TYPE_MARKER = 'BITCOIN SIGNATURE'
BASE64_MSG_TYPE_MARKER = 'BITCOIN MESSAGE'

DEFAULT_FETCH_INTERVAL = 30*MINUTE
DEFAULT_MIN_PRIORITY = 2048

PAGE_LOAD_OFFSET = 10

WLTVIEWCOLS = enum('Visible', 'FileID', 'ID', 'Name', 'Secure', 'Bal')
LEDGERCOLS  = enum('NumConf', 'UnixTime', 'DateStr', 'TxDir', 'WltName',
                   'Comment', 'Amount', 'isOther', 'WltID', 'TxHash',
                   'isCoinbase', 'toSelf', 'DoubleSpend')
ADDRESSCOLS  = enum('ChainIdx', 'Address', 'Comment', 'NumTx', 'Balance')
ADDRBOOKCOLS = enum('Address', 'WltID', 'NumSent', 'Comment')

TXINCOLS  = enum('WltID', 'Sender', 'Btc', 'OutPt', 'OutIdx', 'FromBlk',
                 'ScrType', 'Sequence', 'Script', 'AddrStr')
TXOUTCOLS = enum('WltID', 'Recip', 'Btc', 'ScrType', 'Script', 'AddrStr')
PROMCOLS = enum('PromID', 'Label', 'PayAmt', 'FeeAmt')

USERMODE       = enum('Standard', 'Advanced', 'Expert')
SATOSHIMODE    = enum('Auto', 'User')
NETWORKMODE    = enum('Offline', 'Full', 'Disconnected')
WLTTYPES       = enum('Plain', 'Crypt', 'WatchOnly', 'Offline')
WLTFIELDS      = enum('Name', 'Descr', 'WltID', 'NumAddr', 'Secure',
                      'BelongsTo', 'Crypto', 'Time', 'Mem', 'Version')
MSGBOX         = enum('Good','Info', 'Question', 'Warning', 'Critical', 'Error')
MSGBOX         = enum('Good','Info', 'Question', 'Warning', 'Critical', 'Error')
DASHBTNS       = enum('Close', 'Browse', 'Install', 'Instruct', 'Settings')

VERTICAL = 'vertical'
HORIZONTAL = 'horizontal'

NO_CHANGE = 'NoChange'
STRETCH = 'Stretch'
CLICKED = 'clicked()'

MAX_QR_SIZE = 198
MAX_SATOSHIS = 2100000000000000

LOCKBOXCOLS = enum('ID', 'MSType', 'CreateDate', 'LBName', 'Key0', 'Key1',
                   'Key2', 'Key3', 'Key4', 'NumTx', 'Balance', 'UnixTime')

WALLET_DATA_ENTRY_FIELD_WIDTH = 60

ALWAYS_OPEN_URL = 'http://google.com'
ALWAYS_OPEN_URL2 = 'http://microsoft.com'

ANNOUNCE_TEXT_URL = 'https://bitcoinarmory.com/announce.txt'
ANNOUNCE_TEXT_BACKUP_URL = 'https://s3.amazonaws.com/bitcoinarmory-media/announce.txt'
ANNOUNCE_TEXT_TEST_URL = 'https://s3.amazonaws.com/bitcoinarmory-testing/testannounce.txt'
ARMORY_ANNOUNCE_URL = 'https://bitcoinarmory.com/announcements/'
ARMORY_URL = 'https://www.bitcoinarmory.com'
BACKUP_URL = 'https://bitcoinarmory.com/armory-backups-are-forever/'
BUG_REPORT_URL = 'https://bitcoinarmory.com/scripts/receive_debug.php'
CHANGE_URL = 'https://bitcoinarmory.com/all-about-change'
DOWNLOAD_URL = 'https://bitcoinarmory.com/download/'
FAQ_URL = 'https://bitcoinarmory.com/faq/'
INSTALL_LINUX_URL = 'https://www.bitcoinarmory.com/install-linux/'
INSTALL_OSX_URL = 'https://www.bitcoinarmory.com/install-macosx/'
INSTALL_WINDOWS_URL = 'https://www.bitcoinarmory.com/install-windows/'
NEED_BITCOIN_URL = 'https://bitcoinarmory.com/armory-and-bitcoin-qt'
OFFLINE_URL = 'https://bitcoinarmory.com/using-our-wallet/#offlinewallet'
PRIVACY_URL = 'https://bitcoinarmory.com/privacy-policy'
QUICK_START_URL = 'https://bitcoinarmory.com/using-our-wallet'
SUPPORT_URL = 'https://bitcoinarmory.com/support'
TROUBLESHOOTING_URL = 'https://bitcoinarmory.com/troubleshooting/'


ALERTS_URL = 'http://www.bitcoin.org/en/alerts'
BITCOIN_DOWNLOAD_URL = 'http://www.bitcoin.org/en/download'
BITCOIN_URL = 'http://www.bitcoin.org'

AGPL_URL = 'http://www.gnu.org/licenses/agpl-3.0.html'

DEFAULT_ENCODING = 'utf-8'

# Some more constants that are needed to play nice with the C++ utilities
ARMORY_DB_BARE, ARMORY_DB_LITE, ARMORY_DB_PARTIAL, \
   ARMORY_DB_FULL, ARMORY_DB_SUPER = range(5)

DB_PRUNE_ALL = 0
DB_PRUNE_NONE = 1

# The following params are for the Bitcoin elliptic curves (secp256k1)
SECP256K1_MOD   = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
SECP256K1_B     = 0x0000000000000000000000000000000000000000000000000000000000000007L
SECP256K1_A     = 0x0000000000000000000000000000000000000000000000000000000000000000L
SECP256K1_GX    = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
SECP256K1_GY    = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L

MULTISIG_VERSION = 1
LOCKBOXIDSIZE = 8
PROMIDSIZE = 4
LBPREFIX, LBSUFFIX = 'Lockbox[Bare:', ']'
LBP2SHPREFIX = 'Lockbox['

TX_INVALID, OP_NOT_IMPLEMENTED, OP_DISABLED, SCRIPT_STACK_SIZE_ERROR, \
   SCRIPT_ERROR, SCRIPT_NO_ERROR = range(6)

UNSIGNED_TX_VERSION = 1

SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
SIGHASH_ANYONECANPAY = 0x80

# Use to identify status of individual sigs on an UnsignedTxINPUT
TXIN_SIGSTAT = enum('ALREADY_SIGNED', 'WLT_ALREADY_SIGNED',
                    'WLT_CAN_SIGN', 'NO_SIGNATURE')

# Use to identify status of USTXI objects of an UnsignedTransaction obj
TX_SIGSTAT = enum('SIGNING_COMPLETE', 'WLT_CAN_COMPLETE',
                  'WLT_CAN_CONTRIB', 'CANNOT_COMPLETE')

MSG_INV_ERROR = 0
MSG_INV_TX    = 1
MSG_INV_BLOCK = 2

REJECT_MALFORMED_CODE = 0x01
REJECT_INVALID_CODE = 0x10
REJECT_OBSOLETE_CODE = 0x11
REJECT_DUPLICATE_CODE = 0x12
REJECT_NONSTANDARD_CODE = 0x40
REJECT_DUST_CODE = 0x41
REJECT_INSUFFICIENTFEE_CODE = 0x42
REJECT_CHECKPOINT_CODE = 0x43

# AKP  ~ ArmoryKeyPair
# ABEK ~ ArmoryBip32ExtendedKey
# These are here b/c they might be tweaked in the future.  All other numerics
# are defined within the classes themselves
DEFAULT_CHILDPOOLSIZE = {}
DEFAULT_CHILDPOOLSIZE['ABEK_BIP44Seed']        = 0  # no keypool
DEFAULT_CHILDPOOLSIZE['ABEK_BIP44Purpose']     = 0  # no keypool
DEFAULT_CHILDPOOLSIZE['ABEK_StdBip32Seed']     = 2  # Lookahead two wallets
DEFAULT_CHILDPOOLSIZE['ABEK_SoftBip32Seed']    = 2  # Lookahead two wallets
DEFAULT_CHILDPOOLSIZE['ABEK_StdWallet']        = 2
DEFAULT_CHILDPOOLSIZE['ABEK_StdLeaf']          = 0  # leaf node
DEFAULT_CHILDPOOLSIZE['Armory135Root']         = 1000  # old Armory wallets
DEFAULT_CHILDPOOLSIZE['Armory135KeyPair']      = 1     # old Armory wallets
DEFAULT_CHILDPOOLSIZE['ArmoryImportedKeyPair'] = 0
DEFAULT_CHILDPOOLSIZE['ArmoryImportedRoot']    = 0
DEFAULT_CHILDPOOLSIZE['ABEK_Generic']          = 5
DEFAULT_SEED_SIZE = 16

HASH160PREFIX  = '\x00'
P2SHPREFIX     = '\x05'
MSIGPREFIX     = '\xfe'
NONSTDPREFIX   = '\xff'

NORMALCHARS  = '0123 4567 89ab cdef'.replace(' ','')
EASY16CHARS  = 'asdf ghjk wert uion'.replace(' ','')
HEX_TO_BASE16_MAP = {}
BASE16_TO_HEX_MAP = {}

for n,b in zip(NORMALCHARS,EASY16CHARS):
   HEX_TO_BASE16_MAP[n] = b
   BASE16_TO_HEX_MAP[b] = n

MPEK_FRAG_TYPE = enum('NONE', 'PASSWORD', 'FRAGKEY', 'PLAINFRAG')

MODULES_ZIP_DIR_NAME = 'modules'

################################################################################
# We define default preferences for weightings.  Weightings are used to
# determine the "priorities" for ranking various SelectCoins results
# By setting the weights to different orders of magnitude, you are essentially
# defining a sort-order:  order by FactorA, then sub-order by FactorB...
################################################################################
# TODO:  ADJUST WEIGHTING!
IDX_ALLOWFREE, IDX_NOZEROCONF, IDX_PRIORITY, IDX_NUMADDR, IDX_TXSIZE, \
   IDX_OUTANONYM = range(6)
WEIGHTS = [None] * 6
WEIGHTS[IDX_ALLOWFREE]  =  100000
WEIGHTS[IDX_NOZEROCONF] = 1000000  # let's avoid zero-conf if possible
WEIGHTS[IDX_PRIORITY]   =      50
WEIGHTS[IDX_NUMADDR]    =  100000
WEIGHTS[IDX_TXSIZE]     =     100
WEIGHTS[IDX_OUTANONYM]  =      30
