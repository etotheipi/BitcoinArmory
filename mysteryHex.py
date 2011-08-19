from pybtcengine import *
from os import path
import sys




################################################################################
################################################################################
def figureOutMysteryHex(hexStr):
   print '\nTrying to identify Bitcoin-related strings in this block of hex:'
   hexStr.replace(' ','')
   pprintHex(hexStr, '   ')
   
   binStr = hex_to_binary(hexStr)

   # These search terms only give us hints about where things are.  We have more
   # operations to determine if something is actually behind these strings
   hintStr = {}
   hintStr['Empty4B'  ] = hex_to_binary('00000000'      )  
   hintStr['Version'  ] = hex_to_binary('01000000'      ) 
   hintStr['PkStart'  ] = hex_to_binary('76a9'          )
   hintStr['PkEnd'    ] = hex_to_binary('88ac'          )  
   hintStr['SeqNum'   ] = hex_to_binary('ffffffff'      )  

   # These search terms are simple, self-explanatory terms.  We find them, flag
   # them and we're done.
   simpleList = []
   simpleList.append(['f9beb4d9', 'MagicNum', 'Main network magic bytes (f9beb4d9)'])
   simpleList.append(['fabfb5da', 'MagicNum', 'Test network magic bytes (fabfb5da)'])
   simpleList.append(['76657261636b', 'VERACK', 'Version acknowledgement message'])
   simpleList.append(['76657273696f6e', 'VersionMsg', 'Version declaration message'])
   simpleList.append(['61646472', 'AddressMsg', 'Address declaration message'])

   # To verify a timestamp, check it's between 2009 and today + 10days
   timeMin = time.mktime( (2009,1,1,0,0,0,0,0,-1))
   timeMax = time.time() + 10*86400

   # Exclusive list of [Name, startIdx, endIdx, hexSubstr, toPrintAfter]
   # Exlucsive means that if we already identified something there, we don't
   # search it again
   idListExcl = []

   # Inclusive list of multipe random things.  Inclusive means that even if 
   # we already identified a transaction somewhere, we will still ID all the
   # scripts in it, even though it's technically already flagged as ID'd
   idListIncl = []

   # This is a running mask of what bytes have been identified already
   maskAll = [0]*len(binStr)

   # This method will return all indices that match the substring "findBin"
   # excluding matches inside chunks already ID'd
   def getIdxListNotIdYet(findBin, theMask):
      versIdx = []
      findIdx = binStr.find(findBin)
      while not findIdx == -1:
         if not theMask[findIdx] == 1:
            versIdx.append(findIdx) 
         findIdx = binStr.find(hintStr['Version'],findIdx+1)
      return versIdx
      
   # Return all matches for the string, regardless of whether it's ID'd already
   def getIdxList(findBin):
      versIdx = []
      findIdx = binStr.find(findBin)
      while not findIdx == -1:
         versIdx.append(findIdx)
         findIdx = binStr.find(findBin,findIdx+1)
      return versIdx
         
   ############################################################################
   # Search for version numbers which will help us find Tx's and BlockHeaders
   ############################################################################
   versIdx = getIdxListNotIdYet(hintStr['Version'], maskAll)
   
   for idx in versIdx:
      # Check for block Header:  hash has leading zeros and timestamp is sane
      hashZeros = binStr[idx+32:idx+36] == hintStr['Empty4B']
      validTime = timeMin < binary_to_int(binStr[idx+68:idx+72]) < timeMax
      if hashZeros and validTime:
         bin80 = binStr[idx:idx+80]
         blkhead = BlockHeader().unserialize(bin80) 
         idListExcl.append(['BlockHeader', idx, idx+80, binary_to_hex(bin80), blkhead])
         maskAll[idx:idx+80] = [1]*80
         continue 
      
      # If not a header, check to see if it's a Tx
      try:
         testTx = Tx().unserialize(binStr[idx:])
         if len(testTx.inputs) < 1 or len(testTx.outputs) < 1:
            raise Exception
         for inp in testTx.inputs:
            if not inp.intSeq==binary_to_int(hintStr['SeqNum']):
               raise Exception

         # If we got here, the sequence numbers should be sufficient evidence for
         # declaring this is a transaction
         txBin = testTx.serialize()
         txLen = len(txBin)
         txHex = binary_to_hex(txBin)
         idListExcl.append(['Transaction', idx, idx+txLen, txHex, testTx])
         maskAll[idx:idx+txLen] = [1]*txLen
      except:
         # Obviously wasn't a transaction, either
         continue

   
   # Try to find a PkScript
   pkIdx = getIdxList(hintStr['PkStart'])
   for idx in pkIdx:
      if binStr[idx+23:idx+25] == hintStr['PkEnd']:
         addrStr = BtcAccount().createFromPublicKeyHash160(binStr[idx+3:idx+23])
         extraInfo = addrStr.getAddrStr()
         idListIncl.append(['TxOutScript', idx, idx+25, extraInfo, ''])

   startCBPK = hex_to_binary('04')
   pkIdx = getIdxList(startCBPK)
   for idx in pkIdx:
      #if idx > len(binStr)-65 or maskAll[idx] == 1:
      if idx > len(binStr)-65:
         continue
      #if binStr[idx+65] == endCBPK:
      try:
         addrStr = BtcAccount().createFromPublicKey(binStr[idx:idx+65])
         extraInfo = addrStr.calculateAddrStr()
         if binStr[idx+65] == hex_to_binary('ac'):
            idListIncl.append(['CoinbaseScript', idx, idx+66, extraInfo, ''])
         else:
            idListIncl.append(['BarePublicKey', idx, idx+65, extraInfo, ''])
         if binStr[idx-1]  == hex_to_binary('41'):
            idListIncl[-1][1] -= 1  # get the 41 that's there if it's a script
      except:
         pass # I guess this wasn't a PK after all...
         

   ############################################################################
   # Random straightforward things to search for without any extra computation.
   ############################################################################
   for triplet in simpleList:
      foundIdx = getIdxList( hex_to_binary(triplet[0]))
      for idx in foundIdx:      
         idListIncl.append([triplet[1], idx, idx+len(triplet[0])/2, triplet[2], ''])


   # Start printing out the exclusive data we found
   for ids in idListExcl:
      print ''
      print '################################################################################'
      idx0,idx1 = ids[1], ids[2]

      # If this is a Tx or BH, need to pprint the last arg
      hexToPrint = ['-'] * 2*len(binStr) 
      if ids[0] == 'Transaction' or ids[0] == 'BlockHeader':
         hexToPrint[2*ids[1]:2*ids[2]] = ids[3]
         print 'Found: ', ids[0]
         print 'Size:', idx1-idx0, 'bytes'
         print 'Bytes: %d to %d  (0x%s to 0x%s)' % (idx0, idx1, \
                                                    int_to_hex(idx0, 4, BIGENDIAN), \
                                                    int_to_hex(idx1, 4, BIGENDIAN))
         pprintHex( ''.join(hexToPrint), '   ')
         print '\n\nObject found:' 
         ids[4].pprint(1)
      print ''
      print '################################################################################'

   # Print all the inclusive stuff onto a single bytemap
   print 'Other assorted things:'
   idListIncl.sort(key=lambda x: x[1])
   hexToPrint = ['-'] * 2*len(binStr) 
   ReprList = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
   for j,ids in enumerate(idListIncl):
      i1 = ids[1]
      i2 = ids[2]
      nb = i2-i1
      maskAll[i1:i2] = [1]*nb
      hexToPrint[2*i1:2*i2] = ReprList[j]*2*nb
      print len(hexToPrint)

   hexToPrint = ''.join(hexToPrint)
   pprintHex(hexToPrint, '   ')

   print ''
   for j,ids in enumerate(idListIncl):
      print '\t', ReprList[j] + ':', ids[0].ljust(16,' '), ':', ids[3]
      
   print '\n\nUnidentified bytes'
   maskedBytes = ['--' if maskAll[i] == 1 else hexStr[2*i:2*i+2] for i in range(len(binStr))]
   
   pprintHex(''.join(maskedBytes));
   


