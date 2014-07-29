################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
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

from armoryengine.AsciiSerialize import AsciiSerializable

UNSIGNED_TX_VERSION = 1

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
opCodeLookup['OP_0']     = 0
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


################################################################################
def getOpCode(name):
   return int_to_binary(opCodeLookup[name], widthBytes=1)


################################################################################
def getMultisigScriptInfo(rawScript):
   """
   Gets the Multi-Sig tx type, as well as all the address-160 strings of
   the keys that are needed to satisfy this transaction.  This currently
   only identifies M-of-N transaction types, returning unknown otherwise.

   However, the address list it returns should be valid regardless of
   whether the type was unknown:  we assume all 20-byte chunks of data
   are public key hashes, and 65-byte chunks are public keys.

   M==0 (output[0]==0) indicates this isn't a multisig script
   """

   if not getTxOutScriptType(rawScript)==CPP_TXOUT_MULTISIG:
      return [0, 0, None, None]

   scrAddr = ''
   addr160List = []
   pubKeyList   = []

   M,N = 0,0

   pubKeyStr = Cpp.BtcUtils().getMultisigPubKeyInfoStr(rawScript)

   bu = BinaryUnpacker(pubKeyStr)
   M = bu.get(UINT8)
   N = bu.get(UINT8)

   if M==0:
      return [0, 0, None, None]

   for i in range(N):
      pkstr = bu.get(BINARY_CHUNK, 33)
      if pkstr[0] == '\x04':
         pkstr += bu.get(BINARY_CHUNK, 32)
      pubKeyList.append(pkstr)
      addr160List.append(hash160(pkstr))

   return M, N, addr160List, pubKeyList


################################################################################
def getHash160ListFromMultisigScrAddr(scrAddr):
   mslen = len(scrAddr) - 3
   if not (mslen%20==0 and scrAddr[0]==SCRADDR_MULTISIG_BYTE):
      raise BadAddressError('Supplied ScrAddr is not multisig!')

   catList = scrAddr[3:]
   return [catList[20*i:20*(i+1)] for i in range(len(catList)/20)]


################################################################################
# These two methods are just easier-to-type wrappers around the C++ methods
def getTxOutScriptType(script):
   return Cpp.BtcUtils().getTxOutScriptTypeInt(script)

################################################################################
# These two methods are just easier-to-type wrappers around the C++ methods
def getTxOutScriptDisplayStr(script):
   scrAddr = script_to_scrAddr(script)
   scrType = getTxOutScriptType(script)
   if scrType in CPP_TXOUT_HAS_ADDRSTR:
      return scrAddr_to_addrStr(scrAddr)
   elif scrType==CPP_TXOUT_MULTISIG:
      M, N, addrs, pubs = getMultisigScriptInfo(script)
      p2shStr = script_to_addrStr(script_to_p2sh_script(script))
      return '[Multisig %d-of-%d] (not P2SH but would be %s)' % (M,N,p2shStr)
   else:
      return '[Non-Standard Script: %s]: ' % binary_to_hex(scrAddr[1:65])


################################################################################
def getTxInScriptType(txinObj):
   """
   NOTE: this method takes a TXIN object, not just the script itself.  This
         is because this method needs to see the OutPoint to distinguish an
         UNKNOWN TxIn from a coinbase-TxIn
   """
   script = txinObj.binScript
   prevTx = txinObj.outpoint.txHash
   return Cpp.BtcUtils().getTxInScriptTypeInt(script, prevTx)

################################################################################
def getTxInP2SHScriptType(txinObj):
   """
   If this TxIn is identified as SPEND-P2SH, then it contains a subscript that
   is really a TxOut script (which must hash to the value included on the
   actual TxOut script).

   Use this to get the TxOut script type of the Spend-P2SH subscript
   """
   scrType = getTxInScriptType(txinObj)
   if not scrType==CPP_TXIN_SPENDP2SH:
      return None

   lastPush = Cpp.BtcUtils().getLastPushDataInScript(txinObj.binScript)

   return getTxOutScriptType(lastPush)


################################################################################
def TxInExtractAddrStrIfAvail(txinObj):
   rawScript  = txinObj.binScript
   prevTxHash = txinObj.outpoint.txHash
   scrType = Cpp.BtcUtils().getTxInScriptTypeInt(rawScript, prevTxHash)
   lastPush = Cpp.BtcUtils().getLastPushDataInScript(rawScript)

   if scrType in [CPP_TXIN_STDUNCOMPR, CPP_TXIN_STDCOMPR]:
      return hash160_to_addrStr( hash160(lastPush) )
   elif scrType == CPP_TXIN_SPENDP2SH:
      return binScript_to_p2shAddrStr(lastPush)
   else:
      return ''


