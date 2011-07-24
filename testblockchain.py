from pybtcengine import *
from pybtcstructures import *
from datetime import datetime




blkDataPath  = '/home/alan/download/bitcoin-blockchain-20110716/blk0001.dat'
blkIndexPath = '/home/alan/download/bitcoin-blockchain-20110716/blkindex.dat'
blkHeadPath  = 'blkHeaders.dat'

bc = BlockChain()

timestart = datetime.now()
bc.readBlockChainFile(blkDataPath, justHeaders=True)
timeend = datetime.now()
print 'Took %0.1f s to read %s (blockchain file)' % ((timeend-timestart).seconds, blkHeadPath)

timestart = datetime.now()
bc.writeHeadersFile(blkHeadPath)
timeend = datetime.now()
print 'Took %0.1f s to write %s (headers file)' % ((timeend-timestart).seconds, blkHeadPath)

timestart = datetime.now()
bc.readHeadersFile(blkHeadPath)
timeend = datetime.now()
print 'Took %0.1f s to read %s (headers file)' % ((timeend-timestart).seconds, blkHeadPath)

k = bc.getBlockChainStats()
print 'Block chain in memory contains:'
print '\tNum Blocks:      ', k[0]
print '\tNum Transactions:', k[1]

topblkhash = bc.calcLongestChain()
print ''
print 'Top of the blockchain:'
print ''
bc.getBlockHeaderByHash(topblkhash).pprint()


