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

frags = []
wltIdList = []
mList = []

for fn in files:
   frags.append({})
   with open(fn,'r') as f:
      allData = [line.strip() for line in f.readlines()]

   for line in allData:
      if line[:2].lower() in ['id','x1','x2','x3','x4','y1','y2','y3','y4']:
         frags[-1][line[:2].lower()] = line[3:].replace(' ','')

   m = hex_to_int(frags[-1]['id'][:2])
   wltID = binary_to_base58(hex_to_binary(frags[-1]['id'][2:]))

   wltIdList.append([fn, wltID])
   mList.append([fn, m])


mset = set([x[1] for x in mList])
if len(mset)>1:
   print 'ERROR: Not all fragments use the same M-value!'
   for fn,m in mList:
      print '   %s: M=%d' % (fn, m)
   exit(0)

idset = set([x[1] for x in wltIdList])
if len(idset)>1:
   print 'ERROR: Not all fragments are for the same wallet!'
   for fn,fid in wltIdList:
      print '   %s: %s' % (fn, fid)
   exit(0)


fragMtrx = []
for i,fragMap in enumerate(frags):

   def checkLine(line, prefix):
      binAll = easyType16_to_binary(line)
      bin16  = binAll[:-2] 
      chk2   = binAll[ -2:] 
      bin16Fix = verifyChecksum(bin16, chk2)
      if len(bin16Fix)==0:
         print 'ERROR:  Uncorrectable error'
         print '        File: ', files[i]
         print '        Line: ', prefix
         exit(0)
      if not bin16==bin16Fix:
         print ' Error corrected,  %s:%s' % (files[i], prefix)
      return bin16Fix

   x,y = ['']*4, ['']*4
   
   for prefix,data in fragMap.iteritems():
      if prefix.lower()=='id':
         continue
      
      rawData = checkLine(data,prefix)
      toList = x if prefix[0].lower()=='x' else y
      toList[int(prefix[1])-1] = rawData

    
   fragMtrx.append( [''.join(x), ''.join(y)] )

M = mList[0][1]
testFrags = len(fragMtrx)>M
   

sp = lambda x,n,s: s.join([x[i*n:i*n+n] for i in range((len(x)-1)/n+1)])
for f in fragMtrx:
   print [binary_to_hex(a) for a in f]
recon = ReconstructSecret(fragMtrx, M, 64)

print 'Recovered paper backup:'
pcs = [recon[i*16:(i+1)*16] for i in range(4)]
for pc in pcs:
   full = pc + computeChecksum(pc, nBytes=2)
   print '   ',sp(binary_to_easyType16(full), 4, ' ')


print ''
doEncr = raw_input('Would you like to encrypt the recovered wallet? [Y/n]: ')
name = 'armory_%s_recovered.wallet' % wltID
descr = 'Wallet recovered from fragmented backup.'
if doEncr.lower().startswith('y'):
   while True:
      passwd1 = getpass.getpass('Encrypt using passphrase: ')
      passwd2 = getpass.getpass('Re-enter you passphrase:  ')
      if not passwd1==passwd2:
         print 'Passphrases do not match!  Try again...'
      elif len(passwd1)<5:
         print 'Passphrase is too short!  Try again (5+ chars, 8 recommened)...'
      else:
         break

   passwd = SecureBinaryData(passwd1)
         
   newWallet = PyBtcWallet().createNewWallet( \
                                     withEncrypt=True, \
                                     securePassphrase=passwd, \
                                     kdfTargSec=kdfSec, \
                                     kdfMaxMem=kdfBytes, \
                                     shortLabel=name, \
                                     longLabel=descr, \
                                     doRegisterWithBDM=False)
   newWallet.unlock(securePassphrase=passwd)

else:
   newWallet = PyBtcWallet().createNewWallet( \
                                     withEncrypt=False, \
                                     shortLabel=name, \
                                     longLabel=descr, \
                                     doRegisterWithBDM=False)

print 'Please wait while the address pool is being populated....'
newWallet.fillAddressPool(doRegister=False)
