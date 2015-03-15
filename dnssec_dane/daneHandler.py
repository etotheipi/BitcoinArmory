################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

#from armoryengine.ArmoryUtils import binary_to_hex
import getdns
from binascii import hexlify
from armoryengine.ArmoryUtils import LOGERROR
from armoryengine.ConstructedScript import PublicKeySource, ConstructedScript, \
   ScriptRelationshipProof, PublicKeyRelationshipProof, BTCAID_PR_VERSION, \
   BTCAID_PAYLOAD_TYPE
from pytest.testConstructedScript import PKS1NoChksum_Comp_v0, CS1Chksum_Comp_v0

# Function that takes a wallet ID payment request and validates it. This is the
# entry function that launches all the steps required to regenerate all the
# TxOut scripts for the requested payment.
#
# INPUT:  A PaymentRequest object received from elsewhere.
# OUTPUT: None
# RETURN: -1 if an error prevented validation from completing, 0 if the
#         generated script didn't match the unvalidated script, and 1 if the
#         generated and unvalidated scripts match.
def validatePaymentRequest(inPayReq):
   retCode = -1
   ctr = 0

   # Use the number of TxOut requests as our guide. The number of list entries
   # MUST match the number of TxOut requests. If they don't, something's wrong.
   # Also, while we're here, let's go ahead and check for all other fatal errors.
   if inPayReq.version != BTCAID_PR_VERSION:
      print 'Payment Request validation fails: Incorrect version'
   elif inPayReq.numTxOutScripts > 65535:
      print 'Payment Request validation fails: Too many TxOuts'
   elif inPayReq.reqSize > 65535:
      print 'Payment Request validation fails: Request is too large'
   elif inPayReq.numTxOutScripts != len(inPayReq.unvalidatedScripts):
      print 'Payment Request validation fails: TxOut script template amount mismatch'
   elif inPayReq.numTxOutScripts != len(inPayReq.daneReqNames):
      print 'Payment Request validation fails: DANE name amount mismatch'
   elif inPayReq.numTxOutScripts != len(inPayReq.srpLists):
      print 'Payment Request validation fails: SRP amount mismatch'
   else:
      while ctr < inPayReq.numTxOutScripts:
         # Get the DANE record.
         # HACK ALERT: This call is a hack for now. Will change very soon.
         recType, daneReq = getDANERecord(inPayReq.daneReqNames[ctr],
                                          BTCAID_PAYLOAD_TYPE.ConstructedScript)

         # Have the record type recreate the script. If we receive a PKS, assume
         # a P2PKH record must be created. If we receive a CS, generate whatever
         # resides in the CS.
         # NOTE: If functions share the same name across classes, it's ideal for
         # the prototypes to match too!
         finalKey = None
         finalScript = None
         if recType == BTCAID_PAYLOAD_TYPE.InvalidRec:
            print 'Payment Request validation fails: DANE record is invalid.'
         else:
            if recType == BTCAID_PAYLOAD_TYPE.PublicKeySource:
               # Get key and then generate a P2PKH TxOut script from it.
               finalKey = daneReq.generateKeyData(inPayReq.srpLists[ctr].pkrpList)
               retCode = 1
            elif recType == BTCAID_PAYLOAD_TYPE.ConstructedScript:
               finalScript = daneReq.generateScript(inPayReq.srpLists[ctr])
               if inPayReq.unvalidatedScripts[ctr] != finalScript:
                  retCode = 0
               else:
                  retCode = 1

         # We're done.
         ctr += 1

   return retCode


# Function that obtains a DANE record for a given record name.
# WARNING: For now, this is a placeholder that will return one of two pre-built
# records. Once proper DNS code has been written, actual records will be pulled
# down. The logic will be as follows:
# - Use getdns-python-bindings to get the DANE record for the given name.
# - Process the DANE header (TBD) as needed. This will include information like
#   the payment network, the wallet ID record type (PKS or CS), etc.
# - Pass back the wallet ID record type and a value indicating the record type.
#
# INPUT:  The DANE record name (string) and a byte indicating if a PKS or CS
#         record is desired (BTCA_PAYLOAD_TYPE - TEMPORARY - ONLY USED BY
#         PLACEHOLDER CODE)
# OUTPUT: None
# RETURN: An enum indicating the returned record type, and the returned record.
def getDANERecord(daneRecName, desiredRecType=None):
   retType = BTCAID_PAYLOAD_TYPE.InvalidRec
   retRec = None

   # TO BE USED ONLY FOR TEST CASES!!!
   # For now, it returns a PKS or CS based on the second master pub key from the
   # BIP32 test vector. Any code that doesn't account for this will fail.
   if desiredRecType != None:
      if desiredRecType == BTCAID_PAYLOAD_TYPE.PublicKeySource:
         retRec = PublicKeySource().unserialize(PKS1NoChksum_Comp_v0)
         retType = BTCAID_PAYLOAD_TYPE.PublicKeySource
      elif desiredRecType == BTCAID_PAYLOAD_TYPE.ConstructedScript:
         retRec = ConstructedScript().unserialize(CS1Chksum_Comp_v0)
         retType = BTCAID_PAYLOAD_TYPE.ConstructedScript
      else:
         LOGERROR('Wrong BTCA record type requested.')

   else:
      # Assume PMTA record type = 65337
      GETDNS_RRTYPE_PMTA = 65337

      # Go out and grab the record that we're querying.
      ctx = getdns.Context()
      #extensions = { "dnssec_return_only_secure": getdns.GETDNS_EXTENSION_TRUE }
      results = ctx.general(name = daneRecName, request_type = GETDNS_RRTYPE_PMTA)
      status = results['status']

      # Deep dive to extract the data we want.
      daneRec = None
      if status == getdns.GETDNS_RESPSTATUS_GOOD:
         for reply in results['replies_tree']:
            for rr in reply['answer']:
               if rr['type'] == GETDNS_RRTYPE_PMTA:
                  # HACK HACK HACK: Rec type & format are set for a demo.
                  # Must fix later!!!
                  rdata = rr['rdata']
                  retRec = rdata['rdata_raw']
                  retType = BTCAID_PAYLOAD_TYPE.PublicKeySource
      else:
         LOGERROR("getdns: failed looking up PMTA record, code: %d" % status)

   return retType, retRec
