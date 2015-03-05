product_name = 'BitTornado'
version_short = 'T-0.3.17'

version = version_short+' ('+product_name+')'
report_email = version_short+'@degreez.net'

import hashlib 
from time import time, clock
from os import getpid

mapbase64 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.-'

_idprefix = version_short[0]
for subver in version_short[2:].split('.'):
    try:
        subver = int(subver)
    except:
        subver = 0
    _idprefix += mapbase64[subver]
_idprefix += ('-' * (6-len(_idprefix)))
_idrandom = [None]

def resetPeerIDs():
    try:
        f = open('/dev/urandom','rb')
        x = f.read(20).decode("ascii")
        f.close()
    except:
        x = ''

    l1 = 0
    t = clock()
    while t == clock():
        l1 += 1
    l2 = 0
    t = int(time()*100)
    while t == int(time()*100):
        l2 += 1
    l3 = 0
    if l2 < 1000:
        t = int(time()*10)
        while t == int(clock()*10):
            l3 += 1
    z = "%s/%s/%s/%s/%s/%s" % ( time(), time(), l1, l2 , l3, getpid())
    x += z

    s = ''
    for i in hashlib.sha1(x.encode("ascii")).digest()[-11:]:
        s += mapbase64[i & 0x3F]
    _idrandom[0] = s
        
resetPeerIDs()

def createPeerID(ins = '---'):
    assert isinstance(ins, str)
    assert len(ins) == 3
    return _idprefix + ins + _idrandom[0]
