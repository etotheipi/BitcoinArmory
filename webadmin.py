# -*- Mode: Python -*-

import re
import sys
import zlib

from urllib import splitquery
from urlparse import parse_qs
from cgi import escape

favicon = zlib.decompress (
    '789ca552594f1351141ee3a32fc607e3a32f2e3fc168a2a6893e49e242884113d4288ab6a10bc2a8a5553add66693b5da69db6d399cedaa1a57491ae208b5096'
    '8284e08a11a998b8fc0542e255e32ff0bb39f7e1dc9c73bef37d1782f680b37f3f04ee43d0bdbd10741082a0e320400a3a0cfdcdff01783bb0ef6ffc032b24f2'
    'cf732f666a85728e93b908135686e5cdad4fd3b353f34bf3569bd58139a461a13a5e298ce57839e10ffbc4949094192a1ee8edefbdafefa9d4cbabebaf42b180'
    '1d4734e7356734676f76df8873315e665d0422aa9c9c16245534c1a653a74fe9fbf4f34b8d483cecf6b8eeeaee52516a6e61968ed398174d8fa6224c40c9084e'
    '1cb970b14d734e637c68bad3733bca451e3eee9b7e394d86c8d676cb1f26fbcdfd18898e16b3628a4f8d0857af771c3976f462fb2525ad5886cc4ec2363337b5'
    'bbbbcbf28942295fa957e0c10117ee4cca1c58969598f6ab97794940dc481f6c8ab3513b3654ae95b6bf6e670b2304896d7cfc403311abcd627a6424299fc536'
    'd876a90df560f589da958e2b3a83ce4f91a22a2ead2c6db53e4fcd4eb162c213209c9823955610b7cdd067d0eab59d5d9de56ab9587a7efdc63517ee4808cce2'
    'f2c2c6c70db0efadee5bc6017db152ac4f5443d1206c19b0a388d9f64467d2365f354374f0e4e9133aa35654f9101dd01a1e08b2e0f113f9b15c3c191594a409'
    '36989f9a079f998db01127f14f9f37f3853cfc0446bd6e92f2d6c66b1881755c6b373f838192f1640478045be06038e4f57b810ea54ae9dbf76fa010483a92cb'
    'acbd5e6b2c34ec2e0450e224c61ff62018d2d3db435224701054e1243633f7b2f5a5e5225c8fadb09a517363a3e158880cfa80b3e230c708310b023477701247'
    '33b42fe4f50489f537eb3f7efe9054c9812256bb050fa092caa73272b690f9cd8a8ff828af288bc572a13a511d2d64814d8df9c6cececee6d626ea71dfeceec2'
    '7c4e51152ab50aea750aa924f83f7482020cc727eb933393c5725150442925adaeadbe7dffaeb9d224489c13d9c5e5c5a760a07b28c1c77999e3a45894a5d3d9'
    'b4ac4a4a46612516f449cac9e5d56663b1210fcba01bf49ff8057db2cf3a'.decode ('hex_codec')
    )

from __main__ import *

