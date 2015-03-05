import sys
sys.path.append('..')
sys.path.append('/usr/share/armory')

import os
from armoryengine import *


def extractSignedDataFromVersionsDotTxt(wholeFile, doVerify=True):
   """
   This method returns a pair: a dictionary to lookup link by OS, and 
   a formatted string that is sorted by OS, and re-formatted list that 
   will hash the same regardless of original format or ordering
   """

   msgBegin = wholeFile.find(b'# -----BEGIN-SIGNED-DATA-')
   msgBegin = wholeFile.find(b'\n', msgBegin+1) + 1
   msgEnd   = wholeFile.find(b'# -----SIGNATURE---------')
   sigBegin = wholeFile.find(b'\n', msgEnd+1) + 3
   sigEnd   = wholeFile.find(b'# -----END-SIGNED-DATA---')

   MSGRAW = wholeFile[msgBegin:msgEnd]
   SIGHEX = wholeFile[sigBegin:sigEnd].strip()

   if -1 in [msgBegin,msgEnd,sigBegin,sigEnd]:
      LOGERROR('No signed data block found')
      return ''

   print('MESSAGE:  ')
   print(MSGRAW.decode())
   print('SIGNATURE:')
   print(SIGHEX.decode())

   
   if doVerify:
      Pub = SecureBinaryData()
      Pub.createFromHex(ARMORY_INFO_SIGN_PUBLICKEY.decode())
      Msg = SecureBinaryData()
      Msg.createFromHex(binary_to_hex(MSGRAW).decode())
      Sig = SecureBinaryData()
      Sig.createFromHex(SIGHEX.decode())
      isVerified = CryptoECDSA().VerifyData(Msg, Sig, Pub)
   
      if not isVerified:
         LOGERROR('Signed data block failed verification!')
         return ''
      else:
         print('SIGNATURE IS GOOD!')


   return MSGRAW


def parseLinkList(theData):
   """ 
   Plug the verified data into here...
   """
   DLDICT,VERDICT = {},{}
   sectStr = None
   for line in theData.split('\n'): 
      pcs = line[1:].split()
      if line.startswith('# SECTION-') and 'INSTALLERS' in line:
         sectStr = pcs[0].split('-')[-1].lower()
         if not sectStr in DLDICT:
            DLDICT[sectStr] = {}
            VERDICT[sectStr] = ''
         if len(pcs)>1:
            VERDICT[sectStr] = pcs[-1]
         continue
      
      if len(pcs)==3 and pcs[1].startswith('http'):
         DLDICT[sectStr][pcs[0]] = pcs[1:]

   return DLDICT,VERDICT


if __name__=='__main__':
   fn = 'versions.txt'
   if not os.path.exists(fn):
      print('File does not exist!')
      fn = '../versions.txt'
      if not os.path.exists(fn):
         print('Really does not exist. Aborting.')
         exit(1)

   f = open(fn, 'r')
   allData = f.read()

   msgVerified = extractSignedDataFromVersionsDotTxt(allData, doVerify=False)
   DICT,VER = parseLinkList(msgVerified)
         
   print(DICT)
   for dl in DICT:
      print(dl.upper(), VER[dl])
      for theOS in DICT[dl]:
         print('   ' + dl + '-' + theOS)
         print('      ', DICT[dl][theOS][0])
         print('      ', DICT[dl][theOS][1])

   msgVerified = extractSignedDataFromVersionsDotTxt(allData)
      
   


   
