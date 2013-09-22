from sys import path,argv
import os
import getpass
path.append('..')

from armoryengine import *

if '--testnet' in argv:
   i = argv.index('--testnet')
   del argv[i]

testRecon = False
if '--test' in argv:
   testRecon = True
   i = argv.index('--test')
   del argv[i]

if len(argv)<2:
   print ''
   print 'USAGE: %s <file.wallet> <m> <n> ' % argv[0]
   print ''
   print 'Will produce N files, of which any subset of M of them is '
   print 'sufficient to reproduce your wallet.'
   print ''
   exit(0)


files = argv[1:]
for filename in files:
   if not os.path.exists(filename):
      print 'ERROR: File does not exist: %s' % filename
      exit(0)

frags = []
wltIdList = []
mList = []
fnumList = []

for filename in files:
   frags.append({})
   with open(filename,'r') as f:
      allData = [line.strip() for line in f.readlines()]

   for line in allData:
      if line[:2].lower() in ['id','x1','x2','x3','x4','y1','y2','y3','y4','f1','f2','f3','f4']:
         frags[-1][line[:2].lower()] = line[3:].replace(' ','')

   m = hex_to_int(frags[-1]['id'][:2])
   fnum = hex_to_int(frags[-1]['id'][2:4])
   wltID = binary_to_base58(hex_to_binary(frags[-1]['id'][4:]))

   wltIdList.append([filename, wltID])
   mList.append([filename, m])
   fnumList.append([filename, fnum])


mset = set([x[1] for x in mList])
if len(mset)>1:
   print 'ERROR: Not all fragments use the same M-value!'
   for filename,m in mList:
      print '   %s: M=%d' % (filename, m)
   exit(0)

idset = set([x[1] for x in wltIdList])
if len(idset)>1:
   print 'ERROR: Not all fragments are for the same wallet!'
   for filename,fid in wltIdList:
      print '   %s: %s' % (filename, fid)
   print 'If you are sure these are for the same wallet, check the "ID:" lines'
   exit(0)

netbyte = base58_to_binary(wltIdList[0][1])[-1]
if not netbyte==ADDRBYTE:
   print 'Wallet is for the wrong network!!!'
   print 'You are running on:  %s' % NETWORKS[ADDRBYTE]
   if NETWORKS.has_key(netbyte):
      print 'Wallet is for:       %s' % NETWORKS[netbyte]
   else:
      print 'Wallet is for:       Unknown Network(%s)' % binary_to_hex(netbyte)
   exit(0)


fnumset = set([x[1] for x in fnumList])
if len(fnumset)<len(frags):
   print 'ERROR: Some files are duplicates!'
   fnumList.sort(key=lambda x: x[1]) 
   for filename,fnum in fnumList:
      print '   %s is \t Fragment %s' % (filename, fnum)
   exit(0)


M = mList[0][1]
print ''
print '*'*80
print '* Restoring wallet from %d-of-N fragmented backup! ' % M
print '*'*80
print ''

fragMtrx = []
for i,fragMap in enumerate(frags):

   def checkLine(line, prefix):
      bin16,err = readSixteenEasyBytes(line)
      if err=='Error_2+':
         print 'ERROR:  Uncorrectable error'
         print '        File: ', files[i]
         print '        Line: ', prefix
         exit(0)
      elif err=='Fixed_1':
         print ' Error corrected,  %s:%s' % (files[i], prefix)
      elif err=='No_Checksum':
         print ' Checksum absent,  %s:%s' % (files[i], prefix)
      return bin16

   x,y,f = ['']*4, ['']*4, ['']*4
   
   for prefix,data in fragMap.iteritems():
      if prefix.lower()=='id':
         continue
      
      rawData = checkLine(data,prefix)
      L = prefix[0].lower()
      toList = x if L=='x' else (y if L=='y' else f)
      toList[int(prefix[1])-1] = rawData

   if len(x[0])==0 and len(f[0])>0: 
      fragnum = fragMap['id'][2:4]
      fragMtrx.append( [hex_to_binary(fragnum), ''.join(f)] )
   else:
      fragMtrx.append( [''.join(x), ''.join(y)] )

