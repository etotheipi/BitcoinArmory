from sys import path,argv
import os
path.append('..')

from armoryengine import *

if len(argv)<2:
   print ''
   print 'USAGE: %s <file.wallet> <m> <n> ' % argv[0]
   print ''
   print 'Will produce N files, of which any subset of M of them is '
   print 'sufficient to reproduce your wallet.'
   print ''
   exit(0)


files = argv[1:]
for fn in files:
   if not os.path.exists(fn):
      print 'ERROR: File does not exist: %s' % fn
      exit(0)

fragIDset = set([])
Mset = set([])
frags = []

for fn in files:
   frags.append({})
   with open(fn,'r') as f:
      allData = [line.strip() for line in f.readlines()]

   for line in allData:
      if line[:2].lower() in ['id','x1','x2','x3','x4','y1','y2','y3','y4']:
         frags[-1][line[:2].lower()] = line[3:].replace(' ','')


   print frags
   raw_input('pause')





