################################################################################
# This takes a sample AddressEntry serialization as seen in the wallet files,
# and appends 500k copies of it with private keys found in the wltfile.  This 
# is useful for appending mass amounts of addresses to your wallet, though don't
# expect ArmoryQt.py to work with 500k+ addresses.  But the underlying C++ code
# CAN handle it.
################################################################################
import os
import sys
sys.path.append('..')
from armoryengine import *


print '*'*80
print '* WARNING:  THIS SCRIPT IS VERY DANGEROUS!  '
print '*           IT DIRECTLY MODIFIES ARMORY WALLETS AT THE BINARY LEVEL.'
print '*           DO NOT USE WHILE ARMORY IS RUNNING! '
print '*           MAKE A BACKUP OF YOUR WALLET BEFORE RUNNING THIS SCRIPT!'
print '*           '
print '*           THIS SCRIPT IS A TOY, NOT GUARNATEED TO BE FIT FOR ANY'
print '*           PURPOSE.  NO WARRANTIES, NO EXPECTATIONS.  NO COMPLAINTS.'
print '*           Please.'
print '*'*80
ans = raw_input('Yeah yeah, I get it... right? [y/N]: ')
if not ans.lower().startswith('y'):
   exit(0)


# Could use sys.argv but this script will be used, like, once.  Hardcode it!
wltID        = '6hR6bAcW' # this was the ID of the wallet I tested with
wltDir       = '6hR6bAcW' # this was the ID of the wallet I tested with
keyfile      = '../allprivatekeys.txt'
NLINESTOREAD = 500000

def extractPrivateKeyFromLine(line):
   # Modify this function according to the format of the private keys in keyfile
   # Currently assumes format,  "<addrString>:<privateKeySipaFormat>:<otherData>"
   # Sipa format is:  
   #   encodedKey = '\x80' + rawPrivKey32 + hash256('\x80'+rawPrivKey32)[:4]
   #   len(encodedKey)==37
   pcs = line.strip().split(':')
   return base58_to_binary(pcs[1])[1:-4]
   

wltfile    = os.path.join(ARMORY_HOME_DIR, 'armory_%s_.wallet' % wltID)
wltfilebak = os.path.join(ARMORY_HOME_DIR, 'armory_%s_backup.wallet' % wltID)


if not os.path.exists(wltfile):
   print 'ERROR: Wallet does not exist:', wltfile
   exit(1)

if not os.path.exists(keyfile):
   print 'ERROR: Keyfile does not exist:', keyfile
   exit(1)

# Remove the backup if it exists
if os.path.exists(wltfilebak):
   os.remove(wltfilebak)




# If you don't delete the backup, Armory will think the primary wallet 
# is corrupted and restore the backup

exampleEntry = hex_to_binary( \
  '0047b8ad 0b1d6803 260ce428 d9e09e2c d99fd3b3 5947b8ad 0b1d6803 260ce428 '
  'd9e09e2c d99fd3b3 59fb1670 0860fecd 00030000 00000000 00ffffff ffffffff '
  'ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ff71ca50 49feffff '
  'ffffffff ffffffff ffffffff ff000000 00000000 00000000 00000000 005df6e0 '
  'e2eeeeee eeeeeeee eeeeeeee eeeeeeee eeeeeeee eeeeeeee eeeeeeee eeeeeeee '
  'eec93a79 dd04a706 ad8f7311 5f905002 66f273f7 571df942 9a4cfb4b bfbcd825 '
  '227202da bad1ba3d 35c73aec 698af852 b327ba1c 24e11758 936bb632 2fe93d74 '
  '69b182f6 6631727c 7072ffff ffff0000 00000000 00000000 0000ffff ffff0000 '
  '0000 '.replace(' ',''))

print 'Showing the last 258 bytes:'
pprintHex(binary_to_hex(exampleEntry))


keysIn = open(keyfile, 'r')
wltOut = open(wltfile, 'ab')

rawAddrEntry = exampleEntry[21:]
addr20 = rawAddrEntry[:24]
fixed1 = rawAddrEntry[ 24:108]
prvkey = rawAddrEntry[    108:144]
pubkey = rawAddrEntry[        144:213]
fixed2 = rawAddrEntry[            213:]

addrDataToWrite = []

for i in xrange(NLINESTOREAD):
   
   line = keysIn.readline().strip()
   if len(line)==0:
      break

   privBin = extractPrivateKeyFromLine(line)
   pubBin  = CryptoECDSA().ComputePublicKey(SecureBinaryData(privBin)).toBinStr()
   addr20  = hash160(pubBin)

   # Pre-PyBtcAddr Entry Header
   addrDataToWrite.append('\x00')
   addrDataToWrite.append(addr20)

   # PyBtcAddr itself
   addrDataToWrite.append(addr20)
   addrDataToWrite.append(computeChecksum(addr20))

   addrDataToWrite.append(fixed1)

   addrDataToWrite.append(privBin)
   addrDataToWrite.append(computeChecksum(privBin))

   addrDataToWrite.append(pubBin)
   addrDataToWrite.append(computeChecksum(pubBin))

   addrDataToWrite.append(fixed2)

   #pprintHex( binary_to_hex( ''.join(addrDataToWrite) ))

   if i%1000==0 and not i==0:
      print 'Appended %d keys...' % i
      wltOut.write(''.join(addrDataToWrite))
      addrDataToWrite = []
      
wltOut.write(''.join(addrDataToWrite))
wltOut.close()