################################################################################
################################################################################
def updateHashList(hashfile, blkfile):

   print 'Updating hashlist in', hashfile, 'from', blkfile
   if not path.exists(hashfile):
      hf = open('knownHashes.txt','wb')
      hf.write('\x00'*8)
      hf.close()
   hf = open(hashfile, 'rb')

   
   assert(path.exists(blkfile))
   blkfileSize = os.stat(blkfile).st_size
   bf = open(blkfile, 'rb')

   
   startBlkByte = binary_to_int(hf.read(8))
   hf.close()
   hf = open(hashfile, 'r+')
   hf.write(int_to_binary(blkfileSize, widthBytes=8))
   hf.seek(0,2) # start writing at the end of the file

   # The first line of the hashfile tells us where to start searching
   # blk0001.dat (so we don't recompute every time).  We need to rewrite
   # this line every time. 

   bf.seek(startBlkByte, 0)  # seek to this point in the file

   binunpack = BinaryUnpacker(bf.read())
   print 'Amount of data to read from blkfile: %d bytes' % (blkfileSize)
   newBlocksRead = 0
   newHashes = 0
   while( binunpack.getRemainingSize() > 0):
      binunpack.advance(4)  # magic
      sz = binunpack.get(UINT32)  # total bytes in this block
      thisHeader = BlockHeader().unserialize(binunpack)
      hf.write(thisHeader.theHash + '\x01')
      hf.write(thisHeader.merkleRoot + '\x02')
      thisData = BlockData().unserialize(binunpack)
      for tx in thisData.txList:
         hf.write(tx.thisHash + '\x03')
      newHashes += 2 + len(thisData.txList)
      newBlocksRead += 1

   
   if(newBlocksRead%1000):
      if(newBlocksRead%10000):
         print '\n\tRead', newBlocksRead, 'blocks',
      print '.',
      sys.stdout.flush()


   
   print 'Read', newHashes, 'new hashes in', newBlocksRead, 'new blocks from blkfile'
   hf.close()

   


