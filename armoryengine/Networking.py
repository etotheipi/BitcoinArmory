################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
################################################################################
#
# Armory Networking:
# 
#    This is where I will define all the network operations needed for 
#    Armory to operate, using python-twisted.  There are "better"
#    ways to do this with "reusable" code structures (i.e. using huge
#    deferred callback chains), but this is not the central "creative" 
#    part of the Bitcoin protocol.  I need just enough to broadcast tx
#    and receive new tx that aren't in the blockchain yet.  Beyond that,
#    I'll just be ignoring everything else.
#
################################################################################

import os.path
import random

from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

from armoryengine.ArmoryUtils import LOGINFO, RightNow, getVersionString, \
   BTCARMORY_VERSION, NetworkIDError, LOGERROR, BLOCKCHAINS, CLI_OPTIONS, LOGDEBUG, \
   binary_to_hex, BIGENDIAN, LOGRAWDATA, ARMORY_HOME_DIR, ConnectionError, \
   MAGIC_BYTES, hash256, verifyChecksum, NETWORKENDIAN, int_to_bitset, \
   bitset_to_int, unixTimeToFormatStr
from armoryengine.BDM import TheBDM
from armoryengine.BinaryPacker import BinaryPacker, BINARY_CHUNK, UINT32, UINT64, \
   UINT16, VAR_INT, INT32, INT64, VAR_STR, INT8
from armoryengine.BinaryUnpacker import BinaryUnpacker, UnpackerError
from armoryengine.Block import PyBlockHeader
from armoryengine.Transaction import PyTx, indent