################################################################################
def TxInExtractPreImageIfAvail(txinObj):
   rawScript  = txinObj.binScript
   prevTxHash = txinObj.outpoint.txHash
   scrType = Cpp.BtcUtils().getTxInScriptTypeInt(rawScript, prevTxHash)

   if scrType == [CPP_TXIN_STDUNCOMPR, CPP_TXIN_STDCOMPR, CPP_TXIN_SPENDP2SH]:
      return Cpp.BtcUtils().getLastPushDataInScript(rawScript)
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
   def __init__(self, txHash=None, txOutIndex=None):
      self.txHash     = txHash
      self.txOutIndex = txOutIndex

   def __eq__(self, op2):
      return self.serialize()==op2.serialize()
   def __ne__(self, op2):
      return not self.__eq__(op2)

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

      self.outpoint  = PyOutPoint().unserialize(txInData.get(BINARY_CHUNK, 36) )

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
      addrStr = TxInExtractAddrStrIfAvail(self)
      if len(addrStr)==0:
         addrStr = '<UNKNOWN>'
      print indstr + indent + 'Sender:    ', addrStr
      print indstr + indent + 'Seq:       ', self.intSeq

   def toString(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      indstr2 = indstr + indent
      result = indstr + 'PyTxIn:'
      result = ''.join([result, '\n',  indstr2 + 'PrevTxHash:', \
                  binary_to_hex(self.outpoint.txHash, endian), \
                      '(BE)' if endian==BIGENDIAN else '(LE)'])
      result = ''.join([result, '\n',  indstr2 + 'TxOutIndex:', \
                                    str(self.outpoint.txOutIndex)])
      result = ''.join([result, '\n',  indstr2 + 'Script:    ', \
                  '('+binary_to_hex(self.binScript)[:64]+'...)'])
      addrStr = TxInExtractAddrStrIfAvail(self)
      if len(addrStr)>0:
         result = ''.join([result, '\n',  indstr2 + 'Sender:    ', addrStr])
      result = ''.join([result, '\n',  indstr2 + 'Seq:       ', str(self.intSeq)])
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
      sigScript = createDERSigFromRS(rBin, sBin)
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
      """
      indstr  = indent*nIndent
      indstr2 = indent*nIndent + indent
      print indstr + 'TxOut:'
      print indstr2 + 'Value:   ', self.value, '(', float(self.value) / ONE_BTC, ')'
      txoutType = getTxOutScriptType(self.binScript)
      if txoutType in [CPP_TXOUT_STDPUBKEY33, CPP_TXOUT_STDPUBKEY65]:
         print indstr2 + 'Script: PubKey(%s) OP_CHECKSIG' % \
                                          script_to_addrStr(self.binScript)
      elif txoutType == CPP_TXOUT_STDHASH160:
         print indstr2 + 'Script: OP_DUP OP_HASH160 (%s) OP_EQUALVERIFY OP_CHECKSIG' % \
                                          script_to_addrStr(self.binScript)
      elif txoutType == CPP_TXOUT_P2SH:
         print indstr2 + 'Script: OP_HASH160 (%s) OP_EQUAL' % \
                                          script_to_addrStr(self.binScript)
      else:
         opStrList = convertScriptToOpStrings(self.binScript)
         print indstr + indent + 'Script:  ', ' '.join(opStrList)
      """
      print self.toString(nIndent, endian)

   def toString(self, nIndent=0, endian=BIGENDIAN):
      indstr  = indent*nIndent
      indstr2 = indent*nIndent + indent
      valStr, btcStr = str(self.value), str(float(self.value)/ONE_BTC)
      result = indstr + 'TxOut:\n'
      result += indstr2 + 'Value:   %s (%s)\n' % (valStr, btcStr)
      result += indstr2
      txoutType = getTxOutScriptType(self.binScript)

      if txoutType in [CPP_TXOUT_STDPUBKEY33, CPP_TXOUT_STDPUBKEY65]:
         result += 'Script:  PubKey(%s) OP_CHECKSIG \n' % \
                                          script_to_addrStr(self.binScript)
      elif txoutType == CPP_TXOUT_STDHASH160:
         result += 'Script:  OP_DUP OP_HASH160 (%s) OP_EQUALVERIFY OP_CHECKSIG' % \
                                          script_to_addrStr(self.binScript)
      elif txoutType == CPP_TXOUT_P2SH:
         result += 'Script:  OP_HASH160 (%s) OP_EQUAL' % \
                                          script_to_addrStr(self.binScript)
      else:
         opStrList = convertScriptToOpStrings(self.binScript)
         result += 'Script:  ' + ' '.join(opStrList)

      return result

#####
class PyTx(BlockComponent):
   def __init__(self):
      self.version    = UNINITIALIZED
      self.inputs     = UNINITIALIZED
      self.outputs    = UNINITIALIZED
      self.lockTime   = 0
      self.thisHash   = UNINITIALIZED

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

   def copy(self):
      return PyTx().unserialize(self.serialize())


   def makeRecipientsList(self):
      """
      Make a list of lists, each one containing information about
      an output in this tx.  Usually contains
         [ScriptType, Value, Script]
      May include more information if any of the scripts are multi-sig,
      such as public keys and multi-sig type (M-of-N)
      """
      recipInfoList = []
      for txout in self.outputs:
         recipInfoList.append([])

         scrType = getTxOutScriptType(txout.binScript)
         recipInfoList[-1].append(scrType)
         recipInfoList[-1].append(txout.value)
         recipInfoList[-1].append(txout.binScript)
         if scrType == CPP_TXOUT_MULTISIG:
            recipInfoList[-1].append(getMultisigScriptInfo(txout.binScript))
         else:
            recipInfoList[-1].append([])

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
      result = ''.join([result, '\n', indstr + indent + 'Outputs: '])
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




# Use to identify status of individual sigs on an UnsignedTxINPUT
TXIN_SIGSTAT = enum('ALREADY_SIGNED',
                    'WLT_ALREADY_SIGNED',
                    'WLT_CAN_SIGN',
                    'NO_SIGNATURE')

# Use to identify status of USTXI objects of an UnsignedTransaction obj
TX_SIGSTAT = enum('SIGNING_COMPLETE',
                  'WLT_CAN_COMPLETE',
                  'WLT_CAN_CONTRIB',
                  'CANNOT_COMPLETE')


################################################################################
# This is a container object for holding data about USTXI signing status
class InputSigningStatus(object):
   def __init__(self):
      self.M              = 0
      self.N              = 0
      self.statusN        = []
      self.statusM        = []
      self.allSigned      = False
      self.wltCanSign     = False
      self.wltIsRelevant  = False
      self.wltCanComplete = False


   def pprint(self, indent=3, lutFunc=None):
      if lutFunc is None:
         def lutDispLetter(code):
            if   code==TXIN_SIGSTAT.ALREADY_SIGNED:
               return '#'
            elif code==TXIN_SIGSTAT.WLT_ALREADY_SIGNED:
               return '@'
            elif code==TXIN_SIGSTAT.WLT_CAN_SIGN:
               return '-'
            elif code==TXIN_SIGSTAT.NO_SIGNATURE:
               return '_'
         lutFunc = lutDispLetter

      ind = ' '*indent
      print ind,
      print '(%d-of-%d)' % (self.M, self.N),
      print 'AllSigned: %s' % str(self.allSigned).ljust(6),
      print 'AllSlots:',  ' '.join([lutFunc(s) for s in self.statusN]), ' ',
      print 'ReqSorted:', ' '.join([lutFunc(s) for s in self.statusM]), ' '


################################################################################
# This is a container object for holding a list of InputSigningStatus objects
# and aggregating info about
class TxSigningStatus(object):
   def __init__(self):
      self.numInputs        = 0
      self.statusList       = []
      self.canBroadcast     = False
      self.wltCanSign       = False
      self.wltIsRelevant    = False
      self.wltAlreadySigned = False
      self.wltCanComplete   = False


   def pprint(self, indent=3, lutFunc=None):
      print ' '*indent + 'Tx has %d inputs:' % self.numInputs
      for stat in self.statusList:
         stat.pprint(indent+3, lutFunc)


################################################################################
def generatePreHashTxMsgToSign(pytx, txInIndex, prevTxOutScript, hashcode=1):
   """
   This wraps up all the complexity of:
   https://en.bitcoin.it/w/images/en/7/70/Bitcoin_OpCheckSig_InDetail.png
   into a few simple lines of code!
   (blank all scripts except this one, insert prev script, append hashcode)

   Right now only supports SIGHASH_ALL
   """
   if not hashcode==1:
      LOGERROR('Only hashcode=1 is supported at this time!')
      LOGERROR('Requested hashcode=%d' % hashcode)
      return None

   # Create a copy of the tx with all scripts blanked out
   txCopy = pytx.copy()
   for i in range(len(txCopy.inputs)):
      txCopy.inputs[i].binScript = ''

   # Set the script of the TxIn being signed, to the previous TxOut script
   txCopy.inputs[txInIndex].binScript = prevTxOutScript

   hashCode1  = int_to_binary(hashcode, widthBytes=1)
   hashCode4  = int_to_binary(hashcode, widthBytes=4, endOut=LITTLEENDIAN)
   preHashMsg = txCopy.serialize() + hashCode4
   return preHashMsg, hashCode1



################################################################################
class UnsignedTxInput(AsciiSerializable):
   """
   The name is really "UnsignedTx" input ... it is an input of an unsignedTx

   This used to be part of the PyTxDP class itself, but it didn't make sense
   to be tracking all those individual, parallel lists anymore.  So now we
   use this class to hold all the data that used to be split between half
   a dozen TxDP vars, and just store a list of these in the TxDP.

   This holds the full, raw, supporting transaction for the particular input
   needing to be signed, as well as the raw P2SH script if needed.  Can also
   store a "contributor" ID -- all UTXO inputs with the same contribID will
   be shown in the user interface as belonging to a single person/device.

   A "locator" is a 4-byte, user-specified string, that identifies where
   in a BIP32 wallet a particular address is located.  This isn't needed
   for regular Armory wallets, but may be needed in the future for HW or
   other lightweight wallets to be able to locate their keys (because they
   don't store all the keys, they compute them on-the-fly and need to be
   told the BIP32 branch where it is).

   This class will also be used to store/track signatures.  Note that for
   regular Pay2PubKeyHash scripts, "adding a signature" to this object
   means also adding a public key

   insert* inputs are either single values (for single-sig scraddrs), or
   [index, val] pairs which specify which input is associated with the val

   self.txoScript is always the exact script of the TxOut being spend

   self.scriptType is the CPP_TXOUT_TYPE of the txoScript *UNLESS* that
   script is P2SH -- then it will be the type of the P2SH subscript,
   and that subscript will be stored in self.p2shScript

   i.e.  consider a bare multisig and a P2SH multisig:

   Bare Multisig:

      scriptType == CPP_TXOUT_MULTISIG
      txoScript  == "OP_2 [KeyA] [KeyB] [KeyC] OP_3 OP_CHECKMULTISIG"
      p2shScript == ''

   Same script but using P2SH:

      scriptType == CPP_TXOUT_MULTISIG
      txoScript  == "OP_DUP [ScriptHash] OP_EQUALVERIFY"
      p2shScript == "OP_2 [KeyA] [KeyB] [KeyC] OP_3 OP_CHECKMULTISIG"

   The txoScript variable always contains the script that needs to be inserted
   into the TxIn script when signing (look at OP_CHECKSIG for details)
   """

   EQ_ATTRS_SIMPLE = ['version', 'supportTx', 'outpoint', 'txoScript', 'value',
                      'scriptType', 'contribID', 'contribLabel', 'p2shScript',
                      'sequence', 'keysListed', 'sigsNeeded']
   EQ_ATTRS_LISTS  = ['scrAddrs', 'signatures', 'wltLocators', 'pubKeys']


   #############################################################################
   def __init__(self, rawSupportTx='',
                      txoutIndex=-1,
                      p2sh=None,
                      pubKeyMap=None,
                      insertSigs=None,
                      insertWltLocs=None,
                      contribID=None,
                      contribLabel=None,
                      sequence=UINT32_MAX,
                      version=UNSIGNED_TX_VERSION):

      if not rawSupportTx:
         self.isInitialized = False
         return

      tx = PyTx().unserialize(rawSupportTx)
      txout = tx.outputs[txoutIndex]

      self.isInitialized = True

      self.version     = version
      self.supportTx   = rawSupportTx
      self.outpoint    = PyOutPoint(hash256(rawSupportTx), txoutIndex)
      self.txoScript   = txout.getScript()
      self.scriptType  = getTxOutScriptType(self.txoScript)
      self.value       = txout.getValue()
      self.contribID   = '' if contribID is None else contribID
      self.contribLabel= '' if contribLabel is None else contribLabel
      self.p2shScript  = '' if p2sh is None else p2sh
      self.sequence    = sequence

      # Each of these will be a single value for single-signature UTXOs
      self.keysListed  = 0
      self.sigsNeeded  = 0
      self.scrAddrs    = None
      self.pubKeys     = None
      self.signatures  = None
      self.wltLocators = None


      
      if pubKeyMap is not None and not isinstance(pubKeyMap, dict):
         if isinstance(pubKeyMap, (list,tuple)):
            pub = dict([[SCRADDR_P2PKH_BYTE+hash160(pk), pk] for pk in pubKeyMap])
         elif isinstance(pubKeyMap, basestring):
            pub = {SCRADDR_P2PKH_BYTE+hash160(pubKeyMap): pubKeyMap}
         else:
            LOGERROR('Invalid type for pub keys input: %s', str(type(pubKeyMap)))
            self.isInitialized = False
            return 
         pubKeyMap = pub
         

      #####
      if not self.sequence==UINT32_MAX:
         LOGWARN('WARNING: NON-MAX SEQUENCE NUMBER ON UNSIGNEDTX INPUT!')
         LOGWARN('Sequence: %d' % self.sequence)

      #####
      # If this is P2SH, let's check things, and then use the sub-script
      baseScript = self.txoScript
      if self.scriptType==CPP_TXOUT_P2SH:
         # If we're here, we should've passed in a P2SH script
         if self.p2shScript is None:
            self.isInitialized = False
            raise UstxError('No P2SH script supplied for P2SH input')

         # Sanity check tha the supplied P2SH script actually matches
         self.p2shScrAddr = script_to_scrAddr(baseScript)
         scriptHash = hash160(self.p2shScript)
         if not SCRADDR_P2SH_BYTE+scriptHash == self.p2shScrAddr:
            self.isInitialized = False
            raise InvalidScriptError, 'No P2SH script info avail for TxDP'

         # Replace script type with that of the sub-script
         # We can use the presence of p2shScript to identify it's p2sh
         # Do the rest of the processing with the baseScript though we
         # will leave self.txoScript alone since that needs to be the
         # original script
         baseScript = self.p2shScript
         self.scriptType = getTxOutScriptType(self.p2shScript)


      #####
      # Fill some of the other fields with info needed to spend the script
      if self.scriptType==CPP_TXOUT_P2SH:
         # If this is a P2SH script, we've already overwritten the script
         # type with the type of sub script.  If we're here, this means
         # that the subscript is also P2SH, which is not allowed
         raise InvalidScriptError('Cannot have recursive P2SH scripts!')
      elif self.scriptType in CPP_TXOUT_STDSINGLESIG:
         scrAddr = script_to_scrAddr(baseScript)
         if pubKeyMap is None or pubKeyMap.get(scrAddr) is None:
            raise KeyDataError('Must give pubkey map for singlesig USTXI!')
         self.sigsNeeded  = 1
         self.keysListed  = 1
         self.scrAddrs    = [scrAddr]
         self.pubKeys     = [pubKeyMap[scrAddr]]
         self.signatures  = ['']
         self.wltLocators = ['']
      elif self.scriptType==CPP_TXOUT_MULTISIG:
         M, N, a160s, pubs = getMultisigScriptInfo(baseScript)
         self.sigsNeeded   = M
         self.keysListed   = N
         self.scrAddrs     = [SCRADDR_P2PKH_BYTE+a for a in a160s]
         self.pubKeys      = pubs[:]
         self.signatures   = ['']*N
         self.wltLocators  = ['']*N
      else:
         LOGWARN("Non-standard script for TxIn %d" % i)
         pass


      # "insert*s" can either be a single values, or a list
      # of pairs [multisgIndex, pubKey]
      insertData = [(insertSigs,    self.setSignature),
                    (insertWltLocs, self.setWltLocator)]

      for insList,insFunc in insertData:
         if insList is None:
            continue

         listlist = insList
         if not isinstance(listlist, (list, tuple)):
            listlist = [[0, insList]]

         if not isinstance(listlist[0], (list, tuple)):
            listlist = [listlist]

         for idx,data in listlist:
            if idx >= self.keysListed:
               LOGERROR('Insert list has index too big')
               continue
            insFunc(idx, data)


   #############################################################################
   def setPubKey(self, msIndex, pubKey):
      self.pubKeys[msIndex] = pubKey


   #############################################################################
   def setSignature(self, msIndex, sigStr):
      LOGDEBUG('Setting signature in key index: %d' % msIndex)
      self.signatures[msIndex] = sigStr


   #############################################################################
   def setWltLocator(self, msIndex, wltLoc):
      self.wltLocators[msIndex] = wltLoc



   #############################################################################
   def getPublicKeyList(self):
      """
      This returns a list of PAIRS:  [pubkey, wltLocator]
      The wallet-locator is a client-dependent string which helps lightweight
      wallets find a particular key within their own wallet structure.  This
      would only be used by clients that don't store any keys, but always
      recompute them on the fly.  As of this writing, I'm not aware of any
      wallets doing this yet, so you can expect all wltLoc's to be empty.
      And even if they are not empty, you can still ignore it, unless you
      put the wltLoc yourself to help yourself out later!
      """
      return zip(self.pubKeys, self.wltLocators)

   #############################################################################
   def createSigScript(self, stripExtraSigs=True):
      """
      Here, we don't care what the orig script was in the TxOut being spent,
      unless it was P2SH.  It's because this method assumes that all the sigs
      are already created, valid and in the right place -- which requires the
      previous TxOut script to do (before we get to this method).

      The exception is if this is P2SH, in which case we have to append the
      script to the end of the sigScript.

      However we *do* care about the original TxOut script's TYPE, so that we
      know what data to include in the sig script.  For instance, Pay2PubKey
      scripts only require a signature, whereas Pay2PubKeyHash requires both
      a pub key and a sig.  P2SH always needs the serialized script appended
      to the end of it.
      """

      outScript = ''

      if self.scriptType in CPP_TXOUT_STDSINGLESIG and not self.signatures[0]:
         return ''


      # All signatures are already DER-encoded. 
      if self.scriptType == CPP_TXOUT_P2SH:
         raise InvalidScriptError('Nested P2SH not allowed')
      if self.scriptType in [CPP_TXOUT_STDPUBKEY33, CPP_TXOUT_STDPUBKEY65]:
         # Only need the signature to complete coinbase TxOut
         outScript = scriptPushData(self.signatures[0])
      elif self.scriptType==CPP_TXOUT_STDHASH160:
         # Gotta include the public key, too, for standard TxOuts
         serSig    = scriptPushData(self.signatures[0])
         serPubKey = scriptPushData(self.pubKeys[0])
         outScript = serSig + serPubKey
      elif self.scriptType==CPP_TXOUT_MULTISIG:
         # Serialize non-empty sigs, replace empty ones with OP_0
         sigList = self.signatures[:]
         countSigs = lambda slist: sum([ (1 if s else 0)  for s in slist ])
         if stripExtraSigs:
            # Mainnet appears to treat extra sigs as non-std.  Remove if req
            while countSigs(sigList) > self.sigsNeeded:
               sigList.pop()

         OP_0 = getOpCode('OP_0')
         pushSig = lambda sig: (scriptPushData(sig) if sig else '')
         outScript = OP_0 + ''.join([pushSig(s) for s in sigList])
      else:
         raise InvalidScriptError('Non-std script, cannot create sig script')


      # If P2SH, the script type already identifies the subscript.  But we
      # can tell because the p2shScript var will be non-empty.  All we do
      # for these types of script is append the raw p2sh script to the end
      if len(self.p2shScript) > 0:
         outScript += scriptPushData(self.p2shScript)

      return outScript


   #############################################################################
   def createTxSignature(self, pytx, sbdPrivKey, hashcode=1):
      """
      This might be a little confusing ... remember this is an input for a
      transaction which may not have been fully defined at the time this
      object was created.  We supply the final PyTx object is being signed,
      and assume that this input is one of them.  Then we produce the signature
      using the CryptoECDSA module and the supplied privKey.

      This returns a DER-encoded signature string with the 1-byte hashcode
      appended to the end
      """

      # Make sure the supplied privateKey is relevant to this USTXI
      computedPub = CryptoECDSA().ComputePublicKey(sbdPrivKey).toBinStr()
      if not computedPub in self.pubKeys:
         raise SignatureError('No PubKey that matches this privKey')

      txiIdx = -1
      for i,txin in enumerate(pytx.inputs):
         if self.outpoint.serialize()==txin.outpoint.serialize():
            txiIdx = i
            break
      else:
         raise SignatureError('No TxIn in tx that matches this USTXI')

      msg,hc = generatePreHashTxMsgToSign(pytx, txiIdx, 
                                    self.getTxoScriptToSign(), hashcode)
      sbdSig = CryptoECDSA().SignData(SecureBinaryData(msg), sbdPrivKey)
      binSig = sbdSig.toBinStr()
      return createDERSigFromRS(binSig[:32], binSig[32:]) + hc


   #############################################################################
   def insertSignature(self, sigStr, pubKey):
      """
      Returns -1 if no sig can be added, index of last sig added otherwise 
      (usually only one sig added, but if this is a multisig and has repeated
      public keys, it will insert the sig in every slot for which it is valid)
      """
      msIdx = -1
      
      while(True):
         try:
            newIdx = self.pubKeys.index(pubKey, msIdx+1)
         except ValueError:
            # Eventually we run out of slots to insert into and error out.    
            # Since we're using [].index(), exception-control-flow is easiest
            return msIdx
   
         msIdx = newIdx
         self.setSignature(msIdx, sigStr)


   #############################################################################
   def createAndInsertSignature(self, pytx, sbdPrivKey, hashcode=1):

      derSig = self.createTxSignature(pytx, sbdPrivKey, hashcode)
      computedPub = CryptoECDSA().ComputePublicKey(sbdPrivKey).toBinStr()

      msIdx = self.insertSignature(derSig, computedPub)
      return derSig, msIdx

   #############################################################################
   def verifyTxSignature(self, pytx, sigStr, pubKey=None):
      return (self.getValidIndexForSignature(pytx, sigStr, pubKey) >= 0)

   #############################################################################
   def getValidIndexForSignature(self, pytx, sigStr, pubKey=None):
      """
      IMPORTANT:  This returns the index in the self.pubKeys list, for which
                  the signature is valid!  -1 is returned if the signature is
                  not valid for any pubkey!  For boolean query, use:

                     isValid = (verifyTxSignature(...) >= 0)
      """
      txiIdx = -1
      for i,txin in enumerate(pytx.inputs):
         if self.outpoint.serialize()==txin.outpoint.serialize():
            txiIdx = i
            break
      else:
         raise SignatureError('No TxIn that matches this USTXI')


      # If we were not given a public key to use for verification,
      # recurse into this method once with each of self.pubKeys.
      # We've assumed up until now that pubkeys and p2sh script will
      # always be available with the supportingTx, all as part of the
      # USTXI class
      if pubKey is None:
         for i,pubk in enumerate(self.pubKeys):
            if self.verifyTxSignature(pytx, sigStr, pubk):
               return i
         return -1


      # If public key is supplied (including on recursion)
      try:
         msIndex = self.pubKeys.index(pubKey)
      except ValueError:
         raise KeyDataError('Supplied pubkey does not match any USTXI keys')


      rBin, sBin = getRSFromDERSig(sigStr)
      hashcode  = binary_to_int(sigStr[-1])

      # Don't forget "sigStr" has the 1-byte hashcode at the end
      msg = generatePreHashTxMsgToSign(pytx, txiIdx,
            self.getTxoScriptToSign(), hashcode)[0]
      sbdMsg = SecureBinaryData(msg)
      sbdSig = SecureBinaryData(rBin + sBin)
      sbdPub = SecureBinaryData(pubKey)
      return msIndex if CryptoECDSA().VerifyData(sbdMsg, sbdSig, sbdPub) else -1

   #############################################################################
   # make sure to sign the p2shScript if it is there, other wise sign the txoScript
   # For p2sh the txoScript is not signed, it's compared with the p2sh that
   # supplied as input, and the signatures reference that script for p2sh
   def getTxoScriptToSign(self):
      return self.p2shScript if self.p2shScript else self.txoScript
      
   #############################################################################
   def verifyAllSignatures(self, pytx):
      M = self.sigsNeeded
      N = self.keysListed
      signStat = self.evaluateSigningStatus()

      # If we don't have enough raw signatures, bail now
      if not signStat.allSigned:
         return False

      # Now check that all the raw signatures are actually value
      numValid = 0  # we'll double check sufficient sigs
      for i in range(signStat.N):
         if signStat.statusN[i] in [TXIN_SIGSTAT.ALREADY_SIGNED, \
                                    TXIN_SIGSTAT.WLT_ALREADY_SIGNED]:
            pub = self.pubKeys[i]
            sig = self.signatures[i]
            if self.verifyTxSignature(pytx, sig, pub):
               numValid +=1
            else:
               LOGERROR('Signature in USTXI is not valid')

      return (numValid >= M)


   #############################################################################
   def toJSONMap(self, lite=False):
      outjson = {}
      outjson['version']      = self.version
      outjson['magicbytes']   = binary_to_hex(MAGIC_BYTES)
      outjson['outpoint']     = binary_to_hex(self.outpoint.serialize())
      outjson['p2shscript']   = binary_to_hex(self.p2shScript)
      outjson['contribid']    = self.contribID
      outjson['contriblabel'] = self.contribLabel
      outjson['sequence']     = self.sequence
      outjson['numkeys']      = self.keysListed

      outjson['keys'] = []
      for i in range(self.keysListed):
         outjson['keys'].append({})
         outjson['keys'][i]['pubkeyhex'] = binary_to_hex(self.pubKeys[i])
         outjson['keys'][i]['dersighex'] = binary_to_hex(self.signatures[i])
         outjson['keys'][i]['wltlochex'] = binary_to_hex(self.wltLocators[i])


      # Add a few convenience keys to avoid the caller having to calcs for it
      supportPyTx = PyTx().unserialize(self.supportTx)
      txoidx = binary_to_int(self.outpoint.serialize()[-4:], LITTLEENDIAN)

      outjson['supporttxhash_le'] = supportPyTx.getHashHex()
      outjson['supporttxhash_be'] = hex_switchEndian(supportPyTx.getHashHex())
      outjson['supporttxhash']    = outjson['supporttxhash_be'] # BE is default
      outjson['supporttxoutindex']= txoidx
      outjson['inputvalue'] = supportPyTx.outputs[txoidx].value

      if not lite:
         outjson['supporttx'] = binary_to_hex(self.supportTx)

      return outjson

   #############################################################################
   def fromJSONMap(self, jsonMap, skipMagicCheck=False):

      # There is a lite version of toJSONMap(), but can't create from a lite copy
      if not 'supporttx' in jsonMap:
         raise UnserializeError('Incomplete unsigned transaction map')


      ver   = jsonMap['version']
      magic = hex_to_binary(jsonMap['magicbytes'])

      if not ver == UNSIGNED_TX_VERSION:
         LOGWARN('Unserialing USTX of different version')
         LOGWARN('   USTX    Version: %d' % ver)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      # Check the magic bytes of the lockbox match
      if not magic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    USTX    Magic: ' + binary_to_hex(magic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')

      rawSupportTx = hex_to_binary(jsonMap['supporttx'])
      txoutIndex   = jsonMap['supporttxoutindex']
      p2sh         = hex_to_binary(jsonMap['p2shscript'])
      contribID    = jsonMap['contribid']
      contribLabel = jsonMap['contriblabel']
      sequence     = jsonMap['sequence']
      
      pubkeyMap = {}
      insertSigs = []
      insertWltLocs = []
      for i in range(jsonMap['numkeys']):
         pub = hex_to_binary(jsonMap['keys'][i]['pubkeyhex'])
         sig = hex_to_binary(jsonMap['keys'][i]['dersighex'])
         loc = hex_to_binary(jsonMap['keys'][i]['wltlochex'])

         pubkeyMap[SCRADDR_P2PKH_BYTE + hash160(pub)] = pub
         insertSigs.append([i, sig])
         insertWltLocs.append([i, loc])

      self.__init__(rawSupportTx, txoutIndex, p2sh, 
                    pubkeyMap, insertSigs, insertWltLocs,
                    contribID, contribLabel, sequence)

      return self
      


   #############################################################################
   def serialize(self):
      if not self.isInitialized:
         LOGERROR('Cannot serialize an uninitialzed unsigned txin')
         return None

      tempID = binary_to_base58(hash160(self.outpoint.serialize()))[:4]

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES, 4)
      bp.put(BINARY_CHUNK, self.outpoint.serialize(), 36)
      bp.put(VAR_STR,      self.supportTx)
      bp.put(VAR_STR,      self.p2shScript)
      bp.put(VAR_STR,      self.contribID)
      bp.put(VAR_STR,      toBytes(self.contribLabel))
      bp.put(UINT32,       self.sequence)
      bp.put(VAR_INT,      self.keysListed)

      for i in range(self.keysListed):
         bp.put(VAR_STR,      self.pubKeys[i])
         bp.put(VAR_STR,      self.signatures[i])
         bp.put(VAR_STR,      self.wltLocators[i])


      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, rawBinaryData, skipMagicCheck=False):

      bu = BinaryUnpacker(rawBinaryData)
      version    = bu.get(UINT32)
      magic      = bu.get(BINARY_CHUNK, 4)
      outpt      = bu.get(BINARY_CHUNK, 36)
      suppTx     = bu.get(VAR_STR)
      p2shScr    = bu.get(VAR_STR)
      contrib    = bu.get(VAR_STR)
      contribLbl = toUnicode(bu.get(VAR_STR))
      seq        = bu.get(UINT32)
      nEntry     = bu.get(VAR_INT)

      keysiginfo = []
      pubMap, sigList, locList = {},[],[]
      for i in range(nEntry):
         pub = bu.get(VAR_STR)
         sigList.append([i, bu.get(VAR_STR)])
         locList.append([i, bu.get(VAR_STR)])
         pubMap[SCRADDR_P2PKH_BYTE+hash160(pub)] = pub


      if not outpt[:32] == hash256(suppTx):
         raise UnserializeError('OutPoint hash does not match supporting tx')

      if not seq==UINT32_MAX:
         LOGWARN('WARNING: NON-MAX SEQUENCE NUMBER ON UNSIGNEDTX INPUT!')

      if not magic==MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('WRONG NETWORK!')
         LOGERROR('   MAGIC BYTES:  ' + magic)
         LOGERROR('   Expected:     ' + MAGIC_BYTES)
         raise NetworkIDError('Network magic bytes mismatch')


      if not version==UNSIGNED_TX_VERSION:
         LOGWARN('Unserialing UnsignedTxInput of different version')
         LOGWARN('   USTX    Version: %d' % version)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      self.__init__(suppTx,
                    binary_to_int(outpt[-4:]),
                    p2shScr,
                    pubMap,
                    sigList,
                    locList,
                    contrib,
                    contribLbl,
                    seq,
                    version)

      return self

   #############################################################################
   def evaluateSigningStatus(self, cppWlt=None):

      signStatus = InputSigningStatus()

      signStatus.M = self.sigsNeeded
      signStatus.N = self.keysListed

      signStatus.statusM = [TXIN_SIGSTAT.NO_SIGNATURE]*signStatus.M
      signStatus.statusN = [TXIN_SIGSTAT.NO_SIGNATURE]*signStatus.N

      # First evaluate if we have sigs for each key, or if we *COULD* sign
      # This simply returns signed-or-notsigned if no wallet is supplied
      signStatus.wltIsRelevant = False
      signStatus.wltCanSign    = False
      for i in range(signStatus.N):
         if len(self.signatures[i]) > 0:
            signStatus.statusN[i] = TXIN_SIGSTAT.ALREADY_SIGNED

         if cppWlt and cppWlt.hasScrAddress(self.scrAddrs[i]):
            signStatus.wltIsRelevant = True
            if len(self.signatures[i]) > 0:
               signStatus.statusN[i] = TXIN_SIGSTAT.WLT_ALREADY_SIGNED
            else:
               signStatus.wltCanSign    = True
               signStatus.statusN[i] = TXIN_SIGSTAT.WLT_CAN_SIGN


      # Now we sort the results and compare to M-value to get high-level metrics
      # SIGSTAT enumeration values sort the way we ultimately want to display
      signStatus.statusM = sorted(signStatus.statusN)[:signStatus.M]

      # Since values are sorted, the last element tells us whether we're done
      signStatus.allSigned = (signStatus.statusM[-1] in \
                  [TXIN_SIGSTAT.ALREADY_SIGNED, TXIN_SIGSTAT.WLT_ALREADY_SIGNED])

      signStatus.wltCanComplete = (signStatus.statusM[-1] == TXIN_SIGSTAT.WLT_CAN_SIGN)
      return signStatus


   #############################################################################
   def pprint(self, indent=3):
      ind = ' '*indent
      txHashStr = binary_to_hex(self.outpoint.txHash, BIGENDIAN)[:8]
      txoIdx    = self.outpoint.txOutIndex
      scrType   = CPP_TXOUT_SCRIPT_NAMES[self.scriptType]

      print 'UnsignedTxInput --  %s:%d (%s)' % (txHashStr, txoIdx, scrType)



   #############################################################################
   """
   def __eq__(self, obj2):
      if not isinstance(obj2, self.__class__):
         return False

      compareAttrs = ['version', 'supportTx', 'outpoint', 'txoScript', 'value',
                      'scriptType', 'contribID', 'contribLabel', 'p2shScript',
                      'sequence', 'keysListed', 'sigsNeeded']

      compareLists = ['scrAddrs', 'signatures', 'wltLocators', 'pubKeys']
      compareMaps  = []

      for attr in compareAttrs:
         if not getattr(self, attr) == getattr(obj2, attr):
            LOGERROR('Compare failed for attribute: %s' % attr)
            LOGERROR('  self:   %s' % str(getattr(self,attr)))
            LOGERROR('  other:  %s' % str(getattr(obj2,attr)))
            return False


      for attr in compareLists:
         selfList  = getattr(self, attr)
         otherList = getattr(obj2, attr)
      
         if not len(selfList)==len(otherList):
            LOGERROR('List size compare failed for %s' % attr)
            return False

         i = -1
         for a,b in zip(selfList, otherList):
            i+=1
            if not a==b:
               LOGERROR('Failed list compare for attr %s, index %d' % (attr,i))
               return False
            
      return True


   def __ne__(self, obj2):
      return not self.__eq__(obj2)
   """





