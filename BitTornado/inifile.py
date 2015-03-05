# Written by John Hoffman
# see LICENSE.txt for license information

'''
reads/writes a Windows-style INI file
format:

  aa = "bb"
  cc = 11

  [eee]
  ff = "gg"

decodes to:
d = { '': {'aa':'bb','cc':'11'}, 'eee': {'ff':'gg'} }

the encoder can also take this as input:

d = { 'aa': 'bb, 'cc': 11, 'eee': {'ff':'gg'} }

though it will only decode in the above format.  Keywords must be strings.
Values that are strings are written surrounded by quotes, and the decoding
routine automatically strips any.
Booleans are written as integers.  Anything else aside from string/int/float
may have unpredictable results.
'''

from io import StringIO
from traceback import print_exc


DEBUG = False

def ini_write(f, d, comment=''):
    try:
        a = {'':{}}
        for k,v in list(d.items()):
            assert(type(k) == str)
            k = k.lower()
            if type(v) == dict:
                if DEBUG:
                    print('new section:' +k)
                if k:
                    assert k not in a
                    a[k] = {}
                aa = a[k]
                for kk,vv in v:
                    assert type(kk) == str
                    kk = kk.lower()
                    assert kk not in aa
                    if type(vv) == bool:
                        vv = int(vv)
                    if type(vv) == str:
                        vv = '"'+vv+'"'
                    aa[kk] = str(vv)
                    if DEBUG:
                        print('a['+k+']['+kk+'] = '+str(vv))
            else:
                aa = a['']
                assert k not in aa
                if type(v) == bool:
                    v = int(v)
                if type(v) == str:
                    v = '"'+v+'"'
                aa[k] = str(v)
                if DEBUG:
                    print('a[\'\']['+k+'] = '+str(v))
        r = open(f,'w')
        if comment:
            for c in comment.split('\n'):
                r.write('# '+c+'\n')
            r.write('\n')
        l = list(a.keys())
        l.sort()
        for k in l:
            if k:
                r.write('\n['+k+']\n')
            aa = a[k]
            ll = list(aa.keys())
            ll.sort()
            for kk in ll:
                r.write(kk+' = '+aa[kk]+'\n')
        success = True
    except:
        if DEBUG:
            print_exc()
        success = False
    try:
        r.close()
    except:
        pass
    return success


if DEBUG:
    def errfunc(lineno, line, err):
        print('('+str(lineno)+') '+err+': '+line)
else:
    errfunc = lambda lineno, line, err: None

def ini_read(f, errfunc = errfunc):
    try:
        r = open(f,'r')
        ll = r.readlines()
        d = {}
        dd = {'':d}
        for i in range(len(ll)):
            l = ll[i]
            l = l.strip()
            if not l:
                continue
            if l[0] == '#':
                continue
            if l[0] == '[':
                if l[-1] != ']':
                    errfunc(i,l,'syntax error')
                    continue
                l1 = l[1:-1].strip().lower()
                if not l1:
                    errfunc(i,l,'syntax error')
                    continue
                if l1 in dd:
                    errfunc(i,l,'duplicate section')
                    d = dd[l1]
                    continue
                d = {}
                dd[l1] = d
                continue
            try:
                k,v = l.split('=',1)
            except:
                try:
                    k,v = l.split(':',1)
                except:
                    errfunc(i,l,'syntax error')
                    continue
            k = k.strip().lower()
            v = v.strip()
            if len(v) > 1 and ( (v[0] == '"' and v[-1] == '"') or
                                (v[0] == "'" and v[-1] == "'") ):
                v = v[1:-1]
            if not k:
                errfunc(i,l,'syntax error')
                continue
            if k in d:
                errfunc(i,l,'duplicate entry')
                continue
            d[k] = v
        if DEBUG:
            print(dd)
    except:
        if DEBUG:
            print_exc()
        dd = None
    try:
        r.close()
    except:
        pass
    return dd
