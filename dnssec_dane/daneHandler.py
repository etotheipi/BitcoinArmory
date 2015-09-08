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
from armoryengine.Constants import BTCAID_PAYLOAD_TYPE

# Function that obtains a DANE record for a given record name.
# - Use getdns-python-bindings to get the DANE record for the given name.
# - Process the DANE header (TBD) as needed. This will include information like
#   the payment network, the wallet ID record type (PKS or CS), etc.
# - Pass back the wallet ID record type and a value indicating the record type.
#
# INPUT:  The DANE record name (string) and a byte indicating if a PKS or CS
#         record is desired (BTCA_PAYLOAD_TYPE - TEMPORARY - ONLY USED BY
#         PLACEHOLDER CODE)
# OUTPUT: None
# RETURN: The serialized PMTA record obtained from DANE. (binary str)
#         The returned record type. (enum)
def getDANERecord(daneRecName):
   retType = BTCAID_PAYLOAD_TYPE.InvalidRec
   retRec = None

   # Assume PMTA record type = 65337
   GETDNS_RRTYPE_PMTA = 65337

   # Go out and grab the record that we're querying.
   # Allow insecure records to be returned for now. Some people are unable to
   # retrieve secure records.
   ctx = getdns.Context()
#   secExt = { "dnssec_return_only_secure": getdns.GETDNS_EXTENSION_TRUE }
   results = ctx.general(name = daneRecName,
                         request_type = GETDNS_RRTYPE_PMTA)
#                         request_type = GETDNS_RRTYPE_PMTA,
#                         extensions = secExt)
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
               print 'DEBUG: PMTAname=%s' % rr['name']
               print 'DEBUG: type=%d' % rr['type']
               print 'DEBUG: class=%d' % rr['class']
               print 'DEBUG: rdata_raw=%s\n\n' % hexlify(rdata['rdata_raw'])
               retRec = rdata['rdata_raw']
               retType = BTCAID_PAYLOAD_TYPE.PMTA
            elif rr['type'] == getdns.GETDNS_RRTYPE_RRSIG:
               rdata = rr['rdata']
               print 'DEBUG: name=%s' % rr['name']
               print 'DEBUG: type=%d' % rr['type']
               print 'DEBUG: class=%d' % rr['class']
               print 'DEBUG: signers_name=%s' % rdata['signers_name']
               print 'DEBUG: signature_expiration=%s' % rdata['signature_expiration']                  
               print 'DEBUG: algorithm=%d' % rdata['algorithm']
               print 'DEBUG: type_covered=%d' % rdata['type_covered']
               print 'DEBUG: labels=%d' % rdata['labels']
               print 'DEBUG: key_tag=%d' % rdata['key_tag']
               print 'DEBUG: original_ttl=%d' % rdata['original_ttl']
               print 'DEBUG: signature=%s' % hexlify(rdata['signature'])
               print 'DEBUG: signature_inception=%d' % rdata['signature_inception']
               print 'DEBUG: rdata_raw=%s\n\n' % hexlify(rdata['rdata_raw'])
   else:
      LOGERROR("getdns: failed looking up PMTA record, code: %d" % status)

   return retRec, retType
