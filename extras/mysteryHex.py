#! /usr/bin/python
from os import path
import sys
from optparse import OptionParser

sys.path.append('..')
from pybtcengine import *

HASHCODE_HEADER = 1
HASHCODE_MERKLE = 2
HASHCODE_TX     = 3

################################################################################
################################################################################
def figureOutMysteryHex(hexStr, hashDict={}):
   binStr = hex_to_binary(hexStr)
   print '\n' + '-'*80
   print '\nStarting hex data:', len(binStr), 'bytes'
   hexStr.replace(' ','')
   pprintHex(hexStr, '   ')
   print '\n' + '-'*80
   

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
   idListSimple = []

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
      if idx<=len(binStr)-80:
         hashZeros = binStr[idx+32:idx+36] == hintStr['Empty4B']
         validTime = timeMin < binary_to_int(binStr[idx+68:idx+72]) < timeMax
         if hashZeros and validTime:
            bin80 = binStr[idx:idx+80]
            blkhead = PyBlockHeader().unserialize(bin80) 
            idListExcl.append(['BlockHeader', idx, idx+80, binary_to_hex(bin80), blkhead])
            maskAll[idx:idx+80] = [1]*80
            continue 
      
      # If not a header, check to see if it's a Tx
      try:
         testTx = PyTx().unserialize(binStr[idx:])
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

   pubkeyList = [ ]
   
   # Try to find a PkScript
   pkIdx = getIdxListNotIdYet(hintStr['PkStart'], maskAll)
   for idx in pkIdx:
      if binStr[idx+23:idx+25] == hintStr['PkEnd']:
         addrStr = PyBtcAddress().createFromPublicKeyHash160(binStr[idx+3:idx+23])
         extraInfo = addrStr.getAddrStr()
         idListSimple.append(['TxOutScript', idx, idx+25, extraInfo, ''])
         maskAll[idx:idx+25] = [1]*25

   startCBPK = hex_to_binary('04')
   pkIdx = getIdxListNotIdYet(startCBPK, maskAll)
   for idx in pkIdx:
      if idx > len(binStr)-65:
         continue
      try:
         addrStr = PyBtcAddress().createFromPublicKey(binStr[idx:idx+65])
         extraInfo = addrStr.calculateAddrStr()
         if not idx+65==len(binStr) and binStr[idx+65] == hex_to_binary('ac'):
            idListSimple.append(['CoinbaseScript', idx, idx+66, extraInfo, ''])
            maskAll[idx:idx+66] = [1]*66
         else:
            idListSimple.append(['BarePublicKey', idx, idx+65, extraInfo, ''])
            maskAll[idx:idx+65] = [1]*65

         if idx>0 and binStr[idx-1]  == hex_to_binary('41'):
            idListSimple[-1][1] -= 1  # get the 41 that's there if it's a script
            maskAll[idx-1] = 1
      except:
         pass # I guess this wasn't a PK after all...
         

   ############################################################################
   # Random straightforward things to search for without any extra computation.
   ############################################################################
   for triplet in simpleList:
      foundIdx = getIdxList( hex_to_binary(triplet[0]))
      for idx in foundIdx:      
         idListSimple.append([triplet[1], idx, idx+len(triplet[0])/2, triplet[2], ''])


         

   # If we have a useful dictionary of hashes, let's use it
   if len(hashDict) > 0:
      for i in range(len(binStr)-31):
         if maskAll[i] == 1:
            continue
         str32 = binStr[i:i+32]
         if hashDict.has_key(str32):
            hashcode = hashDict[str32]
            if hashcode==HASHCODE_HEADER:
               hashCode = 'HeaderHash'
            elif hashcode==HASHCODE_MERKLE:
               hashCode = 'MerkleRoot'
            elif hashcode==HASHCODE_TX:
               hashCode = 'TxHash'
            else:
               hashCode = 'UnknownHash'
            idListSimple.append([hashCode, i, i+32, binary_to_hex(str32), ''])
         elif hashDict.has_key(binary_switchEndian(str32)):
            hashcode = hashDict[binary_switchEndian(str32)]
            if hashcode==HASHCODE_HEADER:
               hashCode = 'HeaderHash(BE)'
            elif hashcode==HASHCODE_MERKLE:
               hashCode = 'MerkleRoot(BE)'
            elif hashcode==HASHCODE_TX:
               hashCode = 'TxHash(BE)'
            else:
               hashCode = 'UnknownHash'
            idListSimple.append([hashCode, i, i+32, binary_to_hex(str32), ''])


   ############################################################################
   # Done searching for stuff.  Print results
   ############################################################################
   for ids in idListExcl:
      print ''
      print '#'*100
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
         print ''
         ids[4].pprint(1)
      print ''
      print '#'*100


   # Print all the simple stuff onto a single bytemap
   print 'Other assorted things:'
   idListSimple.sort(key=lambda x: x[1])
   hexToPrint = ['-'] * 2*len(binStr) 
   ReprList = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
   for j,ids in enumerate(idListSimple):
      i1 = ids[1]
      i2 = ids[2]
      nb = i2-i1
      maskAll[i1:i2] = [1]*nb
      hexToPrint[2*i1:2*i2] = ReprList[j]*2*nb

   hexToPrint = ''.join(hexToPrint)
   pprintHex(hexToPrint, '   ')

   print ''
   for j,ids in enumerate(idListSimple):
      print '  ', ReprList[j] + ':', ids[0].ljust(16,' '), ':', ids[3]
      
   print '\n\nUnidentified bytes'
   maskedBytes = ['--' if maskAll[i] == 1 else hexStr[2*i:2*i+2] for i in range(len(binStr))]
   
   pprintHex(''.join(maskedBytes));
   