M = mList[0][1]
testFrags = len(fragMtrx)>M
wltID = wltIdList[0][1]
   

sp = lambda x,n,s: s.join([x[i*n:i*n+n] for i in range((len(x)-1)/n+1)])
recon = ReconstructSecret(fragMtrx, M, 64)

print 'Recovered paper backup: %s\n' % wltID
pcs = [recon[i*16:(i+1)*16] for i in range(4)]
for pc in pcs:
   print '   ', makeSixteenBytesEasy(pc)

if not testRecon and len(argv[1:])>M:
   print ''
   print 'You have supplied more pieces (%d) than needed for reconstruction (%d).' % (len(argv[1:]), M)
   print 'Are you trying to run the reconstruction test instead of actually '
   print 'recovering the wallet?  If so, wallet recovery will be skipped.  [Y/n]',
   response = raw_input('')
   if not response.lower().startswith('n'):
      testRecon = True

if testRecon:
   import random
   print ''
   print 'Testing reconstruction on 20 subsets: '
   dec = [(i,z[0],z[1]) for i,z in enumerate(fragMtrx)]
   for test in range(20):
      indices,xys = [0]*M, [[0,0] for i in range(M)]
      random.shuffle(dec)
      for j in range(M):
         indices[j], xys[j][0], xys[j][1]= dec[j]
      print (('   Using fragments (%s)' % ','.join(['%d']*M)) % tuple(sorted(indices))),
      sec = ReconstructSecret(xys, M, 64)
      print ' Reconstructed (first line of paper backup): %s' % makeSixteenBytesEasy(sec[:16])
   exit(0)
else:
   print '\nProceeding with wallet recovery...'

print ''
doEncr = raw_input('Would you like to encrypt the recovered wallet? [Y/n]: ')
filename = 'armory_%s_recovered.wallet' % wltID
name = 'Recovered wallet'
descr = 'Wallet recovered from fragmented backup.'
if doEncr.lower().startswith('y'):
   print 'Choose an encryption passphrase:'
   while True:
      passwd1 = getpass.getpass('   Passphrase: ')
      passwd2 = getpass.getpass('        Again: ')
      if not passwd1==passwd2:
         print 'Passphrases do not match!  Try again...'
      elif len(passwd1)<5:
         print 'Passphrase is too short!  Try again (5+ chars, 8 recommened)...'
      else:
         break

   print 'Set the key-stretching parameters:'
   kdfSec = 0.25
   while True:
      try:
         inp = raw_input('   Seconds to compute (default 0.25): ')
         if len(inp.strip())==0:
            break
         kdfSec = float(inp)
         break
      except ValueError:
         raise
         print 'Bad value!  Please enter compute time in seconds'

   
   kdfMaxMem = 32
   while True:
      try:
         inp = raw_input('   Max RAM used, in MB (default 32):  ')
         if len(inp.strip())==0:
            break
         kdfMaxMem = int(inp)
         break
      except ValueError:
         raise
         print 'Bad value!  Please enter RAM usage in MB'

   passwd = SecureBinaryData(passwd1)
         
   print 'Creating new wallet...'
   newWallet = PyBtcWallet().createNewWallet( \
                                     newWalletFilePath=filename, \
                                     plainRootKey=recon[:32], \
                                     chaincode=recon[32:], \
                                     withEncrypt=True, \
                                     securePassphrase=passwd, \
                                     kdfTargSec=kdfSec, \
                                     kdfMaxMem=kdfMaxMem, \
                                     shortLabel=name, \
                                     longLabel=descr, \
                                     doRegisterWithBDM=False)
   newWallet.unlock(securePassphrase=passwd)

else:
   newWallet = PyBtcWallet().createNewWallet( \
                                     newWalletFilePath=filename, \
                                     plainRootKey=recon[:32], \
                                     chaincode=recon[32:], \
                                     withEncrypt=False, \
                                     shortLabel=name, \
                                     longLabel=descr, \
                                     doRegisterWithBDM=False)

print 'Please wait while the address pool is being populated....'
newWallet.fillAddressPool(doRegister=False)
print ''
print 'Successfully restored wallet!',  filename
print ''