################################################################################
class NullAuthData(object):
   def __init__(self):
      pass

   def serialize(self):
      return ''

   def unserialize(self, s):
      return self

   def __eq__(self, nad2):
      return True

   def __ne__(self, nad2):
      return False

################################################################################
class DecoratedTxOut(AsciiSerializable):
   """
   The name is really "UnsignedTx" output ... it is an output of an unsignedTx

   self.authData can be anything that the offline computer will recognize
   as authentication of the owner of the txOut script.  This could be our
   planned rootkey + multiplier technique (or multiple root keys and
   multipliers, in multisig), or it could be a chain of X509 certs that
   link an ID to this script.

   As of this writing, we're not utilizing any of these auth techniques,
   yet, so we simply assume it will be None, or that it has a .serialize()
   and .unserialize() method so this class doesn't have to care

   ContribID and ContribLabel are optional fields that help in simulfunding
   situations, where there may be tons of inputs and outputs (change) that 
   would otherwise appear unrelated.  We need a way to associate them so we 
   can display intelligent stuff to the user.
   """
   def __init__(self, script=None, value=None, p2sh=None,
                      wltLocator=None, authMethod='NONE', authData=None,
                      contribID=None, contribLabel=None, 
                      version=UNSIGNED_TX_VERSION):

      if None in [script, value]:
         self.isInitialized = False
         return

      self.isInitialized = True
      self.version    = version
      self.binScript  = script
      self.value      = value
      self.p2shScript = p2sh if p2sh else ''
      self.wltLocator = wltLocator if wltLocator else ''
      self.authMethod = authMethod
      self.authData   = authData if authData else NullAuthData()
      self.contribID  = contribID if contribID else ''
      self.contribLabel = contribLabel if contribLabel else ''

      # Derived values
      self.scrAddr    = script_to_scrAddr(script)
      self.scriptType = getTxOutScriptType(script)
      self.multiInfo  = {}

      # P2SH destinations don't *require* the subscript like USTXI do
      baseScript = self.binScript
      if p2sh and self.scriptType == CPP_TXOUT_P2SH:
         self.scriptType = getTxOutScriptType(p2sh)
         baseScript = p2sh


      if self.scriptType == CPP_TXOUT_MULTISIG:
         M, N, a160s, pubs = getMultisigScriptInfo(baseScript)
         self.multiInfo['M'] = M
         self.multiInfo['N'] = N
         self.multiInfo['Addr160s'] = a160s
         self.multiInfo['PubKeys'] = pubs


   #############################################################################
   def setAuthData(self, authType, authObj):
      self.authMethod = authType
      self.authData   = authObj

   #############################################################################
   def setWltLocator(self, wltLocStr):
      self.wltLocator = wltLocStr

   #############################################################################
   def getRecipStr(self):
      if self.scriptType in CPP_TXOUT_HAS_ADDRSTR:
         return script_to_addrStr(self.binScript)
      elif self.scriptType == CPP_TXOUT_MULTISIG:
         lbID = calcLockboxID(self.binScript)
         return 'Multisig %d-of-%d (%s)' % \
            (self.multiInfo['M'], self.multiInfo['N'], lbID)
      else:
         return ''

   #############################################################################
   def toJSONMap(self):
      """
      No lite version needed, since these are usually very small.

      Below is the list of supported TXOUT types defined around line 500 in 
      armoryengine/ArmoryUtils.py.  This list will probably not be maintained
      as regularly as the one in ArmoryUtils.py, since these comments are not
      required to be accurate for the code to be functional.  Please confirm
      that it matches the ArmoryUtils list for the current version of Armory
      before relying on it.

      CPP_TXOUT_STDHASH160   = 0
      CPP_TXOUT_STDPUBKEY65  = 1
      CPP_TXOUT_STDPUBKEY33  = 2
      CPP_TXOUT_MULTISIG     = 3
      CPP_TXOUT_P2SH         = 4
      CPP_TXOUT_NONSTANDARD  = 5

      CPP_TXOUT_HAS_ADDRSTR  = [CPP_TXOUT_STDHASH160, 
                                CPP_TXOUT_STDPUBKEY65,
                                CPP_TXOUT_STDPUBKEY33,
                                CPP_TXOUT_P2SH]

      CPP_TXOUT_STDSINGLESIG = [CPP_TXOUT_STDHASH160, 
                                CPP_TXOUT_STDPUBKEY65,
                                CPP_TXOUT_STDPUBKEY33]

      CPP_TXOUT_SCRIPT_NAMES = ['']*6
      CPP_TXOUT_SCRIPT_NAMES[CPP_TXOUT_STDHASH160]  = 'Standard (PKH)'
      CPP_TXOUT_SCRIPT_NAMES[CPP_TXOUT_STDPUBKEY65] = 'Standard (PK65)'
      CPP_TXOUT_SCRIPT_NAMES[CPP_TXOUT_STDPUBKEY33] = 'Standard (PK33)'
      CPP_TXOUT_SCRIPT_NAMES[CPP_TXOUT_MULTISIG]    = 'Multi-Signature'
      CPP_TXOUT_SCRIPT_NAMES[CPP_TXOUT_P2SH]        = 'Standard (P2SH)'
      CPP_TXOUT_SCRIPT_NAMES[CPP_TXOUT_NONSTANDARD] = 'Non-Standard'
      """

      outjson = {}
      outjson['version']      = self.version
      outjson['magicbytes']   = binary_to_hex(MAGIC_BYTES)
      outjson['txoutscript']  = binary_to_hex(self.binScript)
      outjson['txoutvalue']   = self.value
      outjson['p2shscript']   = binary_to_hex(self.p2shScript)
      outjson['wltlocator']   = binary_to_hex(self.wltLocator)
      outjson['authmethod']   = self.authMethod # we expect plaintext
      outjson['authdata']     = binary_to_hex(self.authData.serialize()) # we expect this won't be
      outjson['contribid']    = self.contribID
      outjson['contriblabel'] = self.contribLabel

      # Some computed values so the caller doesn't have to deal with it
      scrType = getTxOutScriptType(self.binScript)
      outjson['scripttypeint'] = scrType  # armoryengine/ArmoryUtils.py line ~500
      outjson['scripttypestr'] = CPP_TXOUT_SCRIPT_NAMES[scrType]
      outjson['isp2sh']        = (scrType == CPP_TXOUT_P2SH)
      outjson['ismultisig']    = (scrType == CPP_TXOUT_MULTISIG)

      outjson['hasaddrstr']    = False
      outjson['addrstr']       = ''
      if scrType in CPP_TXOUT_HAS_ADDRSTR:
         outjson['hasaddrstr']    = True
         outjson['addrstr']       = script_to_addrStr(self.binScript)

      return outjson


   #############################################################################
   def fromJSONMap(self, jsonMap, skipMagicCheck=False):

      ver   = jsonMap['version'] 
      magic = hex_to_binary(jsonMap['magicbytes'])

      # Issue a warning if the versions don't match
      if not ver == UNSIGNED_TX_VERSION:
         LOGWARN('Unserialing USTX of different version')
         LOGWARN('   USTX    Version: %d' % ver)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      # Check the magic bytes of the lockbox match
      if not magic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    USTX    Magic: ' + binary_to_hex(magic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')

      script = hex_to_binary(jsonMap['txoutscript'])
      value  =               jsonMap['txoutvalue']
      p2sh   = hex_to_binary(jsonMap['p2shscript'])
      loc    = hex_to_binary(jsonMap['wltlocator'])
      meth   =               jsonMap['authmethod']
      data   = hex_to_binary(jsonMap['authdata'])
      cid    =               jsonMap['contribid']
      clbl   =               jsonMap['contriblabel']
      
      authData = NullAuthData().unserialize(data)
      self.__init__(script, value, p2sh, loc, meth, authData, cid, clbl)
      return self

   


   #############################################################################
   def serialize(self):
      if not self.isInitialized:
         LOGERROR('Cannot serialize an uninitialzed unsigned txin')
         return None

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES)
      bp.put(VAR_STR,      self.binScript)
      bp.put(UINT64,       self.value)
      bp.put(VAR_STR,      self.p2shScript)
      bp.put(VAR_STR,      self.wltLocator)
      bp.put(VAR_STR,      self.authMethod)
      bp.put(VAR_STR,      self.authData.serialize())
      bp.put(VAR_STR,      self.contribID)
      bp.put(VAR_STR,      self.contribLabel)

      return bp.getBinaryString()



   #############################################################################
   def unserialize(self, rawData, skipMagicCheck=False):
      bu = BinaryUnpacker(rawData)
      version    = bu.get(UINT32)
      magic      = bu.get(BINARY_CHUNK, 4)
      script     = bu.get(VAR_STR)
      value      = bu.get(UINT64)
      p2shScr    = bu.get(VAR_STR)
      wltLoc     = bu.get(VAR_STR)
      authMeth   = bu.get(VAR_STR)
      authData   = bu.get(VAR_STR)
      contribID  = bu.get(VAR_STR)
      contribLBL = toUnicode(bu.get(VAR_STR))

      if not magic==MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('WRONG NETWORK!')
         LOGERROR('   MAGIC BYTES:  ' + magic)
         LOGERROR('   Expected:     ' + MAGIC_BYTES)
         raise NetworkIDError('Network magic bytes mismatch')


      if not version==UNSIGNED_TX_VERSION:
         LOGWARN('Unserialing UnsignedTxInput of different version')
         LOGWARN('   USTX    Version: %d' % version)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)


      authDataObj = NullAuthData().unserialize(authData)

      self.__init__(script, value, p2shScr, wltLoc, 
                             authMeth, authDataObj, contribID, contribLBL)
      return self


   #############################################################################
   def pprint(self, indent=3):
      ind = ' '*indent
      scrType   = CPP_TXOUT_SCRIPT_NAMES[self.scriptType]

      print ind + 'Version:     ', self.version
      if self.scriptType in CPP_TXOUT_HAS_ADDRSTR:
         print ind + 'Address:     ', scrAddr_to_addrStr(self.scrAddr)
         if self.p2shScript:
            print ind + 'P2SH Script: ', binary_to_hex(self.p2shScript)[:50]

      elif self.scriptType==CPP_TXOUT_MULTISIG:
         print ind + 'Multisig:      %(M)s-of-%(N)s' % self.multiInfo
      print ind + 'Value:       ', coin2strNZS(self.value)
      print ind + 'ContribID:   ', self.contribID
      print ind + 'ContribLabel:', self.contribLabel


   #############################################################################
   def __eq__(self, obj2):

      if not isinstance(obj2, self.__class__):
         return False

      compareAttrs = ['version', 'binScript', 'value', 'p2shScript',
                      'wltLocator', 'authMethod', 'contribID', 'contribLabel',
                      'scrAddr', 'scriptType', 'multiInfo']

      compareLists = []
      compareMaps  = []

      for attr in compareAttrs:
         if not getattr(self, attr) == getattr(obj2, attr):
            LOGERROR('Compare failed for attribute: %s' % attr)
            LOGERROR('  self:   %s' % str(getattr(self,attr)))
            LOGERROR('  other:  %s' % str(getattr(obj2,attr)))
            return False


      for attr in compareLists:
         selfList  = getattr(self, attr)
         otherList = getattr(obj2, attr)
      
         if not len(selfList)==len(otherList):
            LOGERROR('List size compare failed for %s' % attr)
            return False

         i = -1
         for a,b in zip(selfList, otherList):
            i+=1
            if not a==b:
               LOGERROR('Failed list compare for attr %s, index %d' % (attr,i))
               return False
            
      return True


   def __ne__(self, obj2):
      return not self.__eq__(obj2)




