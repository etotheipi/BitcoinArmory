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