class ArmoryClient(Protocol):
   """
   This is where all the Bitcoin-specific networking stuff goes.
   In the Twisted way, you need to inject your own chains of 
   callbacks through the factory in order to get this class to do
   the right thing on the various events.
   """

   ############################################################
   def __init__(self):
      self.recvData = ''
      self.gotVerack = False
      self.sentVerack = False
      self.sentHeadersReq = True
      self.peer = []

   ############################################################
   def connectionMade(self):
      """
      Construct the initial version message and send it right away.
      Everything else will be handled by dataReceived.
      """
      LOGINFO('Connection initiated.  Start handshake')
      addrTo   = str_to_quad(self.transport.getPeer().host)
      portTo   =             self.transport.getPeer().port
      addrFrom = str_to_quad(self.transport.getHost().host)
      portFrom =             self.transport.getHost().port

      self.peer = [addrTo, portTo]

      services = '0'*16
      msgVersion = PayloadVersion()
      msgVersion.version  = 40000   # TODO: this is what my Satoshi client says
      msgVersion.services = services
      msgVersion.time     = long(RightNow())
      msgVersion.addrRecv = PyNetAddress(0, services, addrTo,   portTo  )
      msgVersion.addrFrom = PyNetAddress(0, services, addrFrom, portFrom)
      msgVersion.nonce    = random.randint(2**60, 2**64-1)
      msgVersion.subver   = 'Armory:%s' % getVersionString(BTCARMORY_VERSION)
      msgVersion.height0  = -1
      self.sendMessage( msgVersion )
      self.factory.func_madeConnect()

      
   ############################################################
   def dataReceived(self, data):
      """
      Called by the reactor when data is received over the connection. 
      This method will do nothing if we don't receive a full message.
      """

      
      #print '\n\nData Received:',
      #pprintHex(binary_to_hex(data), withAddr=False)

      # Put the current buffer into an unpacker, process until empty
      self.recvData += data
      buf = BinaryUnpacker(self.recvData)

      messages = []
      while True:
         try:
            # recvData is only modified if the unserialize succeeds
            # Had a serious issue with references, so I had to convert 
            # messages to strings to guarantee that copies were being 
            # made!  (yes, hacky...)
            thisMsg = PyMessage().unserialize(buf)
            messages.append( thisMsg.serialize() )
            self.recvData = buf.getRemainingString()
         except NetworkIDError:
            LOGERROR('Message for a different network!' )
            if BLOCKCHAINS.has_key(self.recvData[:4]):
               LOGERROR( '(for network: %s)', BLOCKCHAINS[self.recvData[:4]])
            # Before raising the error, we should've finished reading the msg
            # So pop it off the front of the buffer
            self.recvData = buf.getRemainingString()
            return
         except UnpackerError:
            # Expect this error when buffer isn't full enough for a whole msg
            break

      # We might've gotten here without anything to process -- if so, bail
      if len(messages)==0:
         return


      # Finally, we have some message to process, let's do it
      for msgStr in messages:
         msg = PyMessage().unserialize(msgStr)
         cmd = msg.cmd

         # Log the message if netlog option
         if CLI_OPTIONS.netlog:
            LOGDEBUG( 'DataReceived: %s', msg.payload.command)
            if msg.payload.command == 'tx':
               LOGDEBUG('\t' + binary_to_hex(msg.payload.tx.thisHash))
            elif msg.payload.command == 'block':
               LOGDEBUG('\t' + msg.payload.header.getHashHex())
            elif msg.payload.command == 'inv':
               for inv in msg.payload.invList:
                  LOGDEBUG(('\tBLOCK: ' if inv[0]==2 else '\tTX   : ') + \
                                                      binary_to_hex(inv[1]))


         # We process version and verackk only if we haven't yet
         if cmd=='version' and not self.sentVerack:
            self.peerInfo = {}
            self.peerInfo['version'] = msg.payload.version
            self.peerInfo['subver']  = msg.payload.subver
            self.peerInfo['time']    = msg.payload.time
            self.peerInfo['height']  = msg.payload.height0
            LOGINFO('Received version message from peer:')
            LOGINFO('   Version:     %s', str(self.peerInfo['version']))
            LOGINFO('   SubVersion:  %s', str(self.peerInfo['subver']))
            LOGINFO('   TimeStamp:   %s', str(self.peerInfo['time']))
            LOGINFO('   StartHeight: %s', str(self.peerInfo['height']))
            self.sentVerack = True
            self.sendMessage( PayloadVerack() )
         elif cmd=='verack':
            self.gotVerack = True
            self.factory.handshakeFinished(self)
            #self.startHeaderDL()

         ####################################################################
         # Don't process any other messages unless the handshake is finished
         if self.gotVerack and self.sentVerack:
            self.processMessage(msg)


   ############################################################
   #def connectionLost(self, reason):
      #"""
      #Try to reopen connection (not impl yet)
      #"""
      #self.factory.connectionFailed(self, reason)


   ############################################################
   def processMessage(self, msg):
      # TODO:  when I start expanding this class to be more versatile,
      #        I'll consider chaining/setting callbacks from the calling
      #        application.  For now, it's pretty static.
      #msg.payload.pprint(nIndent=2)
      if msg.cmd=='inv':
         invobj = msg.payload
         getdataMsg = PyMessage('getdata')
         for inv in invobj.invList:
            if inv[0]==MSG_INV_BLOCK:
               if self.factory.bdm and (self.factory.bdm.getBDMState()=='Scanning' or \
                  self.factory.bdm.hasHeaderWithHash(inv[1])):
                  continue
               getdataMsg.payload.invList.append(inv)
            if inv[0]==MSG_INV_TX:
               if self.factory.bdm and (self.factory.bdm.getBDMState()=='Scanning' or \
                  self.factory.bdm.hasTxWithHash(inv[1])):
                  continue
               getdataMsg.payload.invList.append(inv)

         # Now send the full request
         if self.factory.bdm and not self.factory.bdm.getBDMState()=='Scanning':
            self.sendMessage(getdataMsg)

      if msg.cmd=='tx':
         pytx = msg.payload.tx
         self.factory.func_newTx(pytx)
      elif msg.cmd=='inv':
         invList = msg.payload.invList
         self.factory.func_inv(invList)
      elif msg.cmd=='block':
         pyHeader = msg.payload.header
         pyTxList = msg.payload.txList
         LOGINFO('Received new block.  %s', binary_to_hex(pyHeader.getHash(), BIGENDIAN))
         self.factory.func_newBlock(pyHeader, pyTxList)

                  

   ############################################################
   def startHeaderDL(self):
      numList = self.createBlockLocatorNumList(self.topBlk)
      msg = PyMessage('getheaders')
      msg.payload.version  = 1
      if self.factory.bdm:
         msg.payload.hashList = [self.factory.bdm.getHeaderByHeight(i).getHash() for i in numList]
      else:
         msg.payload.hashList = []
      msg.payload.hashStop = '\x00'*32
   
      self.sentHeadersReq = True


      
   ############################################################
   def startBlockDL(self):
      numList = self.createBlockLocatorNumList(self.topBlk)
      msg = PyMessage('getblocks')
      msg.payload.version  = 1
      if self.factory.bdm:
         msg.payload.hashList = [self.factory.bdm.getHeaderByHeight(i).getHash() for i in numList]
      else:
         msg.payload.hashList = []
      msg.payload.hashStop = '\x00'*32


   ############################################################
   def sendMessage(self, msg):
      """
      Must pass in a PyMessage, or one of the Payload<X> types, which
      will be converted to a PyMessage -- and then sent to the peer.
      If you have a fully-serialized message (with header) already,
      easy enough to user PyMessage().unserialize(binMsg)
      """
         
      if isinstance(msg, PyMessage):
         #print '\n\nSending Message:', msg.payload.command.upper()
         #pprintHex(binary_to_hex(msg.serialize()), indent='   ')
         if CLI_OPTIONS.netlog:
            LOGDEBUG( 'SendMessage: %s', msg.payload.command)
            LOGRAWDATA( msg.serialize() )
         self.transport.write(msg.serialize())
      else:
         msg = PyMessage(payload=msg)
         #print '\n\nSending Message:', msg.payload.command.upper()
         #pprintHex(binary_to_hex(msg.serialize()), indent='   ')
         if CLI_OPTIONS.netlog:
            LOGDEBUG( 'SendMessage: %s', msg.payload.command)
            LOGRAWDATA( msg.serialize() )
         self.transport.write(msg.serialize())


   ############################################################
   def sendTx(self, txObj):
      """
      This is a convenience method for the special case of sending
      a locally-constructed transaction.  Pass in either a PyTx 
      object, or a binary serialized tx.  It will be converted to
      a PyMessage and forwarded to our peer(s)
      """
      LOGINFO('sendTx called...')
      if   isinstance(txObj, PyMessage):
         self.sendMessage( txObj )
      elif isinstance(txObj, PyTx):
         self.sendMessage( PayloadTx(txObj))
      elif isinstance(txObj, str):
         self.sendMessage( PayloadTx(PyTx().unserialize(txObj)) )
         




   


