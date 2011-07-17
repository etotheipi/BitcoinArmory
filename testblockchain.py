from pybtcengine import *
from pybtcstructures import *

blkDataPath  = '/home/alan/download/bitcoin-blockchain-20110716/blk0001.dat'
blkIndexPath = '/home/alan/download/bitcoin-blockchain-20110716/blkindex.dat'

bc = BlockChain()

bc.readBlockChainFile(blkDataPath, justHeaders=True)

k = bc.getBlockChainStats()
print 'Block chain in memory contains:'
print '\tNum Blocks:      ', k[0]
print '\tNum Transactions:', k[1]
raw_input()
