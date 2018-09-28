#! /usr/bin/python
import sys
import getdns
from binascii import hexlify
sys.path.append("..")
from armoryengine.ArmoryUtils import sha224, binary_to_hex, hash160_to_addrStr

# ROUGH CODE!!! When making more robust, search for "assume" and fix any & all
# assumptions. Search for "Python 3" too.

# Assume PMTA record type = 65337
GETDNS_RRTYPE_PMTA = 65337

# User must supply an email address to query and indicate if testnet/mainnet.
if len(sys.argv) != 3:
   print 'Oops! Format is getDaneRec <email address> <M=Mainnet, T=Testnet>'
   sys.exit(0)

# For now, assume record name is an email address. Use the SMIME record format,
# where the username is hashed using SHA224. Also, assume domain is searched.
recordUser, recordDomain = sys.argv[1].split('@', 1)
sha224Res = sha224(recordUser)
daneReqName = binary_to_hex(sha224Res) + '._pmta.' + recordDomain

# Go out and grab the record that we're querying.
ctx = getdns.Context()
#extensions = { "dnssec_return_only_secure": getdns.GETDNS_EXTENSION_TRUE }
results = ctx.general(name = daneReqName, request_type = GETDNS_RRTYPE_PMTA)
status = results['status']

# Deep dive to extract the data we want.
daneRec = None
if status == getdns.GETDNS_RESPSTATUS_GOOD:
   for reply in results['replies_tree']:
      for rr in reply['answer']:
         if rr['type'] == 65337:
            # NB: Can switch hexlify() to binary_to_hex() after Python 3 upgrade
            rdata = rr['rdata']
            print 'Extracted record = %s' % hexlify(rdata['rdata_raw'])
            daneRec = rdata['rdata_raw']
else:
   print "getdns: failed looking up PMTA record, code: %d" % status
   print '%s has no Bitcoin address' % sys.argv[1]
   sys.exit(0)

# Convert Hash160 to Bitcoin address. Assume record is a PKS record that's
# static and has a Hash160 value.
verByte = '\x00'
if sys.argv[2].lower() == 't':
   verByte = '\x6f'
elif sys.argv[2].lower() != 'm':
   print 'Oops! Format is getDaneRec <email address> <M=Mainnet, T=Testnet>'
   sys.exit(0)

userAddr = ''
if daneRec != None:
   userAddr = hash160_to_addrStr(daneRec[4:24], verByte)
   print '%s has a Bitcoin address - %s' % (sys.argv[1], userAddr)
