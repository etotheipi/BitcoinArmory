# Written by Bram Cohen
# see LICENSE.txt for license information

from re import compile

reg = compile(r'^[^/\\.~][^/\\]*$')

def check_info(info):
    if type(info) != dict:
        raise ValueError("bad metainfo - not a dictionary")
    pieces = info.get('pieces')
    if type(pieces) != str or len(pieces) % 20 != 0:
        raise ValueError("bad metainfo - bad pieces key")
    piecelength = info.get('piece length')
    if type(piecelength) != int or piecelength <= 0:
        raise ValueError("bad metainfo - illegal piece length")
    name = info.get('name')
    if type(name) != str:
        raise ValueError("bad metainfo - bad name")
    if not reg.match(name):
        raise ValueError("name %s disallowed for security reasons") % name
    if ('files' in info) == ('length' in info):
        raise ValueError("single/multiple file mix")
    if 'length' in info:
        length = info.get('length')
        if type(length) not in ints or length < 0:
            raise ValueError("bad metainfo - bad length")
    else:
        files = info.get('files')
        if type(files) != list:
            raise ValueError("")
        for f in files:
            if type(f) != dict:
                raise ValueError("bad metainfo - bad file value")
            length = f.get('length')
            if type(length) != int or length < 0:
                raise ValueError("bad metainfo - bad length")
            path = f.get('path')
            if type(path) != list or path == []:
                raise ValueError("bad metainfo - bad path")
            for p in path:
                if type(p) != str:
                    raise ValueError("bad metainfo - bad path dir")
                if not reg.match(p):
                    raise ValueError("path %s disallowed for security reasons") % p
        for i in range(len(files)):
            for j in range(i):
                if files[i]['path'] == files[j]['path']:
                    raise ValueError("bad metainfo - duplicate path")

def check_message(message):
    if type(message) != dict:
        raise ValueError("")
    check_info(message.get('info'))
    if type(message.get('announce')) != str:
        raise ValueError("")

def check_peers(message):
    if type(message) != dict:
        raise ValueError("")
    if 'failure reason' in message:
        if type(message['failure reason']) != str:
            raise ValueError("")
        return
    peers = message.get('peers')
    if type(peers) == list:
        for p in peers:
            if type(p) != dict:
                raise ValueError("")
            if type(p.get('ip')) != str:
                raise ValueError("")
            port = p.get('port')
            if type(port) not in ints or p <= 0:
                raise ValueError("")
            if 'peer id' in p:
                id = p['peer id']
                if type(id) != str or len(id) != 20:
                    raise ValueError("")
    elif type(peers) != str or len(peers) % 6 != 0:
        raise ValueError("")
    interval = message.get('interval', 1)
    if type(interval) not in ints or interval <= 0:
        raise ValueError("")
    minint = message.get('min interval', 1)
    if type(minint) not in ints or minint <= 0:
        raise ValueError("")
    if type(message.get('tracker id', '')) != str:
        raise ValueError("")
    npeers = message.get('num peers', 0)
    if type(npeers) not in ints or npeers < 0:
        raise ValueError("")
    dpeers = message.get('done peers', 0)
    if type(dpeers) not in ints or dpeers < 0:
        raise ValueError("")
    last = message.get('last', 0)
    if type(last) not in ints or last < 0:
        raise ValueError("")