################################################################################
################################################################################
# This class can be used for both multi-signature tx collection, as well as
# offline wallet signing (you are collecting signatures for a 1-of-1 tx only
# involving yourself).
class UnsignedTransaction(AsciiSerializable):
   """
   Let's call this a "USTX" to avoid confusion with "UTXO"s which are
   "unSPENT TxOut"s.

   UnsignedTransaction is basically a PyTx() object that has all the
   metadata needed for an offline device to sign it.

   The contribID is basically just the promissory note ID, if this was
   constrcuted from a collection of promissory notes.  For instance,
   we have 100 inputs to a tx, but only two contributors.  If only 12
   of those inputs have signatures (so far), then it would be good to
   know that, say, there's only two other people that need to provide
   sigs, not 88.
   """

   OBJNAME   = "UnsignedTx"
   BLKSTRING = "TXSIGCOLLECT"
   EMAILSUBJ = 'Armory Multi-sig Transaction to Sign - %s'
   EMAILBODY = """
               The chunk of text below is a proposed spending transaction 
               with all signatures available so far.  Open
               the Lockbox manager in Armory and click on "Review and Sign" 
               in the bottom row of the dashboard.  Copy this text into the
               import box, including the first and last lines.  You will be
               given the opportunity to confirm the transaction before 
               signing.  After it is signed, click "Export" in the bottom-right
               corner and send it back to me."""
           
   EQ_ATTRS_SIMPLE = ['version', 'lockTime', 'asciiID']
   EQ_ATTRS_LISTS  = ['ustxInputs', 'decorTxOuts']
               

   #############################################################################
   def __init__(self, pytx=None, pubKeyMap=None, txMap=None, p2shMap=None,
                                       version=UNSIGNED_TX_VERSION):
      self.version         = version
      self.pytxObj         = UNINITIALIZED
      self.uniqueIDB58     = ''
      self.asciiID         = ''  # need a common name for all ser/unser classes
      self.lockTime        = 0
      self.ustxInputs  = []
      self.decorTxOuts = []

      txMap   = {} if txMap   is None else txMap
      p2shMap = {} if p2shMap is None else p2shMap

      if pytx:
         self.createFromPyTx(pytx, pubKeyMap, txMap, p2shMap)


   #############################################################################
   def createFromUnsignedTxIO(self, ustxinList, dtxoList, lockTime=0):
      """
      All custom sequence numbers are set in the individual ustxi entries
      """

      nIn  = len(ustxinList)
      nOut = len(dtxoList)

      self.pytxObj = PyTx()
      self.pytxObj.version  = UNSIGNED_TX_VERSION
      self.pytxObj.lockTime = lockTime
      self.pytxObj.inputs   = [None]*nIn
      self.pytxObj.outputs  = [None]*nOut


      for iin,ustxi in enumerate(ustxinList):
         self.pytxObj.inputs[iin] = PyTxIn()
         self.pytxObj.inputs[iin].outpoint  = ustxi.outpoint
         self.pytxObj.inputs[iin].binScript = ''
         self.pytxObj.inputs[iin].intSeq    = ustxi.sequence


      for iout,dtxo in enumerate(dtxoList):
         self.pytxObj.outputs[iout] = PyTxOut()
         self.pytxObj.outputs[iout].value     = dtxo.value
         self.pytxObj.outputs[iout].binScript = dtxo.binScript

      # Create copies of the input lists
      self.ustxInputs = ustxinList[:]
      self.decorTxOuts = dtxoList[:]

      # Finally issue a warning if this selection is super high fee
      totalIn  = sum([ustxi.value for ustxi in ustxinList])
      totalOut = sum([dtxo.value  for dtxo  in dtxoList  ])
      if totalIn - totalOut > 100*MIN_RELAY_TX_FEE:
         LOGWARN('Exceptionally high fee in createFromUnsignedTxIO')
         LOGWARN('TotalInputs  = %s BTC', coin2strNZS(totalIn))
         LOGWARN('TotalOutputs = %s BTC', coin2strNZS(totalOut))
         LOGWARN('Computed Fee = %s BTC', coin2strNZS(totalIn-totalOut))
      elif totalIn - totalOut < 0:
         raise ValueError('Supplied inputs are less than the supplied outputs')

      rawTxNoSigs = self.pytxObj.serialize()
      self.uniqueIDB58 = binary_to_base58(hash256(rawTxNoSigs))[:8]
      self.asciiID = self.uniqueIDB58
      return self


   #############################################################################
   def createFromPyTx(self, pytx, pubKeyMap=None, txMap=None, p2shMap=None):
      """
      It might seem silly to convert pytx into USTXIs and DecoratedTxos, just
      to call the other method that reconstructs the same pytx object.  At
      least it all goes through the same construction method.
      """

      pubKeyMap  = {} if not pubKeyMap else pubKeyMap
      txMap   = {} if not txMap     else txMap
      p2shMap = {} if not p2shMap   else p2shMap


      if len(txMap)==0 and not TheBDM.getBDMState()=='BlockchainReady':
         # TxDP includes the transactions that supply the inputs to this
         # transaction, so the BDM needs to be available to fetch those.
         raise BlockchainUnavailableError, ('Must input supporting transactions '
                                            'or access to the blockchain, to '
                                            'create the TxDP')

      ustxiList = []
      dtxoList = []

      # Get support tx for each input and create unsignedTx-input for each
      for txin in pytx.inputs:
         # First, make sure that we have the previous Tx data available
         # We can't continue without it, since BIP 0010 will now require
         # the full tx of outputs being spent
         outpt = txin.outpoint
         txhash = outpt.txHash
         txoIdx  = outpt.txOutIndex
         pyPrevTx = None

         # Either the supporting tx was supplied in txMap, or BDM is avail
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
            raise InvalidScriptError, 'No previous-tx data available for TxDP'

         txoScript = pyPrevTx.outputs[txoIdx].binScript
         txoScrAddr = script_to_scrAddr(txoScript)
         txoType = getTxOutScriptType(txoScript)

         p2sh = None
         if txoType==CPP_TXOUT_P2SH:
            p2sh = p2shMap.get(binary_to_hex(txoScrAddr))
            if not p2sh:
               raise InvalidHashError('P2SH script not supplied')


         ustxiList.append(UnsignedTxInput(pyPrevTx.serialize(), 
                                          txoIdx, 
                                          p2sh, 
                                          pubKeyMap))



      # Create the DecoratedTxOut for each output.  Without any
      # supplemental auth info, this conversion isn't necessarily useful.
      for txout in pytx.outputs:
         scr = txout.getScript()
         val = txout.getValue()
         p2sh = p2shMap.get(script_to_scrAddr(scr)) # returns None if not P2SH

         # Append to the dtxo list
         dtxoList.append(DecoratedTxOut(scr, val, p2sh))

      return self.createFromUnsignedTxIO(ustxiList, dtxoList, pytx.lockTime)




   #############################################################################
   def createFromTxOutSelection(self, utxoSelection, scriptValuePairs,
                                pubKeyMap=None, txMap=None, p2shMap=None):

      totalUtxoSum = sumTxOutList(utxoSelection)
      totalOutputSum = sum([a[1] for a in scriptValuePairs])
      if not totalUtxoSum >= totalOutputSum:
         raise UstxError('More outputs than inputs!')

      thePyTx = PyTx()
      thePyTx.version = UNSIGNED_TX_VERSION
      thePyTx.lockTime = 0
      thePyTx.inputs = []
      thePyTx.outputs = []

      # We can prepare the outputs, first
      for script,value in scriptValuePairs:
         txout = PyTxOut()
         txout.value = long(value)

         # Assume recipObj is either a PBA or a string
         if isinstance(script, PyBtcAddress):
            LOGERROR("Didn't know any func was still using this conditional")

         intType = getTxOutScriptType(script)
         if intType==CPP_TXOUT_NONSTANDARD:
            LOGWARN('Including non-standard script output')
            LOGWARN('Script: ' + binary_to_hex(script))
            #raise BadAddressError('Invalid script for tx creation')

         txout.binScript = script[:]
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
         txoIdx  = utxo.getTxOutIndex()
         txin.outpoint.txHash = str(txhash)
         txin.outpoint.txOutIndex = txoIdx
         thePyTx.inputs.append(txin)


      return self.createFromPyTx(thePyTx, pubKeyMap, txMap, p2shMap)


   #############################################################################
   def createFromUnsignedTxInputSelection(self, ustxiList, scriptValuePairs,
                                                    p2shMap=None, lockTime=0):
      dtxoList = []
      if p2shMap is None:
         p2shMap = {}

      for scr,val in scriptValuePairs:
         p2sh = p2shMap.get(script_to_scrAddr(scr))   # Returns None if DNE
         dtxoList.append(DecoratedTxOut(scr,val,p2sh))

      return self.createFromUnsignedTxIO(ustxiList, dtxoList, lockTime)




         
   

   #############################################################################
   def calculateFee(self):
      totalIn  = sum([ustxi.value for ustxi in self.ustxInputs ])
      totalOut = sum([dtxo.value  for dtxo  in self.decorTxOuts])
      return totalIn-totalOut



   #############################################################################
   def serialize(self):
      """
      TODO:  We should consider the idea that we don't even need to serialize
             the pytxObj at all... it seems there should only be a single,
             canonical way to construct the tx.
      """
      if self.pytxObj==UNINITIALIZED:
         LOGERROR('Cannot serialize an uninitialized tx')
         return None

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES, 4)
      bp.put(UINT32,       self.lockTime)

      bp.put(VAR_INT,  len(self.ustxInputs))
      for ustxi in self.ustxInputs:
         bp.put(VAR_STR, ustxi.serialize())

      bp.put(VAR_INT,  len(self.decorTxOuts))
      for dtxo in self.decorTxOuts:
         bp.put(VAR_STR, dtxo.serialize())

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, rawData, expectID=None, skipMagicCheck=False):
      bu = BinaryUnpacker(rawData)
      ver     = bu.get(UINT32)
      magic   = bu.get(BINARY_CHUNK, 4)
      lockt   = bu.get(UINT32)

      numUSTXI = bu.get(VAR_INT)
      ustxiList = []
      for i in range(numUSTXI):
         ustxiList.append( UnsignedTxInput().unserialize(bu.get(VAR_STR), skipMagicCheck) )

      numDtxo = bu.get(VAR_INT)
      dtxoList = []
      for i in range(numDtxo):
         dtxoList.append( DecoratedTxOut().unserialize(bu.get(VAR_STR), skipMagicCheck) )

      # Issue a warning if the versions don't match
      if not ver == UNSIGNED_TX_VERSION:
         LOGWARN('Unserialing USTX of different version')
         LOGWARN('   USTX    Version: %d' % ver)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      # Check the magic bytes of the lockbox match
      if not magic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    USTX    Magic: ' + binary_to_hex(magic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')

      self.createFromUnsignedTxIO(ustxiList, dtxoList, lockt)

      # Check that we got the expect ID on the TXSIGCOLLECT
      if expectID and not expectID==self.uniqueIDB58:
         raise UnserializeError('ID on ascii block does not match computed ID')

      return self



   #############################################################################
   def toJSONMap(self, lite=False):

      if self.pytxObj==UNINITIALIZED:
         LOGERROR('Cannot serialize an uninitialized tx')
         raise ValueError('Cannot serialize an uninitialized tx')

      outjson = {}
      outjson['version'] = self.version
      outjson['magicbytes'] = binary_to_hex(MAGIC_BYTES)
      outjson['id'] = self.uniqueIDB58
      outjson['locktimeint'] = self.lockTime
      if self.lockTime < 500000000:
         outjson['locktimeblock'] = self.lockTime
         outjson['locktimedate']  = ''
      else:
         outjson['locktimeblock'] = -1
         outjson['locktimedate']  = unixTimeToFormatStr(self.lockTime)
   
      outjson['numinputs'] = len(self.ustxInputs)
      outjson['numoutputs'] = len(self.decorTxOuts)

      totalIn  = sum([ustxi.value for ustxi in self.ustxInputs ])
      totalOut = sum([dtxo.value  for dtxo  in self.decorTxOuts])
      totalFee = totalIn-totalOut

      outjson['suminputs']  = totalIn
      outjson['sumoutputs'] = totalOut
      outjson['fee']        = totalFee

      if lite:
         return outjson

      outjson['inputs'] = []
      for ustxi in self.ustxInputs:
         outjson['inputs'].append(ustxi.toJSONMap())

      outjson['outputs'] = []
      for dtxo in self.decorTxOuts:
         outjson['outputs'].append(dtxo.toJSONMap())
      
      return outjson


   #############################################################################
   def fromJSONMap(self, jsonMap, skipMagicCheck=False):
      

      if not 'inputs' in jsonMap:
         raise UnserializeError('Incomplete unsigned transaction map')

      ver   = jsonMap['version'] 
      magic = hex_to_binary(jsonMap['magicbytes'])
      uniq  = jsonMap['id']
      tlock = jsonMap['locktimeint'] 
   
      # Issue a warning if the versions don't match
      if not ver == UNSIGNED_TX_VERSION:
         LOGWARN('Unserialing USTX of different version')
         LOGWARN('   USTX    Version: %d' % ver)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      # Check the magic bytes of the lockbox match
      if not magic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    USTX    Magic: ' + binary_to_hex(magic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')

      ustxiList = []
      for ustxi in jsonMap['inputs']:
         ustxiList.append(UnsignedTxInput().fromJSONMap(ustxi, skipMagicCheck))

      dtxoList = []
      for dtxo in jsonMap['outputs']:
         dtxoList.append(DecoratedTxOut().fromJSONMap(dtxo, skipMagicCheck))

      self.createFromUnsignedTxIO(ustxiList, dtxoList, tlock)

      return self


   #############################################################################
   def evaluateSigningStatus(self, cppWlt=None):
      txSigStat = TxSigningStatus()
      txSigStat.numInputs = len(self.ustxInputs)
      txSigStat.statusList = [ustxi.evaluateSigningStatus(cppWlt) \
                                       for ustxi in self.ustxInputs]

      txSigStat.canBroadcast   = True
      txSigStat.wltCanSign     = False
      txSigStat.wltIsRelevant  = False
      txSigStat.wltCanComplete = True
      txSigStat.wltAlreadySigned = False
      #txSigStat.wltPartialSigned = False

      for inputStat in txSigStat.statusList:
         if not inputStat.allSigned:
            txSigStat.canBroadcast = False

         if inputStat.wltCanSign:
            txSigStat.wltCanSign = True

         if inputStat.wltIsRelevant:
            txSigStat.wltIsRelevant = True

         if not inputStat.wltCanComplete:
            txSigStat.wltCanComplete = False

         for statCode in inputStat.statusN:
            # WLT_CAN_SIGN is true only if it's not signed yet.  
            # Therefore, if we run into with other WLT_ALREADY_SIGNED
            # that means we're in a partial state (not sure how that happens)
            #wltCanSign = statCode == TXIN_SIGSTAT.WLT_CAN_SIGN
            wltAlready = statCode == TXIN_SIGSTAT.WLT_ALREADY_SIGNED
            #if (wltCanSign and txSigStat.wltAlreadySigned) or \
               #(wltAlready and txSigStat.wltCanSign):
               #txSigStat.wltPartialSigned = True
               #break

            if wltAlready: 
               txSigStat.wltAlreadySigned = True
               break

      return txSigStat


   #############################################################################
   def verifySigsAllInputs(self):
      for ustxi in self.ustxInputs:
         if not ustxi.verifyAllSignatures(self.pytxObj):
            return False

      return True

   #############################################################################
   def verifyInputsMatchPyTxObj(self):
      """
      This assumes that all inputs are sorted the same way.  I was going to
      make it totally generic and have a function for creating a mapping, but
      so far, I can't see how you would end up with mis-sorted data, since
      the pytxObj always is created from the ustxInputs list (originally)

      Nonetheless, it probably wouldn't be too hard to have ustxInputs
      re-sorted by this method in less then N^2 time
      """
      opList1 = [inp.outpoint.serialize() for inp in self.pytxObj.inputs]
      opList2 = [inp.outpoint.serialize() for inp in self.ustxInputs]

      #return sorted(opList1)==sorted(opList2)
      return opList1==opList2


   #############################################################################
   def getUnsignedPyTx(self, doVerifySigs=True):
      return self.pytxObj.copy()


   #############################################################################
   def getSignedPyTx(self, doVerifySigs=True, stripExtraSigs=True):
      # Make sure the USTXI list is synchronous with the pytx input list
      if not self.verifyInputsMatchPyTxObj():
         LOGERROR('Invalid USTXI set or ordering')
         return None

      finalTx = self.pytxObj.copy()

      # Check signatures are valid (if not skipped)
      # TODO: I would've used PyScriptProcessor since it evaluates the scripts
      #       as a whole, instead of just verifying the individual signatures,
      #       but it doesn't currently handle P2SH scripts properly, so it
      #       wouldn't be reliable for P2SH scripts
      if doVerifySigs:
         if not self.verifySigsAllInputs():
            LOGERROR('Attempted to prepare final tx, but not all sigs available')
            raise SignatureError('Invalid signature while preparing final tx')

      # Iterate through the lists
      for iin in range(len(self.ustxInputs)):
         ustxi = self.ustxInputs[iin]
         sigScript = ustxi.createSigScript(stripExtraSigs=stripExtraSigs)
         if not sigScript:
            return None
         finalTx.inputs[iin].binScript = sigScript

      return finalTx


   #############################################################################
   def getPyTxSignedIfPossible(self, doVerifySigs=True):
      if self.evaluateSigningStatus().canBroadcast:
         return self.getSignedPyTx()
      else:
         return self.getUnsignedPyTx()


   #############################################################################
   def isSigValidForInput(self, txInIndex, sigStr, pubKey=None):
      """
      This returns the multi-sig index
      """

      if txInIndex >= len(self.ustxInputs):
         raise SignatureError('TxIn index is out of range for this USTX')

      ustxi = self.ustxInputs[txInIndex]
      return ustxi.verifyTxSignature(self.pytxObj, sigStr, pubKey)


   #############################################################################
   def createAndInsertSignatureForInput(self, txInIndex, sbdPrivKey, hashcode=1):
      if txInIndex >= len(self.ustxInputs):
         raise SignatureError('TxIn index is out of range for this USTX')

      ustxi = self.ustxInputs[txInIndex]
      ustxi.createAndInsertSignature(self.pytxObj, sbdPrivKey, hashcode)


   #############################################################################
   def insertSignatureForInput(self, txInIndex, sigStr, pubKey=None):
      ustxi = self.ustxInputs[txInIndex]
      sigIndex = ustxi.getValidIndexForSignature(self.pytxObj, sigStr, pubKey)
      if sigIndex >= 0:
         ustxi.setSignature(sigIndex, sigStr)
         return sigIndex

      return -1

   #############################################################################
   def insertSignature(self, sigStr, pubKey=None):
      if pubKey is None or len(self.ustxInputs)>5:
         LOGWARN('Inserting sig without input index and/or pubkey will be SLOW!')

      for iin,ustxi in enumerate(self.ustxInputs):
         msIdx = ustxi.insertSignature(sigStr, pubKey)
         if msIdx >= 0:
            return msIdx

      return -1


   #############################################################################
   def getBroadcastTxIfReady(self, verifySigs=True):
      try:
         return self.getSignedPyTx(verifySigs)
      except SignatureError, msg:
         return None





   #############################################################################
   def pprint(self, indent=3):
      ind = ' '*indent
      tx = self.pytxObj
      txHash = hash256(tx.serialize())
      print ind+'UnsignedTx ID: ', self.uniqueIDB58
      print ind+'Curr TxID    : ', binary_to_hex(txHash, BIGENDIAN)
      print ind+'Version      : ', tx.version
      print ind+'Lock Time    : ', tx.lockTime
      print ind+'Fee (BTC)    : ', coin2strNZS(self.calculateFee())
      print ind+'#Inputs      : ', len(tx.inputs)

      for i,ustxi in enumerate(self.ustxInputs):
         prevHash  = binary_to_hex(ustxi.outpoint.txHash, BIGENDIAN)[:8]
         prevIdx   = ustxi.outpoint.txOutIndex
         typeName  = CPP_TXOUT_SCRIPT_NAMES[ustxi.scriptType]
         usesP2SH  = '*' if len(ustxi.p2shScript)>0 else ' '
         value     = coin2str(ustxi.value).lstrip().rjust(12)
         M,N       = ustxi.sigsNeeded, ustxi.keysListed
         contrib   = '(%s)'%ustxi.contribID if ustxi.contribID else ''
         pubKeySz  = '(' + ' '.join([str(len(s)) for s in ustxi.pubKeys]) + ')'

         printStr  = ' '*2*indent
         printStr += '%(prevHash)s:%(prevIdx)d / ' % locals()
         printStr += '%(typeName)s%(usesP2SH)s / '  % locals()
         printStr += '(M=%(M)d, N=%(N)d) / '  % locals()
         printStr += '%(value)s / %(contrib)s'  % locals()
         printStr += 'PubSz: ' + pubKeySz
         print printStr

      print ind+'#Outputs     : ', len(tx.outputs)
      for i,txout in enumerate(tx.outputs):
         dtxo = self.decorTxOuts[i]
         addrDisp = getTxOutScriptDisplayStr(txout.binScript)
         valDisp = coin2str(txout.value, maxZeros=2)
         print ' '*2*indent + 'Recip:', addrDisp.ljust(35),
         print valDisp, 'BTC',
         print ('(%s)' % dtxo.contribID) if dtxo.contribID else ''


   #############################################################################
   """
   def __eq__(self, obj2):
      if not isinstance(obj2, self.__class__):
         return False

      compareAttrs = ['version', 'lockTime']
      compareLists = ['ustxInputs', 'decorTxOuts']
      compareMaps  = []

      for attr in compareAttrs:
         if not getattr(self, attr) == getattr(obj2, attr):
            LOGERROR('Compare failed for attribute: %s' % attr)
            LOGERROR('  self:   %s' % str(getattr(self,attr)))
            LOGERROR('  other:  %s' % str(getattr(obj2,attr)))
            return False


      for attr in compareLists:
         selfList  = getattr(self, attr)
         otherList = getattr(obj2, attr)
      
         if not len(selfList)==len(otherList):
            LOGERROR('List size compare failed for %s' % attr)
            return False

         i = -1
         for a,b in zip(selfList, otherList):
            i+=1
            if not a==b:
               LOGERROR('Failed list compare for attr %s, index %d' % (attr,i))
               return False

      for attr in compareMaps:
         selfMap  = getattr(self, attr)
         otherMap = getattr(obj2, attr)

         if not len(selfMap)==len(otherMap):
            LOGERROR('Map size compare failed for %s' % attr)
            return False

         for key,val in selfMap.iteritems():
            if not key in otherMap:
               LOGERROR('First map has key not in second map: "%s"' % key)
               return False

            if not val==otherMap[key]:
               LOGERROR('Value for attr=%s, key=%s does not match' % (attr,key))
               return False 
            
      return True


   def __ne__(self, obj2):
      return not self.__eq__(obj2)
      
   """



