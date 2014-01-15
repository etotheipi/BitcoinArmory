################################################################################
#                                                                              #
# Copyright (C) 2011-2013, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import logging
import os

import CppBlockUtils as Cpp
from armoryengine.ArmoryUtils import *
from armoryengine.BinaryPacker import *
from armoryengine.BinaryUnpacker import *

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
opnames[0] =   'OP_0'
for i in range(1,76):
   opnames[i] ='OP_PUSHDATA'
opnames[76] =   'OP_PUSHDATA1'
opnames[77] =   'OP_PUSHDATA2'
opnames[78] =   'OP_PUSHDATA4'
opnames[79] =   'OP_1NEGATE'
opnames[81] =  'OP_1'
opnames[81] =   'OP_TRUE'
for i in range(1,17):
   opnames[80+i] = 'OP_' + str(i)
opnames[97] =   'OP_NOP'
opnames[99] =   'OP_IF'
opnames[100] =   'OP_NOTIF'
opnames[103] = 'OP_ELSE'
opnames[104] = 'OP_ENDIF'
opnames[105] =   'OP_VERIFY'
opnames[106] = 'OP_RETURN'
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
opnames[127] = 'OP_SUBSTR'
opnames[128] =   'OP_LEFT'
opnames[129] =   'OP_RIGHT'
opnames[130] =   'OP_SIZE'
opnames[131] =   'OP_INVERT'
opnames[132] =   'OP_AND'
opnames[133] =   'OP_OR'
opnames[134] = 'OP_XOR'
opnames[135] = 'OP_EQUAL'
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
opnames[162] = 'OP_GREATERTHANOREQUAL'
opnames[163] =   'OP_MIN'
opnames[164] =   'OP_MAX'
opnames[165] = 'OP_WITHIN'
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


opCodeLookup = {}
opCodeLookup['OP_FALSE'] = 0
opCodeLookup['OP_PUSHDATA1'] =   76
opCodeLookup['OP_PUSHDATA2'] =   77
opCodeLookup['OP_PUSHDATA4'] =   78
opCodeLookup['OP_1NEGATE'] =   79
opCodeLookup['OP_1'] =  81
for i in range(1,17):
   opCodeLookup['OP_'+str(i)] =  80+i
opCodeLookup['OP_TRUE'] =   81
opCodeLookup['OP_NOP'] =   97
opCodeLookup['OP_IF'] =   99
opCodeLookup['OP_NOTIF'] =   100
opCodeLookup['OP_ELSE'] = 103
opCodeLookup['OP_ENDIF'] = 104
opCodeLookup['OP_VERIFY'] =   105
opCodeLookup['OP_RETURN'] = 106
opCodeLookup['OP_TOALTSTACK'] =   107
opCodeLookup['OP_FROMALTSTACK'] =   108
opCodeLookup['OP_IFDUP'] =   115
opCodeLookup['OP_DEPTH'] =   116
opCodeLookup['OP_DROP'] =   117
opCodeLookup['OP_DUP'] =   118
opCodeLookup['OP_NIP'] =   119
opCodeLookup['OP_OVER'] =   120
opCodeLookup['OP_PICK'] =   121
opCodeLookup['OP_ROLL'] =   122
opCodeLookup['OP_ROT'] =   123
opCodeLookup['OP_SWAP'] =   124
opCodeLookup['OP_TUCK'] =   125
opCodeLookup['OP_2DROP'] =   109
opCodeLookup['OP_2DUP'] =   110
opCodeLookup['OP_3DUP'] =   111
opCodeLookup['OP_2OVER'] =   112
opCodeLookup['OP_2ROT'] =   113
opCodeLookup['OP_2SWAP'] =   114
opCodeLookup['OP_CAT'] =   126
opCodeLookup['OP_SUBSTR'] = 127
opCodeLookup['OP_LEFT'] =   128
opCodeLookup['OP_RIGHT'] =   129
opCodeLookup['OP_SIZE'] =   130
opCodeLookup['OP_INVERT'] =   131
opCodeLookup['OP_AND'] =   132
opCodeLookup['OP_OR'] =   133
opCodeLookup['OP_XOR'] = 134
opCodeLookup['OP_EQUAL'] = 135
opCodeLookup['OP_EQUALVERIFY'] =   136
opCodeLookup['OP_1ADD'] =   139
opCodeLookup['OP_1SUB'] =   140
opCodeLookup['OP_2MUL'] =   141
opCodeLookup['OP_2DIV'] =   142
opCodeLookup['OP_NEGATE'] =   143
opCodeLookup['OP_ABS'] =   144
opCodeLookup['OP_NOT'] =   145
opCodeLookup['OP_0NOTEQUAL'] =   146
opCodeLookup['OP_ADD'] =   147
opCodeLookup['OP_SUB'] =   148
opCodeLookup['OP_MUL'] =   149
opCodeLookup['OP_DIV'] =   150
opCodeLookup['OP_MOD'] =   151
opCodeLookup['OP_LSHIFT'] =   152
opCodeLookup['OP_RSHIFT'] =   153
opCodeLookup['OP_BOOLAND'] =   154
opCodeLookup['OP_BOOLOR'] =   155
opCodeLookup['OP_NUMEQUAL'] =   156
opCodeLookup['OP_NUMEQUALVERIFY'] =   157
opCodeLookup['OP_NUMNOTEQUAL'] =   158
opCodeLookup['OP_LESSTHAN'] =   159
opCodeLookup['OP_GREATERTHAN'] =   160
opCodeLookup['OP_LESSTHANOREQUAL'] =   161
opCodeLookup['OP_GREATERTHANOREQUAL'] = 162
opCodeLookup['OP_MIN'] =   163
opCodeLookup['OP_MAX'] =   164
opCodeLookup['OP_WITHIN'] = 165
opCodeLookup['OP_RIPEMD160'] =   166
opCodeLookup['OP_SHA1'] =   167
opCodeLookup['OP_SHA256'] =   168
opCodeLookup['OP_HASH160'] =   169
opCodeLookup['OP_HASH256'] =   170
opCodeLookup['OP_CODESEPARATOR'] =   171
opCodeLookup['OP_CHECKSIG'] =   172
opCodeLookup['OP_CHECKSIGVERIFY'] =   173
opCodeLookup['OP_CHECKMULTISIG'] =   174
opCodeLookup['OP_CHECKMULTISIGVERIFY'] =   175
#Word Opcode   Description
#OP_PUBKEYHASH = 253   Represents a public key hashed with OP_HASH160.
#OP_PUBKEY = 254   Represents a public key compatible with OP_CHECKSIG.
#OP_INVALIDOPCODE = 255   Matches any opcode that is not yet assigned.
#[edit] Reserved words
#Any opcode not assigned is also reserved. Using an unassigned opcode makes the transaction invalid.
#Word   Opcode   When used...
#OP_RESERVED = 80   Transaction is invalid
#OP_VER = 98   Transaction is invalid
#OP_VERIF = 101   Transaction is invalid
#OP_VERNOTIF = 102   Transaction is invalid
#OP_RESERVED1 = 137   Transaction is invalid
#OP_RESERVED2 = 138   Transaction is invalid
#OP_NOP1 = OP_NOP10   176-185   The word is ignored.


def getOpCode(name):
   return int_to_binary(opCodeLookup[name], widthBytes=1)


TXIN_SCRIPT_STANDARD = 0
TXIN_SCRIPT_COINBASE = 1
TXIN_SCRIPT_SPENDCB  = 2
TXIN_SCRIPT_UNSIGNED = 3
TXIN_SCRIPT_UNKNOWN  = 4

