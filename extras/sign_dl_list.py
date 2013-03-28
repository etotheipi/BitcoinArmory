import sys
sys.path.append('..')
sys.path.append('/usr/share/armory')

import getpass
import os
from armoryengine import *
# Use the parseDownloadList from verify script
from verify_dl_list import *



wltfile = open(os.path.join(ARMORY_HOME_DIR, 'signingwlt.txt'),'r')
wltname = wltfile.readlines()[0].strip()
wltpath = os.path.join(ARMORY_HOME_DIR, wltname)
if not os.path.exists(wltpath):
   print 'No wallet!'
wlt = PyBtcWallet().readWalletFile(wltpath)
LOGINFO('Wallet to use: %s', wltpath)

passwd = SecureBinaryData(getpass.getpass('Unlock wallet %s: ' % wltname))
while not wlt.verifyPassphrase(passwd):
   LOGWARN('Passphrase incorrect')
   passwd = SecureBinaryData(getpass.getpass('Unlock wallet %s: ' % wltname))

wlt.unlock(securePassphrase=passwd)
LOGINFO('Wallet unlocked')

Priv = SecureBinaryData('')
for a160,addr in wlt.addrMap.iteritems():
   if addr.chainIndex==1:
      Priv = addr.binPrivKey32_Plain.copy()


if Priv.getSize()==0:
   LOGERROR('Private key not found!')
   exit(1)

Pub = SecureBinaryData(hex_to_binary(ARMORY_INFO_SIGN_PUBLICKEY))
print 'Keys match? ', CryptoECDSA().CheckPubPrivKeyMatch(Priv, Pub)


fn = 'versions.txt'
if not os.path.exists(fn):
   LOGERROR( 'File does not exist!  %s', fn)
   fn = '../versions.txt'
   if not os.path.exists(fn):
      LOGERROR('Really does not exist. Aborting. %s', fn)
      exit(1)


sigData = open(fn, 'r').read()
msgToSign = extractSignedDataFromVersionsDotTxt(sigData, doVerify=False)
Msg = SecureBinaryData(msgToSign)

result = CryptoECDSA().SignData(Msg, Priv)
print 'Signature:', result.toHexStr()

