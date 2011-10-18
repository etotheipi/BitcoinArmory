from pybtcengine import *
from os import path
import sys
from optparse import OptionParser

import time


def calcAddrFromBinPubKey(binPubKey, netbyte='\x00'):
   keyHash = hash160(binPubKey)
   keyHash    = hash160(binPubKey)
   chkSum     = hash256(netbyte + keyHash)[:4]
   return       binary_to_addrStr(netbyte + keyHash + chkSum)
   


if __name__ == '__main__':
   timeStart = time.time()
   print '\nExtract all addresses from blk0001.dat file'

   parser = OptionParser(usage='USAGE: %prog [-o|--outfile] [-b|blkfile')
   parser.add_option('-o', '--outfile', dest='outfile', default='addrlist.txt', \
                  help='Specify output file')
   parser.add_option('-b', '--blkfile', dest='blk0001file', default='', \
                  help='Specify path to blk0001.dat (default ~/.bitcoin/blk0001.dat)')
   #parser.add_option('-r', '--rescanhashes', action='store_true', dest='doRescan', default=False, \
                  #help='Rescan blkfile for header/tx hashes')
   
   (opts, args) = parser.parse_args()   


   #doRescan = opts.doRescan
   blkfile  = opts.blk0001file
   addrfile = opts.outfile

   if len(blkfile)==0:
      import platform
      opsys = platform.system()
      if 'win' in opsys.lower():
         blkfile = path.join(os.getenv('APPDATA'), 'Bitcoin', 'blk0001.dat')
      if 'nix' in opsys.lower() or 'nux' in opsys.lower():
         blkfile = path.join(os.getenv('HOME'), '.bitcoin', 'blk0001.dat')
      if 'mac' in opsys.lower() or 'osx' in opsys.lower():
			blkfile = os.path.expanduser('~/Library/Application Support/Bitcoin/blk0001.dat')

   if not path.exists(blkfile):
      print 'Cannot find blockdata file', blkfile
      exit(0)


   print '\t\t.BlockFile: ', blkfile
   print '\t\t.OutputFile:', addrfile

   
   blkfileSize = os.stat(blkfile).st_size
   bf = open(blkfile, 'rb')
   of = open(addrfile, 'w')


   binunpack = BinaryUnpacker(bf.read())
   newBlocksRead = 0
   uniqueAddresses = set()
   while binunpack.getRemainingSize() > 0:
      binunpack.advance(4)  # magic
      sz = binunpack.get(UINT32)  # total bytes in this block
      binunpack.advance(80)
      blkdata = BlockData().unserialize(binunpack)
      for tx in blkdata.txList:
         for tin in tx.inputs:
            tintype = getTxInScriptType(tin)
            if tintype == TXIN_SCRIPT_STANDARD:
               binPubkey = tin.binScript[-65:]
               addrStr = calcAddrFromBinPubKey(binPubkey)
               if not addrStr in uniqueAddresses:
                  #of.write('%s\t%s\n' % (addrStr, binary_to_hex(binPubkey)) )
                  of.write(addrStr + '\n')
               uniqueAddresses.add(addrStr)

         for tout in tx.outputs:
            touttype = getTxOutScriptType(tout)
            if touttype == TXOUT_SCRIPT_STANDARD:
               addr160 = tout.binPKScript[3:23]
               newAddr = BtcAddress().createFromPublicKeyHash160(addr160)
               addrStr = newAddr.getAddrStr()
               if not addrStr in uniqueAddresses:
                  of.write(addrStr + '\n')
               uniqueAddresses.add(addrStr)
            elif touttype == TXOUT_SCRIPT_COINBASE:
               binPubkey = tout.binPKScript[1:-1]
               addrStr = calcAddrFromBinPubKey(binPubkey)
               if not addrStr in uniqueAddresses:
                  #of.write('%s\t%s\n' % (addrStr, binary_to_hex(binPubkey)) )
                  of.write(addrStr + '\n')
               uniqueAddresses.add(addrStr)
               
      if newBlocksRead==0:
         print '\n\t\tReading blocks...',
      newBlocksRead += 1
      if(newBlocksRead%1000==0):
         if(newBlocksRead%10000==0):
            print '\n\t\tRead', newBlocksRead, 'blocks',
         print '.',
         sys.stdout.flush()

               
   of.close()
   bf.close()

   timeEnd = time.time()
   print ''
   print 'Took %0.3f minutes to find all addresses' % ((timeEnd - timeStart)/60.0,)
               
            


   