TXOUT_SCRIPT_STANDARD = 0
TXOUT_SCRIPT_COINBASE = 1
TXOUT_SCRIPT_MULTISIG = 2
TXOUT_SCRIPT_OP_EVAL  = 3
TXOUT_SCRIPT_UNKNOWN  = 4

MULTISIG_1of1     = (1,1)
MULTISIG_1of2     = (1,2)
MULTISIG_2oF2     = (2,2)
MULTISIG_1oF3     = (1,3)
MULTISIG_2oF3     = (2,3)
MULTISIG_3oF3     = (3,3)
MULTISIG_UNKNOWN  = (0,0)

TXOUT_TYPE_NAMES = { TXOUT_SCRIPT_STANDARD: 'Standard', \
                     TXOUT_SCRIPT_COINBASE: 'Coinbase', \
                     TXOUT_SCRIPT_MULTISIG: 'Multi-Signature', \
                     TXOUT_SCRIPT_UNKNOWN:  '<Unrecognized>', \
                     TXOUT_SCRIPT_OP_EVAL:  'OP-EVAL' }
TXIN_TYPE_NAMES = {  TXIN_SCRIPT_STANDARD:  'Standard', \
                     TXIN_SCRIPT_COINBASE:  'Coinbase', \
                     TXIN_SCRIPT_SPENDCB:   'Spend-CB', \
                     TXIN_SCRIPT_UNSIGNED:  'Unsigned', \
                     TXIN_SCRIPT_UNKNOWN:   '<Unrecognized>'}

################################################################################
def getTxOutMultiSigInfo(binScript):
   """
   Gets the Multi-Sig tx type, as well as all the address-160 strings of
   the keys that are needed to satisfy this transaction.  This currently
   only identifies M-of-N transaction types, returning unknown otherwise.

   However, the address list it returns should be valid regardless of
   whether the type was unknown:  we assume all 20-byte chunks of data
   are public key hashes, and 65-byte chunks are public keys.

   NOTE:  Because the address list is always valid, there is no reason
          not to use this method to extract addresses from ANY scripts,
          not just multi-sig...
   """
   addr160List = []
   pub65List   = []
   bup = BinaryUnpacker(binScript)
   opcodes = []
   while bup.getRemainingSize() > 0:
      nextByte = bup.get(UINT8)
      binChunk = ''
      if 0 < nextByte < 76:
         nBytes = nextByte
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA1:
         nBytes = bup.get(UINT8)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA2:
         nBytes = bup.get(UINT16)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA4:
         nBytes = bup.get(UINT32)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      else:
         opcodes.append(nextByte)
         

      if len(binChunk) == 20:
         addr160List.append(binChunk)
         pub65List.append('')
         opcodes.append('<Addr20>')
      elif len(binChunk) == 65:
         addr160List.append(convertKeyDataToAddress(pubKey=binChunk))
         pub65List.append(binChunk)
         opcodes.append('<PubKey65>')

   #print 'Transaction:',
   #for op in opcodes:
      #print op,

   # First assume that this is an M-of-N script
   try:
      M = int(opcodes[ 0])
      N = int(opcodes[-2])
      keys  = opcodes[1:-2]
      nPub = sum([(1 if p=='PubKey65' else 0) for p in keys])
      if 0<M<3 and 0<N<=3 and N==nPub:
         # We have a legit M-of-N script, figure out which one
         if M==1 and N==1: return MULTISIG_1of1, addr160List, pub65List
         if M==1 and N==2: return MULTISIG_1of2, addr160List, pub65List
         if M==2 and N==2: return MULTISIG_2oF2, addr160List, pub65List
         if M==1 and N==3: return MULTISIG_1oF3, addr160List, pub65List
         if M==2 and N==3: return MULTISIG_2oF3, addr160List, pub65List
         if M==3 and N==3: return MULTISIG_3oF3, addr160List, pub65List
   except:
      pass

      
   # Next try A-or-(B-and-C) transaction (not implemented yet
   # I'm not sure how these transactions will look
   try:
      pass
   except:
      pass

   return MULTISIG_UNKNOWN, addr160List, pub65List


################################################################################
def getTxOutScriptType(binScript):
   if binScript[:2] == hex_to_binary('4104'):
      is65B = len(binScript) == 67
      lastByteMatch = binScript[-1] == getOpCode('OP_CHECKSIG')
      if (is65B and lastByteMatch):
         return TXOUT_SCRIPT_COINBASE
   else:
      is1 = binScript[ 0] == getOpCode('OP_DUP')
      is2 = binScript[ 1] == getOpCode('OP_HASH160')
      is3 = binScript[-2] == getOpCode('OP_EQUALVERIFY')
      is4 = binScript[-1] == getOpCode('OP_CHECKSIG')
      if (is1 and is2 and is3 and is4):
         return TXOUT_SCRIPT_STANDARD

   # If we got here, let's check if it's a standard Multi-sig type
   mstype = getTxOutMultiSigInfo(binScript)[0]
   if mstype!=MULTISIG_UNKNOWN:
      return TXOUT_SCRIPT_MULTISIG

   return TXOUT_SCRIPT_UNKNOWN

################################################################################
def TxOutScriptExtractAddrStr(binScript):
   return hash160_to_addrStr(TxOutScriptExtractAddr160(binScript))

################################################################################
def TxOutScriptExtractAddr160(binScript):
   txoutType = getTxOutScriptType(binScript)
   if txoutType == TXOUT_SCRIPT_UNKNOWN:
      return '\x00'*20

   if txoutType == TXOUT_SCRIPT_COINBASE:
      return convertKeyDataToAddress(pubKey=binScript[1:66])
   elif txoutType == TXOUT_SCRIPT_STANDARD:
      return binScript[3:23]
   elif txoutType == TXOUT_SCRIPT_MULTISIG:
      # Returns a list of addresses
      return getTxOutMultiSigInfo(binScript)[1]


################################################################################
def getTxInScriptType(txinObj):
   """
   NOTE: this method takes a TXIN object, not just the script itself.  This
         is because this method needs to see the OutPoint to distinguish an
         UNKNOWN TxIn from a coinbase-TxIn
   """
   binScript = txinObj.binScript
   if len(binScript)==0:
      return TXIN_SCRIPT_UNSIGNED
   if txinObj.outpoint.txHash == EmptyHash:
      return TXIN_SCRIPT_COINBASE

   b0,b1,b2,b3,b4 = binScript[:5]
   if not (b1=='\x30' and b3=='\x02'):
      return TXIN_SCRIPT_UNKNOWN

   SigSize = binary_to_int(b2) + 3
   PubkeySize = 66  # 0x4104[Pubx][Puby]

   if len(binScript)==SigSize:
      return TXIN_SCRIPT_SPENDCB
   elif len(binScript)==(SigSize + PubkeySize + 1):
      return TXIN_SCRIPT_STANDARD

   return TXIN_SCRIPT_UNKNOWN


################################################################################
def TxInScriptExtractKeyAddr(txinObj):
   scrType = getTxInScriptType(txinObj)
   if scrType == TXIN_SCRIPT_STANDARD:
      pubKeyBin = txinObj.binScript[-65:]
      newAddr = PyBtcAddress().createFromPublicKey(pubKeyBin)
      return (newAddr.calculateAddrStr(), newAddr.binPublicKey65.toBinStr()) # LITTLE_ENDIAN
   elif scrType == TXIN_SCRIPT_COINBASE:
      return ('[COINBASE-NO-ADDR: %s]'%binary_to_hex(txinObj.binScript), '[COINBASE-NO-PUBKEY]')
      #return ('[COINBASE-NO-ADDR]', '[COINBASE-NO-PUBKEY]')
   elif scrType == TXIN_SCRIPT_SPENDCB:
      return ('[SPENDCOINBASE]', '[SPENDCOINBASE]')
   else:
      return ('[UNKNOWN-TXIN]', '[UNKNOWN-TXIN]')


