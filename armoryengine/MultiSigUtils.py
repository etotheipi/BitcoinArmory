from os import path
import base64
import ast
from armoryengine.ArmoryUtils import *
from armoryengine.Transaction import *


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
#     "Envelope":  A "lock box" for putting coins that will be protected
#                  with multiple signatures.  The envelope contains both
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

   Online computer will create the envelope - needs one public key from its
   own wallet, and one from each offline wallet.  Can have both WO wallets
   on the online computer, and pull keys directly from those.

   User creates an envelope with all three keys, labeling them appropriately
   This envelope will be added to the global list.

   User will fund the envelope from an existing offline wallet with lots of
   money.  He does not need to use the special funding procedure, which is
   only needed if there's multiple people involved with less than full trust.
   
   Creates the transaction as usual, but uses the "envelope" button for the
   recipient instead of normal address.  The address line will show the 
   envelope ID and short description.  

   Will save the envelope and the offline transaction to the USB drive

"""


################################################################################
def getMultiSigID(script):
   M,N = getMultisigScriptInfo(script)[:2]
   hashedData = hash160(MAGIC_BYTES + script)
   return '%d%d%s' % (M, N, binary_to_base58(hashedData)[:6])



################################################################################
################################################################################
class MultiSigEnvelope(object):

   #############################################################################
   def __init__(self, script=None, name=None, descr=None, commList=None):
      self.binScript = script
      self.shortName = name
      self.longDescr = descr
      self.commentList = commList

      if script is not None:
         self.setParams(script, name, descr, commList)


   #############################################################################
   def setParams(self, script, name=None, descr=None, commList=None):
      
      # Set params will only overwrite with non-None data
      self.binScript = script
      
      if name is not None:
         self.shortName = name

      if descr is not None:
         self.longDescr = descr

      if commList is not None:
         self.commentList = commList

      scrType = getTxOutScriptType(script)
      if not scrType==CPP_TXOUT_MULTISIG:
         LOGERROR('Attempted to create envelope from non-multi-sig script')
         self.binScript = None
         return


      # Computed some derived members

      self.scrAddr      = script_to_scrAddr(script)
      self.uniqueIDB58  = getMultiSigID(script)
      self.M, self.N, self.a160List, self.pkList = getMultisigScriptInfo(script)
      self.opStrList = convertScriptToOpStrings(script)

      
      
   #############################################################################
   def serialize(self, width=64):
      data = { 'Script': self.binScript,
               'Name':   self.shortName,
               'Descr':  self.longDescr,
               'Comms':  self.commentList}

      rawStr = base64.b64encode(str(data))
      sz = len(rawStr)
      lines = [rawStr[width*i:width*(i+1)] for i in range((sz-1)/width+1)]
      return '\n'.join(lines)
      

   #############################################################################
   def unserialize(self, envBlock):

      mapStr = base64.b64decode(''.join(envBlock.split()))
      dataMap = ast.literal_eval(mapStr)
      
      if not 'Script' in dataMap or \
         not 'Name'   in dataMap or \
         not 'Descr'  in dataMap or \
         not 'Comms'  in dataMap:
         LOGERROR('Missing envelope data')
      
      self.setParams(dataMap['Script'], \
                     dataMap['Name'], \
                     dataMap['Descr'], \
                     dataMap['Comms'])
      return self


   #############################################################################
   def pprint(self):
      print 'Multi-signature %d-of-%d envelope:' % (self.M, self.N)
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
      
















