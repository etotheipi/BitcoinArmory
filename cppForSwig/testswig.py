#! /usr/bin/python

print 'Importing BlockUtilsSWIG module...',
from BlockUtilsSWIG import *
print 'Done!'
print ''

print 'Constructing BlockchainManager... ',
bcm = SWIG_BlockchainManager()
print 'Done!'
print ''

print 'Loading blk0001.dat...            ',
bcm.loadBlockchain('../blk0001.dat')
print 'Done!'
print ''


print 'Getting top block of the chain... ',
top = bcm.getTopBlockHeader()
top.printHeader()
print 'Done!...'
print ''

print 'Getting top block prevHash ...    ',
prevhash = top.getPrevHash()
print prevhash
print 'Done!'
print ''

print 'Getting almost-top-block'
topm1 = bcm.getHeaderByHash(prevhash)
topm1.printHeader()
print 'Done!'
print ''

print 'Getting almost-top-block'
topm1 = bcm.getHeaderByHeight(170)
topm1.printHeader()
print 'Done!'
print ''

print 'Accessing some top-block properties...'
print 'Difficulty:', top.getDifficulty()
print 'Diff Sum  :', top.getDifficultySum()
print 'Timestamp :', top.getTimestamp()
print ''


print 'Accessing vectors...'
v1 = vector_int(10)
v2 = vector_BinaryData(10)
for i in range(10):
   v1[i] = 2*i
   v2[i] = BinaryData('ascii%03d'%(i,))


print 'Constructed vectors:'
print v1
print v2
for i in range(10):
   print v1[i], v2[i].toString()

print ''