################################################################################
def TxInScriptExtractAddr160IfAvail(txinObj):
   if getTxInScriptType(txinObj) == TXIN_SCRIPT_STANDARD:
      pubKeyBin = txinObj.binScript[-65:]
      return hash160(pubKeyBin)
   else:
      return ''



# Finally done with all the base conversion functions and ECDSA code
# Now define the classes for the objects that will use this


################################################################################
#  Transaction Classes
################################################################################


#####
class BlockComponent(object):
   
   def copy(self):
      return self.__class__().unserialize(self.serialize())
   
   def serialize(self):
      raise NotImplementedError

   def unserialize(self):
      raise NotImplementedError
   
################################################################################
class PyOutPoint(BlockComponent):
   #def __init__(self, txHash, txOutIndex):
      #self.txHash = txHash
      #self.txOutIndex     = outIndex

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         opData = toUnpack
      else:
         opData = BinaryUnpacker( toUnpack )

      if opData.getRemainingSize() < 36: raise UnserializeError
      self.txHash = opData.get(BINARY_CHUNK, 32)
      self.txOutIndex = opData.get(UINT32)
      return self

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.txHash)
      binOut.put(UINT32, self.txOutIndex)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'OutPoint:'
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.txHash, endian), \
                  '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'TxOutIndex:', self.txOutIndex

      
#####
class PyTxIn(BlockComponent):
   def __init__(self):
      self.outpoint   = UNINITIALIZED
      self.binScript  = UNINITIALIZED
      self.intSeq     = 2**32-1

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txInData = toUnpack
      else:
         txInData = BinaryUnpacker( toUnpack )

      self.outpoint  = PyOutPoint().unserialize( txInData.get(BINARY_CHUNK, 36) )
      
      scriptSize     = txInData.get(VAR_INT)
      if txInData.getRemainingSize() < scriptSize+4: raise UnserializeError
      self.binScript = txInData.get(BINARY_CHUNK, scriptSize)
      self.intSeq    = txInData.get(UINT32)
      return self

   def getScript(self):
      return self.binScript

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.outpoint.serialize() )
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      binOut.put(UINT32, self.intSeq)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'PyTxIn:'
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.outpoint.txHash, endian), \
                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'TxOutIndex:', self.outpoint.txOutIndex
      print indstr + indent + 'Script:    ', \
                  '('+binary_to_hex(self.binScript)[:64]+')'
      inAddr160 = TxInScriptExtractAddr160IfAvail(self)
      if len(inAddr160)>0:
         print indstr + indent + 'Sender:    ', hash160_to_addrStr(inAddr160)
      print indstr + indent + 'Seq:       ', self.intSeq
      
   def toString(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      result = indstr + 'PyTxIn:'
      result = ''.join([result, '\n',  indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.outpoint.txHash, endian), \
                      '(BE)' if endian==BIGENDIAN else '(LE)'])
      result = ''.join([result, '\n',  indstr + indent + 'TxOutIndex:', str(self.outpoint.txOutIndex)])
      result = ''.join([result, '\n',  indstr + indent + 'Script:    ', \
                  '('+binary_to_hex(self.binScript)[:64]+')'])
      inAddr160 = TxInScriptExtractAddr160IfAvail(self)
      if len(inAddr160)>0:
         result = ''.join([result, '\n',  indstr + indent + 'Sender:    ', hash160_to_addrStr(inAddr160)])
      result = ''.join([result, '\n',  indstr + indent + 'Seq:       ', str(self.intSeq)])
      return result

   # Before broadcasting a transaction make sure that the script is canonical
   # This TX could have been signed by an older version of the software.
   # Either on the offline Armory installation which may not have been upgraded
   # or on a previous installation of Armory on this computer.
   def minimizeDERSignaturePadding(self):
      rsLen = binary_to_int(self.binScript[2:3])
      rLen = binary_to_int(self.binScript[4:5])
      rBin = self.binScript[5:5+rLen]
      sLen = binary_to_int(self.binScript[6+rLen:7+rLen])
      sBin = self.binScript[7+rLen:7+rLen+sLen]
      sigScript = createSigScript(rBin, sBin)
      newBinScript = int_to_binary(len(sigScript)+1) + sigScript + self.binScript[3+rsLen:]
      paddingRemoved = newBinScript != self.binScript
      newTxIn = self.copy()
      newTxIn.binScript = newBinScript
      return paddingRemoved, newTxIn
   