################################################################################
################################################################################
class ArmoryClientFactory(ReconnectingClientFactory):
   """
   Spawns Protocol objects used for communicating over the socket.  All such
   objects (ArmoryClients) can share information through this factory.
   However, at the moment, this class is designed to only create a single 
   connection -- to localhost.
   """
   protocol = ArmoryClient
   lastAlert = 0

   #############################################################################
   def __init__(self, \
                bdm,
                def_handshake=None, \
                func_loseConnect=(lambda: None), \
                func_madeConnect=(lambda: None), \
                func_newTx=(lambda x: None), \
                func_newBlock=(lambda x,y: None), \
                func_inv=(lambda x: None)):
      """
      Initialize the ReconnectingClientFactory with a deferred for when the handshake 
      finishes:  there should be only one handshake, and thus one firing 
      of the handshake-finished callback
      """
      self.bdm = bdm
      self.lastAlert = 0
      self.deferred_handshake   = forceDeferred(def_handshake)
      self.fileMemPool = os.path.join(ARMORY_HOME_DIR, 'mempool.bin')

      # All other methods will be regular callbacks:  we plan to have a very
      # static set of behaviors for each message type
      # (NOTE:  The logic for what I need right now is so simple, that
      #         I finished implementing it in a few lines of code.  When I
      #         need to expand the versatility of this class, I'll start 
      #         doing more OOP/deferreds/etc
      self.func_loseConnect = func_loseConnect
      self.func_madeConnect = func_madeConnect
      self.func_newTx       = func_newTx
      self.func_newBlock    = func_newBlock
      self.func_inv         = func_inv
      self.proto = None

   

   #############################################################################
   def addTxToMemoryPool(self, pytx):
      if self.bdm and not self.bdm.getBDMState()=='Offline':
         self.bdm.addNewZeroConfTx(pytx.serialize(), long(RightNow()), True)    
      


   #############################################################################
   def handshakeFinished(self, protoObj):
      LOGINFO('Handshake finished, connection open!')
      self.proto = protoObj
      if self.deferred_handshake:
         d, self.deferred_handshake = self.deferred_handshake, None
         d.callback(protoObj)


   #############################################################################
   def clientConnectionLost(self, connector, reason):
      LOGERROR('***Connection to Satoshi client LOST!  Attempting to reconnect...')
      self.func_loseConnect()
      ReconnectingClientFactory.clientConnectionLost(self,connector,reason)

      
   #############################################################################
   def connectionFailed(self, protoObj, reason):
      LOGERROR('***Initial connection to Satoshi client failed!  Retrying...')
      ReconnectingClientFactory.connectionFailed(self, protoObj, reason)
      

   #############################################################################
   def sendTx(self, pytxObj):
      if self.proto:
         self.proto.sendTx(pytxObj)
      else:
         raise ConnectionError, 'Connection to localhost DNE.'


   #############################################################################
   def sendMessage(self, msgObj):
      if self.proto:
         self.proto.sendMessage(msgObj)
      else:
         raise ConnectionError, 'Connection to localhost DNE.'



