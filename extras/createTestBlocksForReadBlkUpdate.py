from sys import path
path.append('..')

from armoryengine import *

TheBDM.setBlocking(True)
TheBDM.setOnlineMode(True)

if not os.path.exists('testmultiblock'):
   os.mkdir('testmultiblock')

fout = []
fout.append([0,   101, 'testmultiblock/blk00000.dat'])
fout.append([0,   102, 'testmultiblock/blk00000_test1.dat']) # Add 1 block
fout.append([0,   105, 'testmultiblock/blk00000_test2.dat']) # Add 3 blocks
fout.append([106, 106, 'testmultiblock/blk00001_test3.dat']) # Just block split
fout.append([107, 109, 'testmultiblock/blk00002_test4.dat']) # Another block split 3 blks
fout.append([107, 110, 'testmultiblock/blk00002_test5.dat']) # Add block 
fout.append([110, 113, 'testmultiblock/blk00003_test5.dat']) #      and split


for start,end,theFile in fout:
   if os.path.exists(theFile):
      os.remove(theFile)

lastLocation = [0]*len(fout)
openfiles    = [[trip[0], trip[1], open(trip[2],'wb')] for trip in fout]

# Assume we are only reading into blk000000.dat, no split
for h in range(120):
   head = TheBDM.getHeaderByHeight(h)
   blk = head.serializeWholeBlock(MAGIC_BYTES, True)
   for i,trip in enumerate(openfiles):
      start,end,theFile = trip
      if (start <= h <= end):
         theFile.write(blk)
         lastLocation[i] += len(blk)
   

for start,end,opnfil in openfiles:
   opnfil.close()
   
   
for i,trip in enumerate(fout):
   start,end,theFile = trip
   sz = os.path.getsize(theFile)
   f = open(theFile,'ab')
   if i<3:
      f.write('\x00'*(22000-sz))
   else:
      f.write('\x00'*(1000-sz))
   f.close()

print 'Blocks written out:'
for start,end,fn in fout:
   if end-start==0:
      print '\t%d    in file: %s' % (end,fn)
   else:
      print '\t%d-%d in file: %s' % (start,end,fn)