################################################################################
################################################################################
def updateHashList(hashfile, blkfile, rescan=False):

   print ''
   print '\t.Updating hashlist from the blockchain file in your bitcoin directory'
   print '\t.This will take 1-5 min the first time you run this script (and on rescan)'
   print '\t\t.Hashfile: ', hashfile
   print '\t\t.BlockFile:', blkfile
   if not path.exists(hashfile) or rescan:
      hf = open('knownHashes.bin','wb')
      hf.write('\x00'*8)
      hf.close()

   hf = open(hashfile, 'rb')
   startBlkByte = binary_to_int(hf.read(8))
   hf.close()

   
   assert(path.exists(blkfile))
   blkfileSize = os.stat(blkfile).st_size
   bf = open(blkfile, 'rb')

   
   hf = open(hashfile, 'r+')
   hf.write(int_to_binary(blkfileSize, widthBytes=8))
   hf.seek(0,2) # start writing at the end of the file

   # The first 8 bytes of the hashfile tells us where to start searching
   # blk0001.dat (so we don't recompute every time).  We need to rewrite
   # this value every time
   bf.seek(startBlkByte, 0)  # seek to this point in the file

   binunpack = BinaryUnpacker(bf.read())
   newBlocksRead = 0
   newHashes = 0
   while( binunpack.getRemainingSize() > 0):
      binunpack.advance(4)  # magic
      sz = binunpack.get(UINT32)  # total bytes in this block
      thisHeader = PyBlockHeader().unserialize(binunpack)
      hf.write(thisHeader.theHash + '\x01')
      hf.write(thisHeader.merkleRoot + '\x02')
      thisData = PyBlockData().unserialize(binunpack)
      for tx in thisData.txList:
         hf.write(tx.thisHash + '\x03')
      newHashes += 2 + len(thisData.txList)

      if newBlocksRead==0:
         print '\n\t\tReading blocks...',
      newBlocksRead += 1
      if(newBlocksRead%1000==0):
         if(newBlocksRead%10000==0):
            print '\n\t\tRead', newBlocksRead, 'blocks',
         print '.',
         sys.stdout.flush()

   
   print '\n\t.Updated hashfile with %d bytes / %d hashes / %d blocks from blkfile' % \
                  (blkfileSize-startBlkByte, newHashes, newBlocksRead)
   hf.close()

   