###############################################################################
###############################################################################
# 
#  Networking Objects
# 
###############################################################################
###############################################################################

def quad_to_str( addrQuad):
   return '.'.join([str(a) for a in addrQuad])

def quad_to_binary( addrQuad):
   return ''.join([chr(a) for a in addrQuad])

def binary_to_quad(addrBin):
   return [ord(a) for a in addrBin]

def str_to_quad(addrBin):
   return [int(a) for a in addrBin.split('.')]

def str_to_binary(addrBin):
   """ I should come up with a better name for this -- it's net-addr only """
   return ''.join([chr(int(a)) for a in addrBin.split('.')])

def parseNetAddress(addrObj):
   if isinstance(addrObj, str):
      if len(addrObj)==4:
         return binary_to_quad(addrObj)
      else:
         return str_to_quad(addrObj)
   # Probably already in the right form
   return addrObj



MSG_INV_ERROR = 0
MSG_INV_TX    = 1
MSG_INV_BLOCK = 2


################################################################################
class PyMessage(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """
   def __init__(self, cmd='', payload=None):
      """
      Can create a message by the command name, or the payload (or neither)
      """
      self.magic   = MAGIC_BYTES
      self.cmd     = cmd
      self.payload = payload

      if payload:
         self.cmd = payload.command
      elif cmd:
         self.payload = PayloadMap[self.cmd]()



   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.magic,                    width= 4)
      bp.put(BINARY_CHUNK, self.cmd.ljust(12, '\x00'),    width=12)
      payloadBin = self.payload.serialize()
      bp.put(UINT32, len(payloadBin))
      bp.put(BINARY_CHUNK, hash256(payloadBin)[:4],     width= 4)
      bp.put(BINARY_CHUNK, payloadBin)
      return bp.getBinaryString()
    
   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         msgData = toUnpack
      else:
         msgData = BinaryUnpacker( toUnpack )


      self.magic = msgData.get(BINARY_CHUNK, 4)
      self.cmd   = msgData.get(BINARY_CHUNK, 12).strip('\x00')
      length     = msgData.get(UINT32)
      chksum     = msgData.get(BINARY_CHUNK, 4)
      payload    = msgData.get(BINARY_CHUNK, length)
      payload    = verifyChecksum(payload, chksum)

      self.payload = PayloadMap[self.cmd]().unserialize(payload)

      if self.magic != MAGIC_BYTES:
         raise NetworkIDError, 'Message has wrong network bytes!'
      return self


   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Bitcoin-Network-Message -- ' + self.cmd.upper()
      print indstr + indent + 'Magic:   ' + binary_to_hex(self.magic)
      print indstr + indent + 'Command: ' + self.cmd
      print indstr + indent + 'Payload: ' + str(len(self.payload.serialize())) + ' bytes'
      self.payload.pprint(nIndent+1)


################################################################################
class PyNetAddress(object):

   def __init__(self, time=-1, svcs='0'*16, netaddrObj=[], port=-1):
      """
      For our client we will ALWAYS use svcs=0 (NODE_NETWORK=0)

      time     is stored as a unix timestamp
      services is stored as a bitset -- a string of 16 '0's or '1's
      addrObj  is stored as a list/tuple of four UINT8s
      port     is a regular old port number...
      """
      self.time     = time
      self.services = svcs
      self.addrQuad = parseNetAddress(netaddrObj)
      self.port     = port

   def unserialize(self, toUnpack, hasTimeField=True):
      if isinstance(toUnpack, BinaryUnpacker):
         addrData = toUnpack
      else:
         addrData = BinaryUnpacker( toUnpack )

      if hasTimeField:
         self.time     = addrData.get(UINT32)

      self.services = addrData.get(UINT64)
      self.addrQuad = addrData.get(BINARY_CHUNK,16)[-4:]
      self.port     = addrData.get(UINT16, endianness=NETWORKENDIAN)

      self.services = int_to_bitset(self.services)
      self.addrQuad = binary_to_quad(self.addrQuad)
      return self

   def serialize(self, withTimeField=True):
      bp = BinaryPacker()
      if withTimeField:
         bp.put(UINT32,       self.time)
      bp.put(UINT64,       bitset_to_int(self.services))
      bp.put(BINARY_CHUNK, quad_to_binary(self.addrQuad).rjust(16,'\x00'))
      bp.put(UINT16,       self.port, endianness=NETWORKENDIAN)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Network-Address:',
      print indstr + indent + 'Time:  ' + unixTimeToFormatStr(self.time)
      print indstr + indent + 'Svcs:  ' + self.services
      print indstr + indent + 'IPv4:  ' + quad_to_str(self.addrQuad)
      print indstr + indent + 'Port:  ' + self.port

   def pprintShort(self):
      print quad_to_str(self.addrQuad) + ':' + str(self.port)

################################################################################
################################################################################
class PayloadAddr(object):

   command = 'addr'
   
   def __init__(self, addrList=[]):
      self.addrList   = addrList  # PyNetAddress objs

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         addrData = toUnpack
      else:
         addrData = BinaryUnpacker( toUnpack )

      self.addrList = []
      naddr = addrData.get(VAR_INT)
      for i in range(naddr):
         self.addrList.append( PyNetAddress().unserialize(addrData) )
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, len(self.addrList))
      for netaddr in self.addrList:
         bp.put(BINARY_CHUNK, netaddr.serialize(), width=30)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(addr):',
      for a in self.addrList:
         a.pprintShort()

   def pprintShort(self):
      for a in self.addrList:
         print '[' + quad_to_str(a.pprintShort()) + '], '

################################################################################
################################################################################
class PayloadPing(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """
   command = 'ping'

   def __init__(self):
      pass
 
   def unserialize(self, toUnpack):
      return self
 
   def serialize(self):
      return ''


   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(ping)'

      
################################################################################
################################################################################
class PayloadVersion(object):

   command = 'version'

   def __init__(self, version=0, svcs='0'*16, tstamp=-1, addrRcv=PyNetAddress(), \
                      addrFrm=PyNetAddress(), nonce=-1, sub=-1, height=-1):
      self.version  = version
      self.services = svcs
      self.time     = tstamp
      self.addrRecv = addrRcv
      self.addrFrom = addrFrm
      self.nonce    = nonce
      self.subver   = sub
      self.height0  = height

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         verData = toUnpack
      else:
         verData = BinaryUnpacker( toUnpack )

      self.version  = verData.get(INT32)
      self.services = int_to_bitset(verData.get(UINT64), widthBytes=8)
      self.time     = verData.get(INT64)
      self.addrRecv = PyNetAddress().unserialize(verData, hasTimeField=False)
      self.addrFrom = PyNetAddress().unserialize(verData, hasTimeField=False)
      self.nonce    = verData.get(UINT64)
      self.subver   = verData.get(VAR_STR)
      self.height0  = verData.get(INT32)
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(INT32,   self.version )
      bp.put(UINT64,  bitset_to_int(self.services))
      bp.put(INT64,   self.time    )  # todo, should this really be int64?
      bp.put(BINARY_CHUNK, self.addrRecv.serialize(withTimeField=False))
      bp.put(BINARY_CHUNK, self.addrFrom.serialize(withTimeField=False))
      bp.put(UINT64,  self.nonce   )
      bp.put(VAR_STR, self.subver  )
      bp.put(INT32,   self.height0 )
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(version):'
      print indstr + indent + 'Version:  ' + str(self.version)
      print indstr + indent + 'Services: ' + self.services
      print indstr + indent + 'Time:     ' + unixTimeToFormatStr(self.time)
      print indstr + indent + 'AddrTo:  ',;  self.addrRecv.pprintShort()
      print indstr + indent + 'AddrFrom:',;  self.addrFrom.pprintShort()
      print indstr + indent + 'Nonce:    ' + str(self.nonce)
      print indstr + indent + 'SubVer:  ',   self.subver
      print indstr + indent + 'StartHgt: ' + str(self.height0)

################################################################################
class PayloadVerack(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """

   command = 'verack'

   def __init__(self):
      pass

   def unserialize(self, toUnpack):
      return self

   def serialize(self):
      return ''

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(verack)'



################################################################################
################################################################################
class PayloadInv(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """

   command = 'inv'

   def __init__(self):
      self.invList = []  # list of (type, hash) pairs

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         invData = toUnpack
      else:
         invData = BinaryUnpacker( toUnpack )

      numInv = invData.get(VAR_INT)
      for i in range(numInv):
         invType = invData.get(UINT32)
         invHash = invData.get(BINARY_CHUNK, 32)
         self.invList.append( [invType, invHash] )
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, len(self.invList))
      for inv in self.invList:
         bp.put(UINT32, inv[0])
         bp.put(BINARY_CHUNK, inv[1], width=32)
      return bp.getBinaryString()
      

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(inv):'
      for inv in self.invList:
         print indstr + indent + ('BLOCK: ' if inv[0]==2 else 'TX   : ') + \
                                 binary_to_hex(inv[1])



################################################################################
################################################################################
class PayloadGetData(object):
   """
   All payload objects have a serialize and unserialize method, making them
   easy to attach to PyMessage objects
   """

   command = 'getdata'

   def __init__(self, invList=[]):
      if invList:
         self.invList = invList
      else:
         self.invList = []
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         invData = toUnpack
      else:
         invData = BinaryUnpacker( toUnpack )

      numInv = invData.get(VAR_INT)
      for i in range(numInv):
         invType = invData.get(UINT32)
         invHash = invData.get(BINARY_CHUNK, 32)
         self.invList.append( [invType, invHash] )
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, len(self.invList))
      for inv in self.invList:
         bp.put(UINT32, inv[0])
         bp.put(BINARY_CHUNK, inv[1], width=32)
      return bp.getBinaryString()
      

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getdata):'
      for inv in self.invList:
         print indstr + indent + ('BLOCK: ' if inv[0]==2 else 'TX   : ') + \
                                 binary_to_hex(inv[1])
      

