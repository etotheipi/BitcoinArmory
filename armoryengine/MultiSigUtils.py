from os import path
import base64
import json
import ast
from armoryengine.ArmoryUtils import *
from armoryengine.Transaction import *

MULTISIG_VERSION = 0

################################################################################
#
# Multi-signature transactions are going to require a ton of different 
# primitives to be both useful and safe for escrow.  All primitives should
# have an ASCII-armored-esque form for transmission through email or text
# file, as well as binary form for when file transfer is guaranteed
#
# Until Armory implements BIP 32, these utilities are more suited to
# low-volume use cases, such as one-time escrow, or long-term savings
# using multi-device authentication.  Multi-signature *wallets* which
# behave like regular wallets but spit out P2SH addresses and usable 
# in every day situations -- those will have to wait for Armory's new
# wallet format.
#
# Concepts:
#     "Lockbox":  A "lock box" for putting coins that will be protected
#                  with multiple signatures.  The lockbox contains both
#                  the script info as well as meta-data, like participants'
#                  names and emails associated with each public key.
#
#
# 
#     
#                  
################################################################################
"""
Use-Case 1 -- Protecting coins with 2-of-3 computers (2 offline, 1 online):

   Create or access existing wallet on each of three computers. 

   Online computer will create the lockbox - needs one public key from its
   own wallet, and one from each offline wallet.  Can have both WO wallets
   on the online computer, and pull keys directly from those.

   User creates an lockbox with all three keys, labeling them appropriately
   This lockbox will be added to the global list.

   User will fund the lockbox from an existing offline wallet with lots of
   money.  He does not need to use the special funding procedure, which is
   only needed if there's multiple people involved with less than full trust.
   
   Creates the transaction as usual, but uses the "lockbox" button for the
   recipient instead of normal address.  The address line will show the 
   lockbox ID and short description.  

   Will save the lockbox and the offline transaction to the USB drive

"""


################################################################################
def getMultiSigID(script):
   #M,N = getMultisigScriptInfo(script)[:2]
   hashedData = hash160(MAGIC_BYTES + script)
   #return '%d%d%s' % (M, N, binary_to_base58(hashedData)[:6])
   return binary_to_base58(hashedData)[:8]



