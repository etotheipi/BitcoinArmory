#! /usr/bin/python

print 'Importing BlockUtilsSWIG module...',
from BlockUtilsSWIG import *
print 'Done!'

print 'Constructing BlockchainManager... ',
bcm = SWIG_BlockchainManager()
print 'Done!'

print 'Loading blk0001.dat...            ',
bcm.loadBlockchain('../blk0001.dat')
print 'Done!'


print 'Getting top block of the chain... ',
top = bcm.getTopBlockHeader()
top.printHeader()
print 'Done!...'

print 'Getting top block prevHash ...    ',
prevhash = top.getPrevHash()
print prevhash
print 'Done!'

print 'Getting almost-top-block'
topm1 = bcm.getHeaderByHash(prevhash)
topm1.printHeader()
print 'Done!'

print 'Accessing some top-block properties...'
print 'Difficulty:', top.getDifficulty()
print 'Diff Sum  :', top.getDifficultySum()
print 'Timestamp :', top.getTimestamp()