#####
class PyTxOut(BlockComponent):
   def __init__(self):
      self.value     = UNINITIALIZED
      self.binScript = UNINITIALIZED

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txOutData = toUnpack
      else:
         txOutData = BinaryUnpacker( toUnpack )

      self.value       = txOutData.get(UINT64)
      scriptSize       = txOutData.get(VAR_INT)
      if txOutData.getRemainingSize() < scriptSize: raise UnserializeError
      self.binScript = txOutData.get(BINARY_CHUNK, scriptSize)
      return self

   def getValue(self):
      return self.value

   def getScript(self):
      return self.binScript

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT64, self.value)
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'TxOut:'
      print indstr + indent + 'Value:   ', self.value, '(', float(self.value) / ONE_BTC, ')'
      txoutType = getTxOutScriptType(self.binScript)
      if txoutType == TXOUT_SCRIPT_COINBASE:
         print indstr + indent + 'Script:   PubKey(%s) OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript),)
      elif txoutType == TXOUT_SCRIPT_STANDARD:
         print indstr + indent + 'Script:   OP_DUP OP_HASH (%s) OP_EQUAL OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript),)
      else:
         print indstr + indent + 'Script:   <Non-standard script!>'

   def toString(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      result = indstr + 'TxOut:'
      result = ''.join([result, '\n',   indstr + indent + 'Value:   ', str(self.value), '(', str(float(self.value) / ONE_BTC), ')'])
      txoutType = getTxOutScriptType(self.binScript)
      if txoutType == TXOUT_SCRIPT_COINBASE:
         result = ''.join([result, '\n',   indstr + indent + 'Script:   PubKey(%s) OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript))])
      elif txoutType == TXOUT_SCRIPT_STANDARD:
         result = ''.join([result, '\n',   indstr + indent + 'Script:   OP_DUP OP_HASH (%s) OP_EQUAL OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript))])
      else:
         result = ''.join([result, '\n',   indstr + indent + 'Script:   <Non-standard script!>'])
      return result 
#####
class PyTx(BlockComponent):
   def __init__(self):
      self.version    = UNINITIALIZED
      self.inputs     = UNINITIALIZED
      self.outputs    = UNINITIALIZED
      self.lockTime   = 0
      self.thisHash   = UNINITIALIZED
      self.isSigned   = False

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT32, self.version)
      binOut.put(VAR_INT, len(self.inputs))
      for txin in self.inputs:
         binOut.put(BINARY_CHUNK, txin.serialize())
      binOut.put(VAR_INT, len(self.outputs))
      for txout in self.outputs:
         binOut.put(BINARY_CHUNK, txout.serialize())
      binOut.put(UINT32, self.lockTime)
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txData = toUnpack
      else:
         txData = BinaryUnpacker( toUnpack )

      startPos = txData.getPosition()
      self.inputs     = []
      self.outputs    = []
      self.version    = txData.get(UINT32)
      numInputs  = txData.get(VAR_INT)
      for i in xrange(numInputs):
         self.inputs.append( PyTxIn().unserialize(txData) )
      numOutputs = txData.get(VAR_INT)
      for i in xrange(numOutputs):
         self.outputs.append( PyTxOut().unserialize(txData) )
      self.lockTime   = txData.get(UINT32)
      endPos = txData.getPosition()
      self.nBytes = endPos - startPos
      self.thisHash = hash256(self.serialize())
      return self
   
   # Before broadcasting a transaction make sure that the script is canonical
   # This TX could have been signed by an older version of the software.
   # Either on the offline Armory installation which may not have been upgraded
   # or on a previous installation of Armory on this computer.
   def minimizeDERSignaturePadding(self):
      paddingRemoved = False
      newTx = self.copy()
      newTx.inputs = []
      for txIn in self.inputs:
         paddingRemovedFromTxIn, newTxIn  = txIn.minimizeDERSignaturePadding() 
         if paddingRemovedFromTxIn:
            paddingRemoved = True
            newTx.inputs.append(newTxIn)
         else:
            newTx.inputs.append(txIn)
            
      return paddingRemoved, newTx.copy()
         
   def getHash(self):
      return hash256(self.serialize())

   def getHashHex(self, endianness=LITTLEENDIAN):
      return binary_to_hex(self.getHash(), endOut=endianness)

   def makeRecipientsList(self):
      """ 
      Make a list of lists, each one containing information about 
      an output in this tx.  Usually contains
         [ScriptType, Value, Addr160]
      May include more information if any of the scripts are multi-sig,
      such as public keys and multi-sig type (M-of-N)
      """
      recipInfoList = []
      for txout in self.outputs:
         recipInfoList.append([])

         scrType = getTxOutScriptType(txout.binScript)
         recipInfoList[-1].append(scrType)
         recipInfoList[-1].append(txout.value)
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            recipInfoList[-1].append(TxOutScriptExtractAddr160(txout.binScript))
         elif scrType in (TXOUT_SCRIPT_MULTISIG,):
            mstype, addr160s, pubs = getTxOutMultiSigInfo(txout.binScript)
            recipInfoList[-1].append(addr160s)
            recipInfoList[-1].append(pubs)
            recipInfoList[-1].append(mstype[0]) # this is M (from M-of-N)
         elif scrType in (TXOUT_SCRIPT_OP_EVAL,):
            LOGERROR('OP_EVAL doesn\'t exist anymore.  How did we get here?')
            recipInfoList[-1].append(txout.binScript)
         elif scrType in (TXOUT_SCRIPT_UNKNOWN,):
            LOGERROR('Unknown TxOut type')
            recipInfoList[-1].append(txout.binScript)
         else:
            LOGERROR('Unrecognized txout script that isn\'t TXOUT_SCRIPT_UNKNOWN...?')
      return recipInfoList


   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'Transaction:'
      print indstr + indent + 'TxHash:   ', self.getHashHex(endian), \
                                    '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'Version:  ', self.version
      print indstr + indent + 'nInputs:  ', len(self.inputs)
      print indstr + indent + 'nOutputs: ', len(self.outputs)
      print indstr + indent + 'LockTime: ', self.lockTime
      print indstr + indent + 'Inputs: '
      for inp in self.inputs:
         inp.pprint(nIndent+2, endian=endian)
      print indstr + indent + 'Outputs: '
      for out in self.outputs:
         out.pprint(nIndent+2, endian=endian)
         
   def toString(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      result = indstr + 'Transaction:'
      result = ''.join([result, '\n',  indstr + indent + 'TxHash:   ', self.getHashHex(endian), \
                                    '(BE)' if endian==BIGENDIAN else '(LE)'])
      result = ''.join([result, '\n',   indstr + indent + 'Version:  ', str(self.version)])
      result = ''.join([result, '\n',   indstr + indent + 'nInputs:  ', str(len(self.inputs))])
      result = ''.join([result, '\n',   indstr + indent + 'nOutputs: ', str(len(self.outputs))])
      result = ''.join([result, '\n',   indstr + indent + 'LockTime: ', str(self.lockTime)])
      result = ''.join([result, '\n',   indstr + indent + 'Inputs: '])
      for inp in self.inputs:
         result = ''.join([result, '\n',   inp.toString(nIndent+2, endian=endian)])
      print indstr + indent + 'Outputs: '
      for out in self.outputs:
         result = ''.join([result, '\n',  out.toString(nIndent+2, endian=endian)])
      return result
         
   def fetchCpp(self):
      """ Use the info in this PyTx to get the C++ version from TheBDM """
      return TheBDM.getTxByHash(self.getHash())

   def pprintHex(self, nIndent=0):
      bu = BinaryUnpacker(self.serialize())
      theSer = self.serialize()
      print binary_to_hex(bu.get(BINARY_CHUNK, 4))
      nTxin = bu.get(VAR_INT)
      print 'VAR_INT(%d)' % nTxin
      for i in range(nTxin):
         print binary_to_hex(bu.get(BINARY_CHUNK,32))
         print binary_to_hex(bu.get(BINARY_CHUNK,4))
         scriptSz = bu.get(VAR_INT)
         print 'VAR_IN(%d)' % scriptSz
         print binary_to_hex(bu.get(BINARY_CHUNK,scriptSz))
         print binary_to_hex(bu.get(BINARY_CHUNK,4))
      nTxout = bu.get(VAR_INT)
      print 'VAR_INT(%d)' % nTxout
      for i in range(nTxout):
         print binary_to_hex(bu.get(BINARY_CHUNK,8))
         scriptSz = bu.get(VAR_INT)
         print binary_to_hex(bu.get(BINARY_CHUNK,scriptSz))
      print binary_to_hex(bu.get(BINARY_CHUNK, 4))






################################################################################
################################################################################
# This class can be used for both multi-signature tx collection, as well as
# offline wallet signing (you are collecting signatures for a 1-of-1 tx only
# involving yourself).
class PyTxDistProposal(object):
   """
   PyTxDistProposal is created from a PyTx object, and represents
   an unsigned transaction, that may require the signatures of
   multiple parties before being accepted by the network.

   This technique (https://en.bitcoin.it/wiki/BIP_0010) is that 
   once TxDP is created, the system signing it only needs the 
   ECDSA private keys and nothing else.   This enables the device
   providing the signatures to be extremely lightweight, since it
   doesn't have to store the blockchain.

   For a given TxDP, we will be storing the following structure
   in memory.  Use a 3-input tx as an example, with the first 
   being a 2-of-3 multi-sig transaction (unsigned)
      
      self.scriptTypes    = [TXOUT_SCRIPT_MULTISIG, 
                             TXOUT_SCRIPT_STANDARD,   
                             TXOUT_SCRIPT_STANDARD]

      self.inputValues    = [ 2313000000, 
                              400000000, 
                              1000000000]

      self.signatures     = [ ['', '', ''],
                              [''],
                              [''],         ]

      self.inAddr20Lists  = [ [addr1, addr2, addr3],
                              [addr4]
                              [addr5]         ]

      # Usually only have public keys on multi-sig TxOuts
      self.inPubKeyLists  = [ [pubKey1, pubKey2, pubKey3],
                              ['']
                              ['']         ]   

      self.numSigsNeeded  = [ 2
                              1
                              1 ]

      self.relevantTxMap  = [ prevTx0Hash: prevTx0.serialize(),
                              prevTx1Hash: prevTx1.serialize(),
                              prevTx2Hash: prevTx2.serialize() ]
      
   UPDATE Feb 2012:  Before Jan 29, 2012, BIP 0010 used a different technique
                     for communicating blockchain information to the offline
                     device.  This is no longer the case
                     
                     Gregory Maxwell identified a reasonable-enough security
                     risk with the fact that previous BIP 0010 cannot guarantee 
                     validity of stated input values in a TxDP.  This is solved
                     by adding the supporting transactions to the TxDP, so that 
                     the signing device can get the input values from those 
                     tx and verify the hash matches the OutPoint on the tx 
                     being signed (which *is* part of what's being signed).  
                     The concern was that someone could manipulate your online
                     computer to misrepresent the inputs, and cause you to 
                     send you entire wallet to tx-fees.  Not the most useful
                     attack (for someone trying to steal your coins), but it is
                     still a risk that can be avoided by adding some "bloat" to
                     the TxDP

                     
   
   """
   #############################################################################
   def __init__(self, pytx=None, txMap={}):
      self.pytxObj       = UNINITIALIZED
      self.uniqueB58     = ''
      self.scriptTypes   = []
      self.signatures    = []
      self.txOutScripts  = []
      self.inAddr20Lists = []
      self.inPubKeyLists = []
      self.inputValues   = []
      self.numSigsNeeded = []
      self.relevantTxMap = {}  # needed to support input values of each TxIn
      if pytx:
         self.createFromPyTx(pytx, txMap)

   #############################################################################
   def createFromPyTx(self, pytx, txMap={}):
      sz = len(pytx.inputs)
      self.pytxObj        = pytx.copy()
      self.uniqueB58 = binary_to_base58(hash256(pytx.serialize()))[:8]
      self.scriptTypes    = []
      self.signatures     = []
      self.txOutScripts   = []
      self.inAddr20Lists  = []
      self.inPubKeyLists  = []
      self.inputValues    = []
      self.numSigsNeeded  = []
      self.relevantTxMap  = {}  # needed to support input values of each TxIn

      if len(txMap)==0 and not TheBDM.getBDMState()=='BlockchainReady':
         # TxDP includes the transactions that supply the inputs to this 
         # transaction, so the BDM needs to be available to fetch those.
         raise BlockchainUnavailableError, ('Must input supporting transactions '
                                            'or access to the blockchain, to '
                                            'create the TxDP')
      for i in range(sz):
         # First, make sure that we have the previous Tx data available
         # We can't continue without it, since BIP 0010 will now require
         # the full tx of outputs being spent
         outpt = self.pytxObj.inputs[i].outpoint
         txhash = outpt.txHash
         txidx  = outpt.txOutIndex
         pyPrevTx = None
         if len(txMap)>0:
            # If supplied a txMap, we expect it to have everything we need
            if not txMap.has_key(txhash):
               raise InvalidHashError, ('Could not find the referenced tx '
                                        'in supplied txMap')
            pyPrevTx = txMap[txhash].copy()
         elif TheBDM.getBDMState()=='BlockchainReady':
            cppPrevTx = TheBDM.getTxByHash(txhash)
            if not cppPrevTx:
               raise InvalidHashError, 'Could not find the referenced tx'
            pyPrevTx = PyTx().unserialize(cppPrevTx.serialize())
         else:
            raise InvalidHashError, 'No previous-tx data available for TxDP'
         self.relevantTxMap[txhash] = pyPrevTx.copy()
               
           
         # Now we have the previous transaction.  We need to pull the 
         # script out of the specific TxOut so we know how it can be
         # spent.
         script =  pyPrevTx.outputs[txidx].binScript
         value  =  pyPrevTx.outputs[txidx].value
         scrType = getTxOutScriptType(script)

         self.inputValues.append(value)
         self.txOutScripts.append(str(script)) # copy it
         self.scriptTypes.append(scrType)
         self.inAddr20Lists.append([])
         self.inPubKeyLists.append([])
         self.signatures.append([])
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            self.inAddr20Lists[-1].append(TxOutScriptExtractAddr160(script))
            self.inPubKeyLists[-1].append('')
            self.signatures[-1].append('')
            self.numSigsNeeded.append(1)
         elif scrType==TXOUT_SCRIPT_MULTISIG:
            mstype, addrs, pubs = getTxOutMultiSigInfo(script)
            self.inAddr20Lists[-1] = addrs
            self.inPubKeyLists[-1] = pubs
            self.signatures[-1]    = ['']*len(addrs)
            self.numSigsNeeded[-1] = mstype[0]  # mstype for M-of-N tx is (M,N)
         elif scrType in (TXOUT_SCRIPT_OP_EVAL, TXOUT_SCRIPT_UNKNOWN):
            pass

      return self


   #############################################################################
   def createFromTxOutSelection(self, utxoSelection, recip160ValPairs, txMap={}):
      """
      This creates a TxDP for a standard transaction from a list of inputs and 
      a list of recipient-value-pairs.  

      NOTE:  I have modified this so that if the "recip" is not a 20-byte binary
             string, it is instead interpretted as a SCRIPT -- which could be
             anything, including a multi-signature transaction
      """

      pprintUnspentTxOutList(utxoSelection)
      #print sumTxOutList(utxoSelection)
      #print sum([a[1] for a in recip160ValPairs])
      assert(sumTxOutList(utxoSelection) >= sum([a[1] for a in recip160ValPairs]))
      thePyTx = PyTx()
      thePyTx.version = 1
      thePyTx.lockTime = 0
      thePyTx.inputs = []
      thePyTx.outputs = []

      # We can prepare the outputs, first
      for recipObj,value in recip160ValPairs:
         txout = PyTxOut()
         txout.value = long(value)

         # Assume recipObj is either a PBA or a string
         if isinstance(recipObj, PyBtcAddress):
            recipObj = recipObj.getAddr160()

         # Now recipObj is def a string
         if len(recipObj)!=20:
            # If not an address, it's a full script
            txout.binScript = recipObj
         else:
            # Construct a std TxOut from addr160 str
            txout.binScript = hash160_to_p2pkhash_script(recipObj)
            #txout.binScript = ''.join([  getOpCode('OP_DUP'        ), \
                                         #getOpCode('OP_HASH160'    ), \
                                         #'\x14',                      \
                                         #recipObj,
                                         #getOpCode('OP_EQUALVERIFY'), \
                                         #getOpCode('OP_CHECKSIG'   )])

         thePyTx.outputs.append(txout)

      # Prepare the inputs based on the utxo objects
      for iin,utxo in enumerate(utxoSelection):
         # First, make sure that we have the previous Tx data available
         # We can't continue without it, since BIP 0010 will now require
         # the full tx of outputs being spent
         txin = PyTxIn()
         txin.outpoint = PyOutPoint()
         txin.binScript = ''
         txin.intSeq = 2**32-1

         txhash = utxo.getTxHash()
         txidx  = utxo.getTxOutIndex()
         txin.outpoint.txHash = str(txhash)
         txin.outpoint.txOutIndex = txidx
         thePyTx.inputs.append(txin)

      return self.createFromPyTx(thePyTx, txMap)


   #############################################################################
   # Currently not used, but may be when we finally implement multi-sig (or coinjoin)
   def appendSignature(self, binSig, txinIndex=None):
      """
      Use this to add a signature to the TxDP object in memory.
      """
      idx, pos, addr = self.processSignature(binSig, txinIndex, checkAllInputs=True)
      if addr:
         self.signatures[idx].append(binSig)
         return True
   
      return False

   #############################################################################
   def processSignature(self, sigStr, txinIdx, checkAllInputs=False):
      """
      For standard transaction types, the signature field is actually the raw
      script to be plugged into the final transaction that allows it to eval
      to true -- except for multi-sig transactions.  We have to mess with the 
      data a little bit if we want to use the script-processor to verify the
      signature.  Instead, we will use the crypto ops directly.

      The return value is everything we need to know about this signature:
      -- TxIn-index:    if checkAllInputs=True, we need to know which one worked
      -- Addr-position: for multi-sig tx, we need to know which addr it matches
      -- Addr160:       address to which this signature corresponds
      """

      if txinIdx==None or txinIdx<0 or txinIdx>=len(self.pytxObj.inputs):
         pass
      else:
         scriptType = self.scriptTypes[txinIdx]
         txCopy = self.pytxObj.copy()
         if scriptType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            # For standard Tx types, sigStr is the full script itself (copy it)
            txCopy.inputs[txinIdx].binScript = str(sigStr)
            prevOutScript = str(self.txOutScripts[txinIdx])
            psp = PyScriptProcessor(prevOutScript, txCopy, txinIdx)
            if psp.verifyTransactionValid():
               return txinIdx, 0, TxOutScriptExtractAddr160(prevOutScript)
         elif scriptType == TXOUT_SCRIPT_MULTISIG:
            pass
            '''
            # For multi-sig, sigStr is the raw ECDSA sig ... we will have to
            # manually construct a tx that the script processor can check,
            # without the other signatures
            for i in range(len(txCopy.inputs)):
               if not i==idx:
                  txCopy.inputs[i].binScript = ''
               else:
                  txCopy.inputs[i].binScript = self.txOutScripts[i]
   
            hashCode   = binary_to_int(sigStr[-1])
            hashCode4  = int_to_binary(hashcode, widthBytes=4)
            preHashMsg = txCopy.serialize() + hashCode4
            if not hashCode==1:
               raise NotImplementedError, 'Non-standard hashcodes not supported!'
   
            # Now check all public keys in the multi-sig TxOut script
            for i,pubkey in enumerate(self.inPubKeyLists):
               tempAddr = PyBtcAddress().createFromPublicKeyData(pubkey)
               if tempAddr.verifyDERSignature(preHashMsg, sigStr):
                  return txInIdx, i, hash160(pubkey)
            '''

      if checkAllInputs:
         for i in range(len(self.pytxObj.inputs)):
            idx, pos, addr160 = self.processSignature(sigStr, i)
            if idx>0:
               return idx, pos, addr160
         
      return -1,-1,''
      

   #############################################################################
   def checkTxHasEnoughSignatures(self, alsoVerify=False):
      """
      This method only counts signatures, unless verify==True
      """
      for i in range(len(self.pytxObj.inputs)):
         numSigsHave = sum( [(1 if sig else 0) for sig in self.signatures[i]] )
         if numSigsHave<self.numSigsNeeded[i]:
            return False

      if not alsoVerify:
         return True

      if not self.getBroadcastTxIfReady():
         return False

      return True
      
      
      
            

   #############################################################################
   def getBroadcastTxIfReady(self):
      try:
         return self.prepareFinalTx()
      except SignatureError, msg:
         return None
      # Let all other exceptions go on up the chain
   

   
   #############################################################################
   def isSigValidForInput(self, i):
      """
      For now we assume that each input only requires one signature, and thus 
      we have it or we don't.  In the future, this will be expanded for the 
      multi-sig case, and return a list signatures needed and which ones are 
      signed/valid
      """
      psp = PyScriptProcessor()
      # STUB -- will get to this when I need it



   #############################################################################
   def prepareFinalTx(self):
      """
      This converts the TxDP back into a regular PyTx object, verifying
      signatures as it goes.  Throw an error if the TxDP does not have
      the complete set of valid signatures needed to be accepted by the 
      network.
      """
      if not self.checkTxHasEnoughSignatures():
         return None

      # We must make/modify a copy of the TxDP, because serialization relies
      # on having the original TxDP intact.
      finalTx = self.pytxObj.copy()

      # Put the txIn scripts together (non-trivial for multi-sig cases)
      # then run them through the script evaluator to make sure they
      # are valid. 
      psp = PyScriptProcessor()
      for i,txin in enumerate(finalTx.inputs):
         if self.scriptTypes[i] in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            finalTx.inputs[i].binScript = self.signatures[i][0]
         elif self.scriptTypes[i]==TXOUT_SCRIPT_MULTISIG:
            sortedSigs = ['']*len(self.inAddr20Lists[i])
            for sig in self.signatures[i]:
               idx, pos, addr = self.processSignature(sig, i)
               if not addr:
                  raise SignatureError, 'Sig is not valid for input', i
               else:
                  sortedSigs[pos] = sig
            finalTx.inputs[i].binScript = getOpCode('OP_0') + ''.join(sortedSigs)

         psp.setTxObjects(self.txOutScripts[i], finalTx, i)
         totalScriptValid = psp.verifyTransactionValid()
         if not totalScriptValid:
            LOGWARN('Invalid script for input %d:')
            pprintScript(finalTx.inputs[i].binScript, 2)
            LOGWARN('Spending txout script:')
            pprintScript(self.txOutScripts[i], 2)
            raise SignatureError, 'Invalid script for input %d' % i
         else:
            if len(self.inAddr20Lists)==1: print 'Signature', i, 'is valid!'
            else: LOGDEBUG('Signatures for input %d are valid!', i)
      return finalTx


   #############################################################################
   def serializeAscii(self):
      txdpLines = []
      headline = ('-----BEGIN-TRANSACTION-' + self.uniqueB58 + '-----').ljust(80,'-')
      txdpLines.append( headline )
      dpsz = len(self.pytxObj.serialize())
      pieces = ['', 'TXDIST', binary_to_hex(MAGIC_BYTES), self.uniqueB58, \
                      int_to_hex(dpsz, widthBytes=2, endOut=BIGENDIAN)]
      txdpLines.append('_'.join(pieces))
      
      # First tx is always the tx being created/signed, others are supporting tx
      try:
         txList = [self.pytxObj.serialize()]
         txList.extend([self.relevantTxMap[txin.outpoint.txHash].serialize() \
                                                for txin in self.pytxObj.inputs])
      except KeyError:
         raise InvalidHashError, ('One or more OutPoints could not be found -- '
                                  'the TxDP could not be serialized')

      txHex = binary_to_hex(''.join(txList))
      for byte in range(0,len(txHex),80):
         txdpLines.append( txHex[byte:byte+80] )

      for iin,txin in enumerate(self.pytxObj.inputs):
         if self.inputValues[iin]:
            formattedVal = coin2str(self.inputValues[iin], ndec=8)
         else:
            formattedVal = '0'

         txdpLines.append('_TXINPUT_%02d_%s' % (iin, formattedVal.strip()))
         for s,sig in enumerate(self.signatures[iin]):
            if len(sig)==0:
               continue
            addrB58 = hash160_to_addrStr(self.inAddr20Lists[iin][s])
            sigsz = int_to_hex(len(sig), widthBytes=2, endOut=BIGENDIAN)
            txdpLines.append('_SIG_%s_%02d_%s' % (addrB58, iin, sigsz))
            sigHex = binary_to_hex(sig)
            for byte in range(0,len(sigHex),80):
               txdpLines.append( sigHex[byte:byte+80] )

      endline = ('-------END-TRANSACTION-' + self.uniqueB58 + '-----').ljust(80,'-')
      txdpLines.append( endline )
      LOGPPRINT(self, logging.DEBUG)
      return '\n'.join(txdpLines)
      

   #############################################################################
   def unserializeAscii(self, asciiStr):
      txdpTxt = [line.strip() for line in asciiStr.split('\n')]

      # Why can't I figure out the best way to do this with generators?
      # I know there's a bettery [python-]way to do this...
      L = [0]
      def nextLine(i):
         s = txdpTxt[i[0]].strip()
         i[0] += 1
         return s

      line = nextLine(L)
      while not ('BEGIN-TRANSACTION' in line):
         line = nextLine(L)

      # Get the network, dp ID and number of bytes
      line = nextLine(L)
      magicBytesHex, dpIdB58, dpsz = line.split('_')[2:]
      magic = hex_to_binary(magicBytesHex)

      # Read in the full, hex, tx list: first one is to be signed, remaining
      # are there to support verification of input values
      dpser = ''
      line = nextLine(L)
      while not 'TXINPUT' in line:
         dpser += line
         line = nextLine(L)

      txListBin = hex_to_binary(dpser) 
      binUnpacker = BinaryUnpacker(txListBin)
      txList = []
      targetTx = PyTx().unserialize(binUnpacker)
      while binUnpacker.getRemainingSize() > 0:
         nextTx = PyTx().unserialize(binUnpacker)
         self.relevantTxMap[nextTx.getHash()] = nextTx

      for txin in targetTx.inputs:
         if not self.relevantTxMap.has_key(txin.outpoint.txHash):
            raise TxdpError, 'Not all inputs can be verified for TxDP.  Aborting!'

      self.createFromPyTx( targetTx, self.relevantTxMap )
      numIn = len(self.pytxObj.inputs)

      # Do some sanity checks
      if not self.uniqueB58 == dpIdB58:
         raise UnserializeError, 'TxDP: Actual DPID does not match listed ID'
      if not MAGIC_BYTES==magic:
         raise NetworkIDError, 'TxDP is for diff blockchain! (%s)' % \
                                                         BLOCKCHAINS[magic]

      # At this point, we should have a TxDP constructed, now we need to 
      # simply scan the rest of the serialized structure looking for any
      # signatures that may be included
      while not 'END-TRANSACTION' in line: 
         [iin, val] = line.split('_')[2:]
         iin = int(iin)
         self.inputValues[iin] = str2coin(val)
         
         line = nextLine(L)
         while '_SIG_' in line:
            addrB58, sz, sigszHex = line.split('_')[2:]
            sz = int(sz) 
            sigsz = hex_to_int(sigszHex, endIn=BIGENDIAN)
            hexSig = ''
            line = nextLine(L)
            while (not '_SIG_' in line)   and \
                  (not 'TXINPUT' in line) and \
                  (not 'END-TRANSACTION' in line):
               hexSig += line
               line = nextLine(L)
            binSig = hex_to_binary(hexSig)
            idx, sigOrder, addr160 = self.processSignature(binSig, iin)
            if idx == -1:
               LOGWARN('Invalid sig: Input %d, addr=%s' % (iin, addrB58))
            elif not hash160_to_addrStr(addr160)== addrB58:
               LOGERROR('Listed addr does not match computed addr')
               raise BadAddressError 
            # If we got here, the signature is valid!
            self.signatures[iin][sigOrder] = binSig

      return self
      


   #############################################################################
   def pprint(self, indent='   '):
      tx = self.pytxObj
      propID = hash256(tx.serialize())
      print indent+'Distribution Proposal : ', binary_to_base58(propID)[:8]
      print indent+'Transaction Version   : ', tx.version
      print indent+'Transaction Lock Time : ', tx.lockTime
      print indent+'Num Inputs            : ', len(tx.inputs)
      for i,txin in enumerate(tx.inputs):
         prevHash = txin.outpoint.txHash
         prevIndex = txin.outpoint.txOutIndex
         #print '   PrevOut: (%s, index=%d)' % (binary_to_hex(prevHash[:8]),prevIndex),
         print indent*2 + 'Value: %s' % self.inputValues[i]
         print indent*2 + 'SrcScript:   %s' % binary_to_hex(self.txOutScripts[i])
         for ns, sig in enumerate(self.signatures[i]):
            print indent*2 + 'Sig%d = "%s"'%(ns, binary_to_hex(sig))
      print indent+'Num Outputs           : ', len(tx.outputs)
      for i,txout in enumerate(tx.outputs):
         print '   Recipient: %s BTC' % coin2str(txout.value),
         scrType = getTxOutScriptType(txout.binScript)
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            print hash160_to_addrStr(TxOutScriptExtractAddr160(txout.binScript))
         elif scrType in (TXOUT_SCRIPT_MULTISIG,):
            mstype, addrs, pubs = getTxOutMultiSigInfo(txout.binScript)
            print 'MULTI-SIG-SCRIPT:%d-of-%d' % mstype
            for addr in addrs:
               print indent*2, hash160_to_addrStr(addr)


################################################################################
# NOTE:  This method was actually used to create the Blockchain-reorg unit-
#        test, and hence why coinbase transactions are supported.  However,
#        for normal transactions supported by PyBtcEngine, this support is
#        unnecessary.
#
#        Additionally, this method both creates and signs the tx:  however
#        PyBtcEngine employs TxDistProposals which require the construction
#        and signing to be two separate steps.  This method is not suited
#        for most of the armoryengine CONOPS.
#
#        On the other hand, this method DOES work, and there is no reason
#        not to use it if you already have PyBtcAddress-w-PrivKeys avail
#        and have a list of inputs and outputs as described below.
#
# This method will take an already-selected set of TxOuts, along with
# PyBtcAddress objects containing necessary the private keys
#
#    Src TxOut ~ {PyBtcAddr, PrevTx, PrevTxOutIdx}  --OR--  COINBASE = -1
#    Dst TxOut ~ {PyBtcAddr, value}
#
# Of course, we usually don't have the private keys of the dst addrs...
#
def PyCreateAndSignTx(srcTxOuts, dstAddrsVals):
   newTx = PyTx()
   newTx.version    = 1
   newTx.lockTime   = 0
   newTx.inputs     = []
   newTx.outputs    = []


   numInputs  = len(srcTxOuts)
   numOutputs = len(dstAddrsVals)

   coinbaseTx = False
   if numInputs==1 and srcTxOuts[0] == -1:
      coinbaseTx = True


   #############################
   # Fill in TxOuts first
   for i in range(numOutputs):
      txout       = PyTxOut()
      txout.value = dstAddrsVals[i][1]
      dstAddr     = dstAddrsVals[i][0]
      if(coinbaseTx):
         txout.binScript = pubkey_to_p2pk_script(dst.binPublicKey65.toBinStr())
         #txout.binScript = ''.join([  '\x41',                      \
                                      #dstAddr.binPublicKey65.toBinStr(),  \
                                      #getOpCode('OP_CHECKSIG'   )])
      else:
         txout.binScript = hash160_to_p2pkhash_script(dst.getAddr160())
         #txout.binScript = ''.join([  getOpCode('OP_DUP'        ), \
                                      #getOpCode('OP_HASH160'    ), \
                                      #'\x14',                      \
                                      #dstAddr.getAddr160(),        \
                                      #getOpCode('OP_EQUALVERIFY'), \
                                      #getOpCode('OP_CHECKSIG'   )])

      newTx.outputs.append(txout)


   #############################
   # Create temp TxIns with blank scripts
   for i in range(numInputs):
      txin = PyTxIn()
      txin.outpoint = PyOutPoint()
      if(coinbaseTx):
         txin.outpoint.txHash = '\x00'*32
         txin.outpoint.txOutIndex     = binary_to_int('\xff'*4)
      else:
         txin.outpoint.txHash = hash256(srcTxOuts[i][1].serialize())
         txin.outpoint.txOutIndex     = srcTxOuts[i][2]
      txin.binScript = ''
      txin.intSeq = 2**32-1
      newTx.inputs.append(txin)


   #############################
   # Now we apply the ultra-complicated signature procedure
   # We need a copy of the Tx with all the txin scripts blanked out
   txCopySerialized = newTx.serialize()
   for i in range(numInputs):
      if coinbaseTx:
         pass
      else:
         txCopy     = PyTx().unserialize(txCopySerialized)
         srcAddr    = srcTxOuts[i][0]
         txoutIdx   = srcTxOuts[i][2]
         prevTxOut  = srcTxOuts[i][1].outputs[txoutIdx]
         binToSign  = ''

         assert(srcAddr.hasPrivKey())

         # Only implemented one type of hashing:  SIGHASH_ALL
         hashType   = 1  # SIGHASH_ALL
         hashCode1  = int_to_binary(1, widthBytes=1)
         hashCode4  = int_to_binary(1, widthBytes=4)

         # Copy the script of the TxOut we're spending, into the txIn script
         txCopy.inputs[i].binScript = prevTxOut.binScript
         preHashMsg = txCopy.serialize() + hashCode4

         # CppBlockUtils::CryptoECDSA modules do the hashing for us
         ##binToSign = hash256(preHashMsg)
         ##binToSign = binary_switchEndian(binToSign)

         signature = srcAddr.generateDERSignature(preHashMsg)


         # If we are spending a Coinbase-TxOut, only need sig, no pubkey
         # Don't forget to tack on the one-byte hashcode and consider it part of sig
         if len(prevTxOut.binScript) > 30:
            sigLenInBinary = int_to_binary(len(signature) + 1)
            newTx.inputs[i].binScript = sigLenInBinary + signature + hashCode1
         else:
            pubkey = srcAddr.binPublicKey65.toBinStr()
            sigLenInBinary    = int_to_binary(len(signature) + 1)
            pubkeyLenInBinary = int_to_binary(len(pubkey)   )
            newTx.inputs[i].binScript = sigLenInBinary    + signature + hashCode1 + \
                                        pubkeyLenInBinary + pubkey

   #############################
   # Finally, our tx is complete!
   return newTx

#############################################################################
def getFeeForTx(txHash):
   if TheBDM.getBDMState()=='BlockchainReady':
      if not TheBDM.hasTxWithHash(txHash):
         LOGERROR('Attempted to get fee for tx we don\'t have...?  %s', \
                                             binary_to_hex(txHash,BIGENDIAN))
         return 0
      txref = TheBDM.getTxByHash(txHash)
      valIn, valOut = 0,0
      for i in range(txref.getNumTxIn()):
         valIn += TheBDM.getSentValue(txref.getTxInCopy(i))
      for i in range(txref.getNumTxOut()):
         valOut += txref.getTxOutCopy(i).getValue()
      return valIn - valOut
      

#############################################################################
def determineSentToSelfAmt(le, wlt):
   """
   NOTE:  this method works ONLY because we always generate a new address
          whenever creating a change-output, which means it must have a
          higher chainIndex than all other addresses.  If you did something 
          creative with this tx, this may not actually work.
   """
   amt = 0
   if TheBDM.isInitialized() and le.isSentToSelf():
      txref = TheBDM.getTxByHash(le.getTxHash())
      if not txref.isInitialized():
         return (0, 0)
      if txref.getNumTxOut()==1:
         return (txref.getTxOutCopy(0).getValue(), -1)
      maxChainIndex = -5
      txOutChangeVal = 0
      changeIndex = -1
      valSum = 0
      for i in range(txref.getNumTxOut()):
         valSum += txref.getTxOutCopy(i).getValue()
         addr160 = CheckHash160(txref.getTxOutCopy(i).getScrAddressStr())
         addr    = wlt.getAddrByHash160(addr160)
         if addr and addr.chainIndex > maxChainIndex:
            maxChainIndex = addr.chainIndex
            txOutChangeVal = txref.getTxOutCopy(i).getValue()
            changeIndex = i
                  
      amt = valSum - txOutChangeVal
   return (amt, changeIndex)


################################################################################
#def getUnspentTxOutsForAddrList(addr160List, utxoType='Sweep', startBlk=-1, \
def getUnspentTxOutsForAddr160List(addr160List, utxoType='Sweep', startBlk=-1, \
                                 abortIfBDMBusy=False):
   """

   You have a list of addresses (or just one) and you want to get all the 
   unspent TxOuts for it.  This can either be for computing its balance, or
   for sweeping the address(es).

   This will return a list of pairs of [addr160, utxoObj]
   This isn't the most efficient method for producing the pairs

   NOTE:  At the moment, this only gets STANDARD TxOuts... non-std uses 
          a different BDM call

   This method will return null output if the BDM is currently in the
   middle of a scan.  You can use waitAsLongAsNecessary=True if you
   want to wait for the previous scan AND the next scan.  Otherwise,
   you can check for bal==-1 and then try again later...

   Multi-threading update:

      This one-stop-shop method has to be blocking.  Instead, you might want 
      to register the address and rescan asynchronously, skipping this method
      entirely:

         cppWlt = Cpp.BtcWallet()
         cppWlt.addScrAddress_1_(Hash160ToScrAddr(self.getAddr160()))
         TheBDM.registerScrAddr(Hash160ToScrAddr(self.getAddr160()))
         TheBDM.rescanBlockchain(wait=False)

         <... do some other stuff ...>
   
         if TheBDM.getBDMState()=='BlockchainReady':
            TheBDM.updateWalletsAfterScan(wait=True) # fast after a rescan
            bal      = cppWlt.getBalance('Spendable')
            utxoList = cppWlt.getUnspentTxOutList()
         else:
            <...come back later...>
   """
   if TheBDM.getBDMState()=='BlockchainReady' or \
         (TheBDM.isScanning() and not abortIfBDMBusy):
      if not isinstance(addr160List, (list,tuple)):
         addr160List = [addr160List]
   
      cppWlt = Cpp.BtcWallet()
      for addr in addr160List:
         if isinstance(addr, PyBtcAddress):
            cppWlt.addScrAddress_1_(Hash160ToScrAddr(addr.getAddr160()))
         else:
            cppWlt.addScrAddress_1_(Hash160ToScrAddr(addr))
   
      TheBDM.registerWallet(cppWlt)
      currBlk = TheBDM.getTopBlockHeight()
      TheBDM.scanBlockchainForTx(cppWlt, currBlk+1 if startBlk==-1 else startBlk)
      #TheBDM.scanRegisteredTxForWallet(cppWlt, currBlk+1 if startBlk==-1 else startBlk)

      if utxoType.lower() in ('sweep','unspent','full','all','ultimate'):
         return cppWlt.getFullTxOutList(currBlk)
      elif utxoType.lower() in ('spend','spendable','confirmed'):
         return cppWlt.getSpendableTxOutList(currBlk)
      else:
         raise TypeError, 'Unknown utxoType!'
   else:
      return []

def pprintLedgerEntry(le, indent=''):
   if len(le.getScrAddr())==21:
      hash160 = CheckHash160(le.getScrAddr())
      addrStr = hash160_to_addrStr(hash160)[:12]
   else:
      addrStr = ''

   leVal = coin2str(le.getValue(), maxZeros=1)
   txType = ''
   if le.isSentToSelf():
      txType = 'ToSelf'
   else:
      txType = 'Recv' if le.getValue()>0 else 'Sent'

   blkStr = str(le.getBlockNum())
   print indent + 'LE %s %s %s %s' % \
            (addrStr.ljust(15), leVal, txType.ljust(8), blkStr.ljust(8))

# Putting this at the end because of the circular dependency
from armoryengine.BDM import TheBDM
from armoryengine.PyBtcAddress import PyBtcAddress
from armoryengine.CoinSelection import pprintUnspentTxOutList, sumTxOutList
from armoryengine.Script import PyScriptProcessor, pprintScript