class handler:

    def __init__ (self):
        self.pending_send = []

    def match (self, request):
        path, params, query, fragment = request.split_uri()
        if path == '/favicon.ico':
            return True
        else:
            return path.startswith ('/admin/')

    safe_cmd = re.compile ('[a-z]+')

    def handle_request (self, request):
        path, params, query, fragment = request.split_uri()
        if path == '/favicon.ico':
            request['Content-Type'] = 'image/x-icon'
            request.push (favicon)
            request.done()
        else:
            parts = path.split ('/')[2:] # ignore ['', 'admin']
            subcmd = parts[0]
            if not subcmd:
                subcmd = 'status'
            method_name = 'cmd_%s' % (subcmd,)
            if self.safe_cmd.match (subcmd) and hasattr (self, method_name):
                method = getattr (self, method_name)
                request.push (
                    '\r\n'.join ([
                            '<html><head></head>'
                            '<body>'
                            '<h1>caesure admin</h1>',
                            ])
                    )
                self.menu (request)
                try:
                    method (request, parts)
                except:
                    request.push ('<h1>something went wrong</h1>')
                    request.push ('<pre>%r</pre>' % (asyncore.compact_traceback(),))
                request.push ('<hr>')
                self.menu (request)
                request.push ('</body></html>')
                request.done()
            else:
                request.error (400)

    def menu (self, request):
        request.push (
            '&nbsp;&nbsp;<a href="/admin/reload">reload</a>'
            '&nbsp;&nbsp;<a href="/admin/status">status</a>'
            '&nbsp;&nbsp;<a href="/admin/block/">blocks</a>'
            '&nbsp;&nbsp;<a href="/admin/wallet/">wallet</a>'
            '&nbsp;&nbsp;<a href="/admin/send/">send</a>'
            )

    def cmd_status (self, request, parts):
        db = the_block_db
        w = the_wallet
        RP = request.push
        RP ('<h3>last block</h3>')
        RP ('hash: %s' % (db.last_block,))
        RP ('<br>num: %d' % (db.block_num[db.last_block],))
        RP ('<h3>connection</h3>')
        RP (escape (repr (bc)))
        RP ('<br>here: %s' % (bc.getsockname(),))
        RP ('<br>there: %s' % (bc.getpeername(),))
        RP ('<h3>wallet</h3>')
        if w is None:
            RP ('No Wallet')
        else:
            RP ('total btc: %s' % (bcrepr (w.total_btc),))

    def cmd_block (self, request, parts):
        db = the_block_db
        RP = request.push
        if len(parts) == 2 and len(parts[1]):
            num = int (parts[1])
        else:
            num = 0
        if db.num_block.has_key (num):
            b = db[db.num_block[num]]
            last_num = db.block_num[db.last_block]
            RP ('<br>&nbsp;&nbsp;<a href="/admin/block/0">First Block</a>')
            RP ('&nbsp;&nbsp;<a href="/admin/block/%d">Last Block</a><br>' % last_num,)
            if num > 0:
                RP ('&nbsp;&nbsp;<a href="/admin/block/%d">Prev Block</a>' % (num-1,))
            if num < db.block_num[db.last_block]:
                RP ('&nbsp;&nbsp;<a href="/admin/block/%d">Next Block</a><br>' % (num+1,))
            RP ('\r\n'.join ([
                        '<br>prev_block: %s' % (hexify (b.prev_block),),
                        '<br>merkle_root: %s' % (hexify (b.merkle_root),),
                        '<br>timestamp: %s' % (b.timestamp,),
                        '<br>bits: %s' % (b.bits,),
                        '<br>nonce: %s' % (b.nonce,),
                        ]))
            RP ('<pre>%d transactions\r\n' % len(b.transactions))
            for tx in b.transactions:
                self.dump_tx (request, tx)
            RP ('</pre>')

    def dump_tx (self, request, tx):
        RP = request.push
        RP ('tx: %s\r\n' % (hexify (dhash (tx.render()))))
        RP ('inputs: %d\r\n' % (len(tx.inputs)))
        for i in range (len (tx.inputs)):
            (outpoint, index), script, sequence = tx.inputs[i]
            RP ('%3d %s:%d %s %d\r\n' % (i, hexify(outpoint), index, hexify (script), sequence))
        RP ('%d outputs\n' % (len(tx.outputs)))
        for i in range (len (tx.outputs)):
            value, pk_script = tx.outputs[i]
            addr = parse_oscript (pk_script)
            if not addr:
                addr = hexify (pk_script)
            RP ('%3d %s %s\n' % (i, bcrepr (value), addr))
        RP ('lock_time: %s\n' % tx.lock_time)

    def cmd_reload (self, request, parts):
        new_hand = reload (sys.modules['webadmin'])
        hl = sys.modules['__main__'].h.handlers
        for i in range (len (hl)):
            if hl[i] is self:
                del hl[i]
                h0 = new_hand.handler()
                # copy over any pending send txs
                h0.pending_send = self.pending_send
                hl.append (h0)
                break
        request.push ('<h3>[reloaded]</h3>')
        self.cmd_status (request, parts)

    def cmd_wallet (self, request, parts):
        RP = request.push
        w = the_wallet
        if not w:
            RP ('<h3>no wallet</h3>')
        else:
            if parts == ['wallet', 'newkey']:
                nk = w.new_key()
                RP ('<p>New Key: %s</p>' % (nk,))
            else:
                addrs = w.value.keys()
                addrs.sort()
                sum = 0
                RP ('<p>%d addrs total</p>' % (len(addrs),))
                for addr in addrs:
                    RP ('<dl>')
                    if len(w.value[addr]):
                        RP ('<dt>addr: %s</dt>' % (addr,))
                        for (outpoint, index), value in w.value[addr].iteritems():
                            RP ('<dd>%s %s:%d</dd>' % (bcrepr (value), outpoint.encode ('hex_codec'), index))
                            sum += value
                    RP ('</dl>')
                RP ('<br>total: %s' % (bcrepr(sum),))
                RP ('<br>unused keys:')
                for addr in addrs:
                    if not len(w.value[addr]):
                        RP ('<br>%s' % (addr,))
                RP ('<p><a href="/admin/wallet/newkey">Make a New Key</a></p>')

    def match_form (self, qparts, names):
        if len(qparts) != len(names):
            return False
        else:
            for name in names:
                if not qparts.has_key (name):
                    return False
        return True

    def cmd_send (self, request, parts):
        path, params, query, fragment = request.split_uri()
        RP = request.push
        w = the_wallet
        print path, params, query, fragment
        if query:
            qparts = parse_qs (query[1:])
            print qparts
            if self.match_form (qparts, ['amount', 'addr', 'fee']):
                btc = float_to_btc (float (qparts['amount'][0]))
                fee = float_to_btc (float (qparts['fee'][0]))
                addr = qparts['addr'][0]
                _ = address_to_key (addr) # verify it's a real address
                tx = w.build_send_request (btc, addr, fee)
                RP ('<br>send tx:<br><pre>')
                self.dump_tx (request, tx)
                self.pending_send.append (tx)
                RP ('</pre>')
            elif self.match_form (qparts, ['cancel', 'index']):
                index = int (qparts['index'][0])
                del self.pending_send[index]
                RP ('<h3>deleted tx #%d</h3>' % (index,))
            elif self.match_form (qparts, ['confirm', 'index']):
                index = int (qparts['index'][0])
                tx = self.pending_send[index]
                RP ('<h3>sent tx #%d</h3>' % (index,))
                # send it
                bc.push (make_packet ('tx', tx.render()))
                # forget about it
                del self.pending_send[index]
            else:
                RP ('???')
        RP ('<form>'
            'Amount to Send: <input type="text" name="amount" /><br/>'
            'To Address: <input type="text" name="addr" /><br/>'
            'Fee: <input type="text" name="fee" value="0.0005"><br/>'
            '<input type="submit" value="Send"/></form>'
            )
        if not self.pending_send:
            RP ('<h3>no pending send requests</h3>')
        else:
            RP ('<h3>pending send requests</h3>')
            for i in range (len (self.pending_send)):
                RP ('<hr>#%d: <br>' % (i,))
                RP ('<pre>')
                self.dump_tx (request, self.pending_send[i])
                RP ('</pre>')
                RP ('<form><input type="hidden" name="index" value="%d">'
                    '<input type="submit" name="confirm" value="confirm"/>'
                    '<input type="submit" name="cancel" value="cancel"/>'
                    '</form>' % (i,))
