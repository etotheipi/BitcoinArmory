# -*- Mode: Python -*-
#       Author: Sam Rushing <rushing@nightmare.com>

# stealing from myself.  taken from amk's medusa-0.5.4 distribution,
# then hacked about ten years into the future, buncha stuff ripped
# out.
#
# mostly useful for debugging, should not be distributed with the final client!
#

#
# python REPL channel.
#

import socket
import string
import sys
import time

import asyncore
import asynchat

class monitor_channel (asynchat.async_chat):
    try_linemode = 1

    def __init__ (self, server, sock, addr):
        asynchat.async_chat.__init__ (self, sock)
        self.server = server
        self.addr = addr
        self.set_terminator ('\r\n')
        self.data = ''
        # local bindings specific to this channel
        self.local_env = sys.modules['__main__'].__dict__.copy()
        self.push ('Python ' + sys.version + '\r\n')
        self.push (sys.copyright+'\r\n')
        self.push ('Welcome to the Monitor.  You are %r\r\n' % (self.addr,))
        self.prompt()
        self.number = server.total_sessions
        self.line_counter = 0
        self.multi_line = []

    def handle_connect (self):
        # send IAC DO LINEMODE
        self.push ('\377\375\"')

    def close (self):
        self.server.closed_sessions += 1
        asynchat.async_chat.close(self)

    def prompt (self):
        self.push ('>>> ')

    def collect_incoming_data (self, data):
        self.data = self.data + data
        if len(self.data) > 1024:
            # denial of service.
            self.push ('BCNU\r\n')
            self.close_when_done()

    def found_terminator (self):
        line = self.clean_line (self.data)
        self.data = ''
        self.line_counter += 1
        # check for special case inputs...
        if not line and not self.multi_line:
            self.prompt()
            return
        if line in ['\004', 'exit']:
            self.push ('BCNU\r\n')
            self.close_when_done()
            return
        oldout = sys.stdout
        olderr = sys.stderr
        try:
            p = output_producer(self, olderr)
            sys.stdout = p
            sys.stderr = p
            try:
                # this is, of course, a blocking operation.
                # if you wanted to thread this, you would have
                # to synchronize, etc... and treat the output
                # like a pipe.  Not Fun.
                #
                # try eval first.  If that fails, try exec.  If that fails,
                # hurl.
                try:
                    if self.multi_line:
                        # oh, this is horrible...
                        raise SyntaxError
                    co = compile (line, repr(self), 'eval')
                    result = eval (co, self.local_env)
                    method = 'eval'
                    if result is not None:
                        print repr(result)
                    self.local_env['_'] = result
                except SyntaxError:
                    try:
                        if self.multi_line:
                            if line and line[0] in [' ','\t']:
                                self.multi_line.append (line)
                                self.push ('... ')
                                return
                            else:
                                self.multi_line.append (line)
                                line =  string.join (self.multi_line, '\n')
                                co = compile (line, repr(self), 'exec')
                                self.multi_line = []
                        else:
                            co = compile (line, repr(self), 'exec')
                    except SyntaxError, why:
                        if why[0] == 'unexpected EOF while parsing':
                            self.push ('... ')
                            self.multi_line.append (line)
                            return
                        else:
                            t,v,tb = sys.exc_info()
                            del tb
                            raise t,v
                    exec co in self.local_env
                    method = 'exec'
            except:
                method = 'exception'
                self.multi_line = []
                (file, fun, line), t, v, tbinfo = asyncore.compact_traceback()
                self.log_info('%s %s %s' %(t, v, tbinfo), 'warning')
        finally:
            sys.stdout = oldout
            sys.stderr = olderr
        self.push_with_producer (p)
        self.prompt()

    # for now, we ignore any telnet option stuff sent to
    # us, and we process the backspace key ourselves.
    # gee, it would be fun to write a full-blown line-editing
    # environment, etc...
    def clean_line (self, line):
        chars = []
        for ch in line:
            oc = ord(ch)
            if oc < 127:
                if oc in [8,177]:
                    # backspace
                    chars = chars[:-1]
                else:
                    chars.append (ch)
        return string.join (chars, '')

class monitor_server (asyncore.dispatcher):

    SERVER_IDENT = 'Bitcoin Monitor Server'

    channel_class = monitor_channel

    def __init__ (self, hostname='127.0.0.1', port=8023):
        asyncore.dispatcher.__init__ (self, socket.socket (socket.AF_INET, socket.SOCK_STREAM))
        self.hostname = hostname
        self.port = port
        self.set_reuse_addr()
        self.bind ((hostname, port))
        self.log_info('%s started on port %d' % (self.SERVER_IDENT, port))
        self.listen (5)
        self.closed             = 0
        self.failed_auths = 0
        self.total_sessions = 0
        self.closed_sessions = 0

    def writable (self):
        return 0

    def handle_accept (self):
        conn, addr = self.accept()
        self.log_info ('Incoming monitor connection from %s:%d' % addr)
        self.channel_class (self, conn, addr)
        self.total_sessions += 1

# don't try to print from within any of the methods
# of this object. 8^)

class output_producer:
    def __init__ (self, channel, real_stderr):
        self.channel = channel
        self.data = ''
        # use _this_ for debug output
        self.stderr = real_stderr

    def check_data (self):
        if len(self.data) > 1<<16:
            # runaway output, close it.
            self.channel.close()

    def write (self, data):
        lines = string.splitfields (data, '\n')
        data = string.join (lines, '\r\n')
        self.data = self.data + data
        self.check_data()

    def writeline (self, line):
        self.data = self.data + line + '\r\n'
        self.check_data()

    def writelines (self, lines):
        self.data = self.data + string.joinfields (
                lines,
                '\r\n'
                ) + '\r\n'
        self.check_data()

    def flush (self):
        pass

    def softspace (self, *args):
        pass

    def more (self):
        if self.data:
            result = self.data[:512]
            self.data = self.data[512:]
            return result
        else:
            return ''