################################################################################
# This is intended only for lists of unsignedTxInputs that have all unlocked
# signing keys in the signAddrObjMap.  Map is all [scrAddr, PyBtcAddress] pairs.
#
# This method is intended for sweep transaction where a bundle of private keys
# were provided.
def PyCreateAndSignTx(ustxiList, dtxoList, sbdPrivKeyMap):
   ustx = UnsignedTransaction().createFromUnsignedTxIO(ustxiList, dtxoList)

   for ustxiIndex in range(len(ustx.ustxInputs)):
      for scrAddr in ustx.ustxInputs[ustxiIndex].scrAddrs:
         sbdPriv = sbdPrivKeyMap.get(scrAddr)
         if sbdPriv is None:
            raise SignatureError('Supplied key map cannot sign all inputs')
         ustx.createAndInsertSignatureForInput(ustxiIndex, sbdPriv)

   # Make sure everythign was good
   if not ustx.verifySigsAllInputs():
      raise SignatureError('Not all signatures are present or valid')

   return ustx.getSignedPyTx(doVerifySigs=False) # already checked them



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
def PyCreateAndSignTx_old(srcTxOuts, dstAddrsVals):
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
      dst         = dstAddrsVals[i][0]
      if(coinbaseTx):
         txout.binScript = pubkey_to_p2pk_script(dst.binPublicKey65.toBinStr())
      else:
         txout.binScript = hash160_to_p2pkhash_script(dst.getAddr160())

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
            newTx.inputs[i].binScript = sigLenInBinary + signature + hashCode1 + \
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
         return cppWlt.getSpendableTxOutList(currBlk, IGNOREZC)
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
from armoryengine.Script import *
from armoryengine.MultiSigUtils import calcLockboxID