################################################################################
################################################################################
class MultiSigLockbox(object):

   #############################################################################
   def __init__(self, script=None, name=None, descr=None, \
                                          commList=None, createDate=None):
      self.version   = 0
      self.binScript = script
      self.shortName = name
      self.longDescr = descr
      self.commentList = commList
      self.createDate = long(RightNow()) if createDate is None else createDate
      self.magicBytes = MAGIC_BYTES

      if script is not None:
         self.setParams(script, name, descr, commList)


   #############################################################################
   def setParams(self, script, name=None, descr=None, commList=None, \
                                 version=MULTISIG_VERSION, createDate=None):
      
      # Set params will only overwrite with non-None data
      self.binScript = script
      
      if name is not None:
         self.shortName = name

      if descr is not None:
         self.longDescr = descr

      if commList is not None:
         self.commentList = commList[:]

      if createDate is not None:
         self.createDate = createDate

      self.version = version
      self.magicBytes = MAGIC_BYTES

      scrType = getTxOutScriptType(script)
      if not scrType==CPP_TXOUT_MULTISIG:
         LOGERROR('Attempted to create lockbox from non-multi-sig script')
         self.binScript = None
         return


      # Computed some derived members

      self.scrAddr      = script_to_scrAddr(script)
      self.uniqueIDB58  = getMultiSigID(script)
      self.M, self.N, self.a160List, self.pkList = getMultisigScriptInfo(script)
      self.opStrList = convertScriptToOpStrings(script)

      
      
   #############################################################################
   def serialize(self, wid=64):

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES)
      bp.put(UINT64,       self.createDate)
      bp.put(VAR_STR,      self.binScript)
      bp.put(VAR_STR,      toBytes(self.shortName))
      bp.put(VAR_STR,      toBytes(self.longDescr))
      bp.put(UINT32,       len(self.commentList))
      for comm in self.commentList:
         bp.put(VAR_STR,   toBytes(comm))

      rawStr = base64.b64encode(bp.getBinaryString())
      sz = len(rawStr)
      lines = ['=====LOCKBOX=%s=====' % self.uniqueIDB58]
      lines.extend([rawStr[wid*i:wid*(i+1)] for i in range((sz-1)/wid+1)])
      lines.append("="*28)
      
      return '\n'.join(lines)
      

   #############################################################################
   def unserialize(self, envBlock):

      lines = envBlock.split()
      if not lines[0].startswith('=====LOCKBOX') or \
         not lines[-1].startswith('======'):
         LOGERROR('Attempting to unserialize lockbox that is not lockbox')
         return None

      idSize = len(getMultiSigID(''))
      expectID = lines[0][13:13+idSize]
      rawData = base64.b64decode(''.join(lines[1:-1]))

      bu = BinaryUnpacker(rawData)
      envVersion = bu.get(UINT32)
      envMagic   = bu.get(BINARY_CHUNK, 4)
      created    = bu.get(UINT64)
      envScript  = bu.get(VAR_STR)
      envName    = bu.get(VAR_STR)
      envDescr   = bu.get(VAR_STR)
      nComment   = bu.get(UINT32)

      envComms = ['']*nComment
      for i in range(nComment):
         envComms[i] = bu.get(VAR_STR)

      # Issue a warning if the versions don't match
      if not envVersion == MULTISIG_VERSION:
         LOGWARN('Unserialing lockbox of different version')
         LOGWARN('   Lockbox Version: ' + envVersion)
         LOGWARN('   Armory  Version: ' + MULTISIG_VERSION)

      # Check the magic bytes of the lockbox match
      if not envMagic == MAGIC_BYTES:
         LOGERROR('Wrong network!')
         LOGERROR('    Lockbox Magic: ' + binary_to_hex(envMagic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         return None

      
      # Lockbox ID is written in the first line, it should match the script
      # If not maybe a version mistmatch, serialization error, or bug
      if not getMultiSigID(envScript) == expectID:
         LOGERROR('ID on lockbox block does not match script')
         return None

      # No need to read magic bytes -- already checked & bailed if incorrect
      self.setParams(envScript, envName, envDescr, envComms, \
                                                   MULTISIG_VERSION, created)

      return self


   #############################################################################
   def pprint(self):
      print 'Multi-signature %d-of-%d lockbox:' % (self.M, self.N)
      print '   Unique ID:  ', self.uniqueIDB58
      print '   Created:    ', unixTimeToFormatStr(self.createDate)
      print '   Env Name:   ', self.shortName
      print '   Env Desc:   '
      print '     ', self.longDescr[:70]
      print '   Key List:   '
      print '   Script Ops: '
      for opStr in self.opStrList:
         print '       ', opStr
      print''
      print '   Key Info:   '
      for i in range(len(self.pkList)):
         print '            Key %d' % i
         print '           ', binary_to_hex(self.pkList[i])[:40] + '...'
         print '           ', hash160_to_addrStr(self.a160List[i])
         print '           ', self.commentList[i]
         print ''
      


   #############################################################################
   def pprintOneLine(self):
      print 'LockBox %s:  %s-of-%s, created: %s;  "%s"' % (self.uniqueIDB58, 
         self.M, self.N, unixTimeToFormatStr(self.createDate), self.shortName)






################################################################################
################################################################################
class MultiSigContribFunds(object):
   #############################################################################
   def __init__(self, envID=None, payAmt=None, feeAmt=None, changeScript=None, 
                  contribLabel=None, supportTx=None, version=MULTISIG_VERSION):
      self.version   = 0
      self.envID     = envID
      self.payAmt    = payAmt
      self.feeAmt    = feeAmt
      self.changeScript  = changeScript
      self.contribLabel  = contribLabel
      self.supportTxPairs = supportTx

      if envID is not None:
         self.setParams(envID, payAmt, feeAmt, changeScript, supportTx, version)


   #############################################################################
   def setParams(self, envID=None, payAmt=None, feeAmt=None, changeScript=None,
                   contribLabel=None, supportTx=None, version=MULTISIG_VERSION):
      
      # Set params will only overwrite with non-None data
      self.envID = envID
      
      if payAmt is not None:
         self.payAmt = payAmt

      if feeAmt is not None:
         self.feeAmt = feeAmt

      if changeScript is not None:
         self.changeScript = changeScript

      if contribLabel is not None:
         self.contribLabel = contribLabel

      if supportTx is not None:
         self.supportTxPairs = supportTx[:]

      # Compute some other data members
      self.version = version
      self.magicBytes = MAGIC_BYTES


      self.outPointTriplets = []
      for rawTx,txoIdx in supportTx:
         tx = PyTx().unserialize(rawTx)
         op = PyOutPoint()
         op.txHash = hash256(rawTx)
         op.txOutIndex = txoIdx
         val = tx.outputs[txoIdx].value
         scr = tx.outputs[txoIdx].binScript
         self.opValues.append([op, val, scr])



      
      
   #############################################################################
   def serialize(self, wid=64):

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES)
      bp.put(VAR_STR,      self.envID)
      bp.put(UINT64,       self.payAmt)
      bp.put(UINT64,       self.feeAmt)
      bp.put(VAR_STR,      self.changeScript)
      bp.put(VAR_STR,      toBytes(self.contribLabel))
      bp.put(UINT32,       len(self.supportTxPairs))
      for rawTx,txoIdx in self.supportTxPairs:
         bp.put(VAR_STR,   rawTx)
         bp.put(UINT32,    txoIdx)

      rawStr = base64.b64encode(bp.getBinaryString())
      sz = len(rawStr)
      lines = ['=====ENVCONTRIB=%s=====' % self.uniqueIDB58]
      lines.extend([rawStr[wid*i:wid*(i+1)] for i in range((sz-1)/wid+1)])
      lines.append("="*28)
      
      return '\n'.join(lines)



   #############################################################################
   def unserialize(self, envBlock):

      lines = envBlock.split()
      if not lines[0].startswith('=====LOCKBOX') or \
         not lines[-1].startswith('======'):
         LOGERROR('Attempting to unserialize lockbox that is not lockbox')
         return None

      idSize = len(getMultiSigID(''))
      expectID = lines[0][14:14+idSize]

      envBlock = ''.join(lines[1:-1])
      mapStr = base64.b64decode(''.join(envBlock.split()))
      dataMap = ast.literal_eval(mapStr)
      
      if not 'Script'  in dataMap or \
         not 'Name'    in dataMap or \
         not 'Descr'   in dataMap or \
         not 'Comms'   in dataMap or \
         not 'Version' in dataMap:
         LOGERROR('Missing lockbox data')
      
      self.setParams(dataMap['Script'], \
                     dataMap['Name'], \
                     dataMap['Descr'], \
                     dataMap['Comms'])
      return self


   #############################################################################
   def pprint(self):
      print 'Multi-signature %d-of-%d lockbox:' % (self.M, self.N)
      print '   Unique ID: ', self.uniqueIDB58
      print '    Env Name: ', self.shortName
      print '    Env Desc: ', self.longDescr[:60]
      print '    Key List: '
      for i in range(len(self.pkList)):
         print '            Key %d' % i
         print '           ', binary_to_hex(self.pkList[i])[:40] + '...'
         print '           ', hash160_to_addrStr(self.a160List[i])
         print '           ', self.commentList[i]
         print ''