################################################################################
################################################################################
class PayloadGetHeaders(object):
   command = 'getheaders'

   def __init__(self, hashStartList=[], hashStop=''):
      self.version    = 1
      self.hashList   = hashStartList
      self.hashStop   = hashStop
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         ghData = toUnpack
      else:
         ghData = BinaryUnpacker( toUnpack )

      self.version = ghData.get(UINT32)
      nhash = ghData.get(VAR_INT)
      for i in range(nhash):
         self.hashList.append(ghData.get(BINARY_CHUNK, 32))
      self.hashStop = ghData.get(BINARY_CHUNK, 32)
      return self

   def serialize(self):
      nhash = len(self.hashList)
      bp = BinaryPacker()
      bp.put(UINT32, self.version)
      bp.put(VAR_INT, nhash)
      for i in range(nhash):
         bp.put(BINARY_CHUNK, self.hashList[i], width=32)
      bp.put(BINARY_CHUNK, self.hashStop, width=32)
      return bp.getBinaryString()
   
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getheaders):'
      print indstr + indent + 'HashList(s) :' + binary_to_hex(self.hashList[0])
      for i in range(1,len(self.hashList)):
         print indstr + indent + '             :' + binary_to_hex(self.hashList[i])
      print indstr + indent + 'HashStop     :' + binary_to_hex(self.hashStop)
         


