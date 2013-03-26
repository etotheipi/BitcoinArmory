import sys
sys.path.append('..')

import os
from armoryengine import *


def parseDownloadList(wholeFile):
   """
   This method returns a pair: a dictionary to lookup link by OS, and 
   a formatted string that is sorted by OS, and re-formatted list that 
   will hash the same regardless of original format or ordering
   """
   DLDICT,DLLIST = {},[]
   for line in wholeFile.split('\n'):
      pcs = line.strip().strip('#').split()
      if len(pcs)==3 and pcs[1].startswith('http'):
         DLDICT[pcs[0]] = pcs[1:]
         DLLIST.append(pcs)
      if 'ARMORY-SIGNATURE' in line:
         sigHex = line.strip().split()[-1]

   DLLIST.sort(key=lambda x: x[0])
   return DLDICT, ('\n'.join([' '.join(trip) for trip in DLLIST])), sigHex




if __name__=='__main__':
   fn = 'versions.txt'
   if not os.path.exists(fn):
      print 'File does not exist!'

   f = open(fn, 'r')
   allVerStr = f.read()

   DICT,STR,SIG = parseDownloadList(allVerStr)

   for dl in DICT:
      print dl
      print '   ', DICT[dl][0]
      print '   ', DICT[dl][1]


   Pub = SecureBinaryData(hex_to_binary(ARMORY_INFO_SIGN_PUBLICKEY))
   Msg = SecureBinaryData(STR)
   Sig = SecureBinaryData(hex_to_binary(SIG.split()[-1]))
   
   
   isVerified = CryptoECDSA().VerifyData(Msg, Sig, Pub)
   print '**********'
   print ''
   print 'Signature Matches Public Key:', isVerified
   print ''
   print '**********'

   