if __name__ == '__main__':
   print '\nTry to identify Bitcoin-related strings in a block of data'

   parser = OptionParser(usage='USAGE: %prog [--binary|-b] -f FILE \n   or: %prog unidentifiedHex')
   parser.add_option('-f', '--file',   dest='filename', \
                  help='Get unidentified data from this file')
   parser.add_option('-k', '--blkfile', dest='blk0001file', default='', \
                  help='Update hashlist from this file (default ~/.bitcoin/blk0001.dat)')
   parser.add_option('-g', '--hashfile', dest='hashfile', default='./knownHashes.bin', \
                  help='The file to store and retrieve header/tx hashes')
   parser.add_option('-b', '--binary', action='store_false', dest='isHex', default=True, \
                  help='Specified file is in binary')
   parser.add_option('--byterange', dest='byterange', default='all', \
                  help='Bytes to read, --byterange=0,100')
   parser.add_option('-s', '--usehashes', action='store_true', dest='useHashes', default=False, \
                  help='Import header/tx hashes to be used in searching')
   parser.add_option('-u', '--noupdatehashes', action='store_false', dest='updateHashes', default=True, \
                  help='Disable searching blk0001.dat to update hashlist (ignored without -s)')
   parser.add_option('-r', '--rescanhashes', action='store_true', dest='doRescan', default=False, \
                  help='Rescan blkfile for header/tx hashes')
   #parser.add_option('-t', '--testnet', action='store_true', dest='testnet', default=False, \
                  #help='Run the script using testnet data/addresses')
   # Should add option for picking (start,end) bytes for files that are long
   #parser.add_option('-o', '--outfile', dest='outfile', default='', \
                  #help='Redirect results to output file')
   
   (opts, args) = parser.parse_args()   


   fn       = opts.filename
   isHex    = opts.isHex
   blkfile  = opts.blk0001file
   hashfile = opts.hashfile
   #outfile  = opts.outfile

   if len(blkfile)==0 and opts.updateHashes:
      import platform
      opsys = platform.system()
      if 'win' in opsys.lower():
         blkfile = path.join(os.getenv('APPDATA'), 'Bitcoin', 'blk0001.dat')
      if 'nix' in opsys.lower() or 'nux' in opsys.lower():
         blkfile = path.join(os.getenv('HOME'), '.bitcoin', 'blk0001.dat')
      if 'mac' in opsys.lower() or 'osx' in opsys.lower():
			blkfile = os.path.expanduser('~/Library/Application Support/Bitcoin/blk0001.dat')

   # A variety of error conditions
   if fn == None and len(args)==0:
      parser.error('Please supply hex data or a file with unidentified data\n')
   if not fn == None and not path.exists(fn):
      parser.error('Cannot find ' + fn)
   if fn == None and not isHex:
      parser.error('Cannot read binary data from command line.  Please put it in a file and use -f option')
   if not path.exists(blkfile) and opts.useHashes and opts.updateHashes:
      print 'Cannot find blockdata file', blkfile, '... proceeding without updating hashes'
      opts.updateHashes = False

   if not opts.useHashes:
      print '\t(use the -s option to enable search for header/tx hashes from blk0001.dat)'

   byteStart,byteStop = 0,0
   print opts.byterange
   if not opts.byterange=='all':
      byteStart,byteStop = [int(i) for i in opts.byterange.split(',')]

   # Update the knownHashes.txt file, if necessary
   if(opts.useHashes and opts.updateHashes):
      updateHashList(hashfile, blkfile, opts.doRescan)

   # If we plan to use it, populate a dictionary of hashes
   hashDict = {}
   if(opts.useHashes):
      hfile = open(hashfile, 'rb')
      skip = hfile.read(8)
      binaryHashes = hfile.read()
      hfile.close()
      print '\t.Reading %s (%0.1f MB)' % (hashfile, len(binaryHashes)/float(1024**2))
      if not opts.updateHashes:
         print '\t (remove -u flag to update hashlist with recent blocks from blk0001.dat'
      nHash = len(binaryHashes) / 33
      for i in range(nHash):
         loc = i*33
         hash32 = binaryHashes[loc:loc+32]
         code   = binaryHashes[loc+32]
         hashDict[hash32] = binary_to_int(code)
      print '\t.Hash dictionary populated with %d hashes from %s' % (len(hashDict),hashfile)

   binaryToSearch = []
   if not fn == None:
      if not isHex:
         f = open(fn, 'rb')
         binaryToSearch = ''
         if byteStop<=byteStart:
            binaryToSearch = f.read()
         else:
            f.seek(byteStart,0);
            binaryToSearch = f.read(byteStop-byteStart)
         
         f.close()
      else:
         f = open(fn, 'r')
         hexLines = f.readlines()
         hexToSearch = ''.join([l.strip().replace(' ','') for l in hexLines])
         if not byteStop<=byteStart:
            hexToSearch = hexToSearch[2*byteStart:2*byteStop]

         try:
            binaryToSearch = hex_to_binary(hexToSearch)
         except:
            print 'Error processing %s.  If this is a binary file, please use the -b flag' % (fn,)
            exit(0)
   else:
      # pull data from the remaining arguments (which must be hex)
      hexToSearch = ''.join(args)
      binaryToSearch = hex_to_binary(hexToSearch.replace(' ',''))
      
   
   # Yeah, I know we just converted it to binary, now back to hex
   figureOutMysteryHex(binary_to_hex(binaryToSearch), hashDict)
         
         

      

