################################################################################
################################################################################
class PayloadGetBlocks(object):
   command = 'getblocks'

   def __init__(self, version=1, startCt=-1, hashStartList=[], hashStop=''):
      self.version    = 1
      self.hashList  = hashStartList
      self.hashStop   = hashStop
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         gbData = toUnpack
      else:
         gbData = BinaryUnpacker( toUnpack )

      self.version = gbData.get(UINT32)
      nhash = gbData.get(VAR_INT)
      for i in range(nhash):
         self.hashList.append(gbData.get(BINARY_CHUNK, 32))
      self.hashStop = gbData.get(BINARY_CHUNK, 32)
      return self

   def serialize(self):
      nhash = len(self.hashList)
      bp = BinaryPacker()
      bp.put(UINT32, self.version)
      bp.put(VAR_INT, nhash)
      for i in range(nhash):
         bp.put(BINARY_CHUNK,  self.hashList[i], width=32)
      bp.put(BINARY_CHUNK, self.hashList, width=32)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getheaders):'
      print indstr + indent + 'Version      :' + str(self.version)
      print indstr + indent + 'HashList(s) :' + binary_to_hex(self.hashList[0])
      for i in range(1,len(self.hashList)):
         print indstr + indent + '             :' + binary_to_hex(self.hashList[i])
      print indstr + indent + 'HashStop     :' + binary_to_hex(self.hashStop)