if __name__ == '__main__':
   from optparse import OptionParser

   parser = OptionParser(usage='USAGE: %prog [--binary|-b] -f FILE \n   or: %prog hexToIdentify')
   parser.add_option('-f', '--file',   dest='filename', \
                  help='Get unidentified data from this file')
   parser.add_option('-k', '--blkfile', dest='blk0001file', default='~/.bitcoin/blk0001.dat', \
                  help='Update hashlist from this file (default ~/.bitcoin/blk0001.dat)')
   parser.add_option('-g', '--hashfile', dest='hashfile', default='./knownHashes.txt', \
                  help='Update hashlist from this file (default ~/.bitcoin/blk0001.dat)')
   parser.add_option('-b', '--binary', action='store_false', dest='isHex', default=True, \
                  help='Specified file is in binary')
   parser.add_option('-s', '--nohashes', action='store_false', dest='useHashes', default=True, \
                  help='Do not import header/tx hashes to be used in searching')
   parser.add_option('-u', '--noupdate', action='store_false', dest='updateHashes', default=True, \
                  help='Do not search blk0001.dat to update hashlist')
   
   (options, args) = parser.parse_args()   

   fn = options.filename
   isHex = options.isHex
   blkfile = options.blk0001file
   hashfile = options.hashfile

   if fn == None and len(args)==0:
      parser.error('Please supply a hex data or a file with unidentified data')

   if not fn == None and not path.exists(fn):
      parser.error('Cannot find ' + fn)

   if fn == None and not isHex:
      parser.error('Cannot read binary data from command line.  Please put it in a file and use -f option')
   
   if not path.exists(blkfile):
      print 'Cannot find blockdata file', blkfile, '... proceeding without updating hashes'
      options.updateHashes = False

   if(options.useHashes and options.updateHashes):
      updateHashList(hashfile, blkfile)

   binaryToSearch = []
   if not fn == None:
      if not isHex:
         f = open(fn, 'rb')
         binaryToSearch = f.read()
         f.close()
      else:
         f = open(fn, 'r')
         hexLines = f.readlines()
         hexToSearch = [l.strip().replace(' ','') for l in hexLines]
         binaryToSearch = hex_to_binary(hexToSearch)
   else:
      # pull data from the remaining arguments (which must be hex)
      hexToSearch = ''.join(args)
      binaryToSearch = hex_to_binary(hexToSearch.replace(' ',''))
      
   
   # Yeah, I know we just converted it to binary, now back to hex
   figureOutMysteryHex(binary_to_hex(binaryToSearch))
         
         

      

















