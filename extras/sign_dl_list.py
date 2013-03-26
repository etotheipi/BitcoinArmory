import sys
sys.path.append('..')

import getpass
import os
from armoryengine import *
from verify_dl_list import *


PRIV32 = getpass.getpass('Copy the private key here: ').replace(' ','')
if not len(PRIV32)==64:
   print 'ERROR: Private key is not valid'
   exit(1)

Priv = SecureBinaryData(hex_to_binary(PRIV32))
Pub = SecureBinaryData(hex_to_binary(ARMORY_INFO_SIGN_PUBLICKEY))

print 'Keys match? ', CryptoECDSA().CheckPubPrivKeyMatch(Priv, Pub)


fn = 'versions.txt'
if not os.path.exists(fn):
   print 'File does not exist!'

f = open(fn, 'r')
allVerStr = f.read()
DICT,STR,SIG = parseDownloadList(allVerStr)
Msg = SecureBinaryData(STR)

result = CryptoECDSA().SignData(Msg, Priv)

print 'Signature:', result.toHexStr()