################################################################################
################################################################################
class PayloadTx(object):
   command = 'tx'

   def __init__(self, tx=PyTx()):
      self.tx = tx

   def unserialize(self, toUnpack):
      self.tx.unserialize(toUnpack)
      return self

   def serialize(self):
      return self.tx.serialize()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(tx):'
      self.tx.pprint(nIndent+1)


################################################################################
################################################################################
class PayloadHeaders(object):
   command = 'headers'

   def __init__(self, header=PyBlockHeader(), headerlist=[]):
      self.header = header
      self.headerList = headerlist
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         headerData = toUnpack
      else:
         headerData = BinaryUnpacker( toUnpack )

      self.headerList = []
      self.header.unserialize(headerData)
      numHeader = headerData.get(VAR_INT)
      for i in range(numHeader):
         self.headerList.append(PyBlockHeader().unserialize(headerData))
      headerData.get(VAR_INT) # Not sure if this is even used, ever
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.header.serialize())
      bp.put(VAR_INT, len(self.headerList))
      for header in self.headerList:
         bp.put(BINARY_CHUNK, header.serialize())
         bp.put(VAR_INT, 0)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(headers):'
      self.header.pprint(nIndent+1)
      for header in self.headerList:
         print indstr + indent + 'Header:', header.getHash()


################################################################################
################################################################################
class PayloadBlock(object):
   command = 'block'

   def __init__(self, header=PyBlockHeader(), txlist=[]):
      self.header = header
      self.txList = txlist
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack
      else:
         blkData = BinaryUnpacker( toUnpack )

      self.txList = []
      self.header.unserialize(blkData)
      numTx = blkData.get(VAR_INT)
      for i in range(numTx):
         self.txList.append(PyTx().unserialize(blkData))
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.header.serialize())
      bp.put(VAR_INT, len(self.txList))
      for tx in self.txList:
         bp.put(BINARY_CHUNK, tx.serialize())
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(block):'
      self.header.pprint(nIndent+1)
      for tx in self.txList:
         print indstr + indent + 'Tx:', tx.getHashHex()


