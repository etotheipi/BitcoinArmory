from ArmoryDB import *

thedb = ArmoryDB()
#rt = thedb.GetAllHeadersAtHeight(150042)
#rtstr = ":".join("{0:x}".format(ord(c)) for c in rt[0].theHash)
#print rtstr

hashfrag = hex_to_binary('5ea84f3776d998e34b0814ef9d05e120c0842498f09643251e48f41be6f6141c', endIn=BIGENDIAN)
#hashfrag = hex_to_binary('e0ec06ce0a96d75ede3610d0120c84e1704310db3ee008c82ca3821ac061ac84', endIn=BIGENDIAN)
#hashfrag = hex_to_binary('7dd56b72ee61090dd30c04ac818884f6c38783fdc30996e5edf42de337166dbd', endIn=BIGENDIAN)
rt = thedb.getAllTxnByPrefix(hashfrag[0:4])
if(rt==None):
   print 'fetch failure'
else:
   print 'fetched!'


blkhash = hex_to_binary('00000000000011906b491883ab0f16f0e690b133ca860b199b775c3cf6581c21', endIn=BIGENDIAN)
rt = thedb.headersDBHasBlockHash(blkhash)
if (rt==False):
   print 'another fetch failure'
else:
   print True

rt = thedb.getDBStatus()
print 'top block in dbheaders: %d' % (rt.TopBlockInHeadersDB)
print 'top block in dbblkdata: %d' % (rt.TopBlockInBlkDataDB)
print 'n missing heights: %d' % (rt.nMissingHeight)
print 'n dups: %d' % (rt.nDupHeight)

del thedb

