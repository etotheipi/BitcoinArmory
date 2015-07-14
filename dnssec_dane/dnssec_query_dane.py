################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

# Portions of the code come from
# https://github.com/getdnsapi/getdns-python-bindings and are licensed as such.
#Copyright (c) 2014, Verisign, Inc., NLnet Labs
#All rights reserved.
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#* Redistributions of source code must retain the above copyright
#notice, this list of conditions and the following disclaimer.
#* Redistributions in binary form must reproduce the above copyright
#notice, this list of conditions and the following disclaimer in the
#documentation and/or other materials provided with the distribution.
#* Neither the names of the copyright holders nor the
#names of its contributors may be used to endorse or promote products
#derived from this software without specific prior written permission.
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL Verisign, Inc. BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import sys, socket, hashlib
from M2Crypto import SSL, X509
import getdns
sys.path.append("..")
from CppBlockUtils import SecureBinaryData
from armoryengine.ArmoryUtils import binary_to_hex, sha256, sha512

# Proof-of-concept code that performs "Usage Type 3" verification on DANE
# records. (Anything more will require verification of the cert chain and will,
# hence, require a lot more code.) Most of the code is taken from
# checkdanecert.py.

# Print the "RDATA" contents of a TLSA resource record (RR).
def get_tlsa_rdata_set(replies):
    tlsa_rdata_set = []
    print 'Data from TLSA replies'
    for reply in replies:
        for rr in reply['answer']:
            if rr['type'] == getdns.GETDNS_RRTYPE_TLSA:
                rdata = rr['rdata']
                usage = rdata['certificate_usage']
                print 'usage: %d' % usage
                selector = rdata['selector']
                print 'selector: %d' % selector
                matching_type = rdata['matching_type']
                print 'matching_type: %d' % matching_type
                cadata = rdata['certificate_association_data']
                print 'cadata: %s' % binary_to_hex(str(cadata))
                tlsa_rdata_set.append(
                    (usage, selector, matching_type, str(cadata)))

    return tlsa_rdata_set


# Get a TLSA record from a given host/port.
def get_tlsa(port, proto, hostname):
    qname = "_%d._%s.%s" % (port, proto, hostname)
    ctx = getdns.Context()
    extensions = { "dnssec_return_only_secure": getdns.GETDNS_EXTENSION_TRUE }
    results = ctx.general(name=qname,
                          request_type=getdns.GETDNS_RRTYPE_TLSA,
                          extensions=extensions)
    status = results['status']

    if status == getdns.GETDNS_RESPSTATUS_GOOD:
        return get_tlsa_rdata_set(results['replies_tree'])
    else:
        print "getdns: failed looking up TLSA record, code: %d" % status
        return None


# Funct that does the actual record verification. Uses OpenSSL instead of
# Crypto++, although Crypto++ can work if GetPublicKeyFromCert()
# (http://www.cryptopp.com/wiki/X.509) is added to the code. Usage type 3
# (verify that the cert or pub key contents match the record) is the only type
# verified for now.
def verify_tlsa(cert, usage, selector, matchtype, hexdata1):
    # Usage type 3 only!
    if usage != 3:
        print 'Only TLSA usage type 3 is currently supported.'
        return False

    # Get the DER-encoded cert or DER-encoded pub key from the cert.
    if selector == 0:
        # Useful example: www.huque.com:443
        certdata = cert.as_der()
    elif selector == 1:
        # Useful example: www.nlnetlabs.nl:443
        certdata = cert.get_pubkey().as_der()
    else:
        raise ValueError('Selector type %d not recognized.' % selector)

    # Do a direct match or a SHA-256/512 match.
    if matchtype == 0:
        # No known examples for now.
        hexdata2 = hexdump(certdata)
    elif matchtype == 1:
        # Useful example: www.nlnetlabs.nl:443
        hexdata2 = sha256(certdata)
    elif matchtype == 2:
        # No known examples for now.
        hexdata2 = sha512(certdata)
    else:
        raise ValueError('Match type %d not recognized.' % matchtype)

    # Moment of truth.
    if hexdata1 == hexdata2:
        return True
    else:
        return False


# Pass in a hostname/port where TLSA records will be queried. Our code will
# print out the raw record info, get the cert from the server, and verify the
# record if it's a usage type 3 record.
if __name__ == '__main__':
    # Do initial setup and get the TLSA info.
    hostname, port = sys.argv[1:]
    port = int(port)
    tlsa_rdata_set = get_tlsa(port, "tcp", hostname)

    # Perform OpenSSL setup. Needed to obtain the cert.
    ctx = SSL.Context()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection = SSL.Connection(ctx, sock=sock)
    connection.connect((hostname, port))

    # Get the 1st cert from the chain (which will be the end entity cert)
    chain = connection.get_peer_cert_chain()
    cert = chain[0]

    # Find a matching TLSA record entry for the cert. (FYI, www.mqas.net:443
    # might be useful for checking against multiple records.)
    tlsa_match = False
    for (usage, selector, matchtype, hexdata) in tlsa_rdata_set:
        if verify_tlsa(cert, usage, selector, matchtype, hexdata):
            tlsa_match = True
            print 'Certificate matched TLSA record %d %d %d %s' % \
                (usage, selector, matchtype, binary_to_hex(hexdata))
        else:
            print 'Certificate did not match TLSA record %d %d %d %s' % \
                (usage, selector, matchtype, binary_to_hex(hexdata))
    if tlsa_match:
        print 'Found at least one matching TLSA record.'

    # Clean everything up.
    connection.close()
    ctx.close()