################################################################################
class PayloadAlert(object):
   command = 'alert'

   def __init__(self):
      self.version = 1
      self.relayUntil = 0
      self.expiration = 0
      self.uniqueID   = 0
      self.cancelVal  = 0
      self.cancelSet  = []
      self.minVersion = 0
      self.maxVersion = 0
      self.subVerSet  = []
      self.comment    = ''
      self.statusBar  = ''
      self.reserved   = ''
      self.signature   = ''
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack
      else:
         blkData = BinaryUnpacker( toUnpack )

      return self

   def serialize(self):
      bp = BinaryPacker()
      return bp.getBinaryString()


   def pprint(self, nIndent=0):
      print nIndent*'\t' + 'ALERT(...)'

REJECT_MALFORMED_CODE = 0x01
REJECT_INVALID_CODE = 0x10
REJECT_OBSOLETE_CODE = 0x11
REJECT_DUPLICATE_CODE = 0x12
REJECT_NONSTANDARD_CODE = 0x40
REJECT_DUST_CODE = 0x41
REJECT_INSUFFICIENTFEE_CODE = 0x42
REJECT_CHECKPOINT_CODE = 0x43

################################################################################
class PayloadReject(object):
   command = 'reject'

   def __init__(self):
      self.messageType = ''
      self.message = ''
      self.data = ''
      self.serializedData = None
      self.rejectCode = None
      
   def unserialize(self, toUnpack):
      bu = BinaryUnpacker(toUnpack)
      self.messageType = bu.get(VAR_STR)
      self.rejectCode = bu.get(INT8)
      self.message = bu.get(VAR_STR)
      self.data = bu.get(BINARY_CHUNK, bu.getRemainingSize())
      self.serializedData = toUnpack
      return self

   def serialize(self):
      return self.serializedData

   def pprint(self, nIndent=0):
      print nIndent*'\t' + 'REJECT - Tx: ' + self.message
      
################################################################################
# Use this map to figure out which object to serialize/unserialize from a cmd
PayloadMap = {
   'ping':        PayloadPing,
   'tx':          PayloadTx,
   'inv':         PayloadInv,
   'version':     PayloadVersion,
   'verack':      PayloadVerack,
   'addr':        PayloadAddr,
   'getdata':     PayloadGetData,
   'getheaders':  PayloadGetHeaders,
   'getblocks':   PayloadGetBlocks,
   'block':       PayloadBlock,
   'headers':     PayloadHeaders,
   'alert':       PayloadAlert,
   'reject':      PayloadReject }


class FakeClientFactory(ReconnectingClientFactory):
   """
   A fake class that has the same methods as an ArmoryClientFactory,
   but doesn't do anything.  If there is no internet, then we want 
   to be able to use the same calls
   """
   #############################################################################
   def __init__(self, \
                def_handshake=None, \
                func_loseConnect=(lambda: None), \
                func_madeConnect=(lambda: None), \
                func_newTx=(lambda x: None), \
                func_newBlock=(lambda x,y: None), \
                func_inv=(lambda x: None)): pass
   def addTxToMemoryPool(self, pytx): pass
   def handshakeFinished(self, protoObj): pass
   def clientConnectionLost(self, connector, reason): pass
   def connectionFailed(self, protoObj, reason): pass
   def sendTx(self, pytxObj): pass

################################################################################
# It seems we need to do this frequently when downloading headers & blocks
# This only returns a list of numbers, but one list-comprehension to get hashes
def createBlockLocatorNumList(topblk):
   blockNumList = []
   n,step,niter = topblk,1,0
   while n>0:
      blockNumList.append(n)
      if niter >= 10:
         step *= 2
      n -= step
      niter += 1
   blockNumList.append(0)
   return blockNumList


################################################################################
def forceDeferred(callbk):
   if callbk:
      if isinstance(callbk, Deferred):
         return callbk
      else:
         d = Deferred()
         d.addCallback(callbk)
         return d

# kate: indent-width 3; replace-tabs on;
