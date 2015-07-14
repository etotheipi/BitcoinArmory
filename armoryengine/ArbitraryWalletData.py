###############################################################################
#                                                                             #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                          #
# Distributed under the GNU Affero General Public License (AGPL v3)           #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                        #
#                                                                             #
###############################################################################
#
# Infinimap:
#
#     An Infinimap is a concept I (ACR) created, which is analogous to BIP32
#     key trees, but for holding arbitrary data instead of ECDSA keys.  It's
#     an infinite dimensional key-value map, the example below shows using
#     it to store wallet settings, but it can be used to store just about
#     anything:
#
#        inf = Infinimap()
#        inf.setData(['CreateDate'],  'Oct 29, 2014, 8:33pm')
#        inf.setData(['Settings','HomePath'], '/home/user/.armory')
#        inf.setData(['Settings','DebugLevel'], 'DEBUG2')
#        inf.setData(['Settings','Defaults'], 'Defaults for ABC')
#        inf.setData(['Settings','Defaults','A'], 'True')
#        inf.setData(['Settings','Defaults','B'], 'False')
#        inf.setData(['Settings','Defaults','C'], '/media/b39f-881a')
#
#        inf.createEncryptedEntry(['APIKeys', 'Exchange1'], aci, ekey))
#        inf.setData(['APIKeys','Exchange1'], SecureBinaryData('PlainKey1'))
#
#        inf.createEncryptedEntry(['APIKeys', 'Exchange2'], aci, ekey))
#        inf.setData(['APIKeys','Exchange2'], SecureBinaryData('PlainKey2'))
#
#    To avoid recursion limit issues, the max key depth is limited to 32.
#
#    The last two examples show us putting encrypted data into the map.  We
#    always get and set plaintext data and rely on the ekey to be unlocked.
#
#    Note an important feature of this map type, which is shared by BIP32
#    wallets but is not obvious:  any node can hold both data, not just the
#    leaves of the tree.  For instance, ['Settings','Defaults'] has both
#    data, but also has children.  This means that you can setData on *any*
#    keyList, regardless of whether a parent path is holding data.
#
###############################################################################

from ArmoryUtils import *

from ArmoryEncryption import ArmoryCryptInfo, EkeyMustBeUnlocked, NULLCRYPTINFO
from BinaryPacker import BinaryPacker, BinaryUnpacker, makeBinaryUnpacker
from BitSet import BitSet
from WalletEntry import WalletEntry


###############################################################################
# Used to be called "InfinimapNode"
class ArbitraryWalletData(WalletEntry):
   FILECODE = 'ARBDATA_'
   CRYPTPADDING = 128

   def __init__(self, klist=None, data=None, cryptInfo=None):
      super(ArbitraryWalletData, self).__init__()
      self.keyList   = klist[:] if klist else []
      self.cryptInfo = cryptInfo.copy() if cryptInfo else NULLCRYPTINFO()
      self.dataStr   = data
      self.ekeyRef   = None

   ############################################################################
   def isEmpty(self):
      return self.dataStr is None or len(self.dataStr)==0

   ############################################################################
   def useEncryption(self):
      if self.cryptInfo is None:
         raise UninitializedError('cryptInfo is None, this should not happen')
      return self.cryptInfo.useEncryption()


   ############################################################################
   def noEncryption(self):
      return not self.useEncryption()

   ############################################################################
   def enableEncryption(self, cryptInfo, ekeyRef):
      if not self.isEmpty():
         LOGWARN('Enabling encryption on an AWD object that already has data')

      self.cryptInfo = cryptInfo.copy()
      self.ekeyRef   = ekeyRef

   ############################################################################
   def disableEncryption(self):
      if not self.isEmpty():
         LOGWARN('Disabling encryption on an AWD object that already has data')

      self.cryptInfo = NULLCRYPTINFO()
      self.ekeyRef   = None

   ############################################################################
   def linkWalletEntries(self, wltFileRef):
      WalletEntry.linkWalletEntries(self, wltFileRef)
      if self.cryptInfo.useEncryption():
         self.ekeyRef = self.wltFileRef.ekeyMap.get(self.cryptInfo.keySource)
         if self.ekeyRef is None:
            LOGERROR('ArbitraryData/InfinimapNode could not link ekey')



   ############################################################################
   @EkeyMustBeUnlocked('ekeyRef')
   def getPlainDataCopy(self):
      """
      self.ekeyRef must be unlocked (if it is encrypted).  Returns a copy of
      the data as a python string (unlike other get*Copy() methods in other
      classes).
      """
      if self.isEmpty():
         return ''

      if self.noEncryption():
         return self.dataStr
      else:
         sbdCrypt = SecureBinaryData(self.dataStr)
         sbdPlain = self.cryptInfo.decrypt(sbdCrypt, ekeyObj=self.ekeyRef)

         bu = BinaryUnpacker(sbdPlain.toBinStr())
         lenData = bu.get(UINT32)
         return SecureBinaryData(bu.get(BINARY_CHUNK, lenData))


   ############################################################################
   def setPlaintext(self, plainData):
      if self.cryptInfo.useEncryption():
         raise EncryptionError('Made a plain setData call on encrypted node')

      self.cryptInfo = NULLCRYPTINFO()
      self.ekeyRef = None
      self.dataStr = plainData[:]




   ############################################################################
   @EkeyMustBeUnlocked('ekeyRef')
   def setPlaintextToEncrypt(self, sbdPlain):
      """
      self.cryptInfo and self.ekeyRef must be set and the ekey must be
      unlocked before calling this method.  This method only destroys a copy
      of the plaintext data.  The caller is responsible for handling the
      destruction of the input. argument.
      """
      if self.noEncryption():
         raise EncryptionError('Attempted to set encrypted data to plain node')
      sbdPlain = SecureBinaryData(sbdPlain)
      lenPlain = sbdPlain.getSize()
      paddedLen = roundUpMod(lenPlain+4, ArbitraryWalletData.CRYPTPADDING)
      zeroBytes = '\x00'*(paddedLen - (lenPlain+4))
      bp = BinaryPacker()
      bp.put(UINT32, lenPlain)
      bp.put(BINARY_CHUNK, sbdPlain.toBinStr())
      bp.put(BINARY_CHUNK, zeroBytes)

      sbdPlain = SecureBinaryData(bp.getBinaryString())

      self.dataStr = self.cryptInfo.encrypt(sbdPlain, ekeyObj=self.ekeyRef)
      self.dataStr = self.dataStr.toBinStr()

      sbdPlain.destroy()


   ############################################################################
   def prettyData(self):
      if self.dataStr is None:
         return ''
      elif self.cryptInfo.useEncryption():
         return '<encrypted:%s>' % binary_to_hex(self.dataStr)[:16] + \
            ('(Encrypted with: %s)' % binary_to_hex(self.cryptInfo.keySource)[:8])
      else:
         return self.dataStr

   ############################################################################
   def pprintOneLineStr(self, indent=0):
      return 'AWD: ' + self.prettyString(indent)

   ############################################################################
   def prettyString(self, indent=0):
      return '%s%s: "%s"' % (indent*' ', str(self.keyList), self.prettyData())

   ############################################################################
   def getPPrintPairs(self):
      pairs = [ ['KeyList', '+'.join(["'%s'" % s.replace("'","^") for s in self.keyList])]]
      if self.cryptInfo.useEncryption():
         pairs.append(['IsEncrypted', 'True'])
         pairs.append(['CryptInfo', self.cryptInfo.getPPrintStr()])
      else:
         pairs.append(['IsEncrypted', 'False'])
         pairs.append(['Message', "'%s'" % self.dataStr.replace("'","^")])

      return pairs

   ############################################################################
   def serialize(self):
      if self.dataStr is None:
         raise UninitializedError('Cannot serialize uninit AWD object')

      bp = BinaryPacker()

      flags = BitSet(8)
      flags.setBit(0, self.cryptInfo.useEncryption())

      bp = BinaryPacker()
      bp.put(VAR_INT,  len(self.keyList))
      for k in self.keyList:
         bp.put(VAR_STR,  k)

      bp.put(BITSET, flags, 1)
      if self.cryptInfo.useEncryption():
         bp.put(BINARY_CHUNK, self.cryptInfo.serialize(), 32)

      bp.put(VAR_STR, self.dataStr)

      return bp.getBinaryString()


   ############################################################################
   def unserialize(self, theStr):
      klist = []

      bu = makeBinaryUnpacker(theStr)
      nkeys = bu.get(VAR_INT)
      for k in range(nkeys):
         klist.append( bu.get(VAR_STR) )

      flags = bu.get(BITSET, 1)
      useEncryption = flags.getBit(0)
      if useEncryption:
         serACI = bu.get(BINARY_CHUNK, 32)

      data = bu.get(VAR_STR)


      self.__init__()
      self.keyList   = klist[:]
      self.dataStr   = data[:]
      self.ekeyRef   = None
      if useEncryption:
         self.cryptInfo = ArmoryCryptInfo().unserialize(serACI)
      else:
         self.cryptInfo = NULLCRYPTINFO()

      return self

   ############################################################################
   def insertIntoInfinimap(self, infmap, errorIfDup=True):
      node = infmap.getNode(self.keyList, doCreate=True)
      if not node.isEmpty() and errorIfDup:
         raise KeyError('Node "%s" already has data' % str(self.keyList))

      if not node.keyList == self.keyList:
         raise ShouldNotGetHereError('Somehow returned key list does not match!?')

      node.awdObj = self


###############################################################################
#
# NOTE:  We override __getattr__ to pass through unrecognized attribute reqs
#        to the underlying awdObj member.  This is very similar to inheriting
#        from that class, but instead we store an instance of that class as
#        a member.
#
#
# We keep InfinimapNode separate from ArbitraryWalletData because I'd like to
# later reuse this class to work with other data types.  i.e. simply replace
# self.awdObj with another datatype.
###############################################################################
class InfinimapNode(object):
   def __init__(self, klist=None, parent=None):
      super(InfinimapNode, self).__init__()
      self.keyList   = klist[:] if klist else []
      self.awdObj    = ArbitraryWalletData()
      self.parent    = parent
      self.children  = {}

      self.awdObj.keyList = self.keyList[:]


   ############################################################################
   def __getattr__(self, attr):
      if self.awdObj is None:
         raise AttributeError('awdObj is None, cannot resolve attr: %s' % attr)

      return getattr(self.awdObj, attr)


   ############################################################################
   def getSelfKey(self):
      return '' if len(self.keyList) == 0 else self.keyList[-1]

   ############################################################################
   def getKeyList(self):
      return self.keyList[:]

   ############################################################################
   def getNodeRecurse(self, keyList, doCreate=False):
      # If size is zero, we're at the requested node
      if len(keyList) == 0:
         return self

      key = keyList[0]
      childKeyList = self.keyList[:] + [key]

      if doCreate:
         # Always creating the next child seems inefficient, but the
         # alternative is doing two map lookups.  We will revisit this
         # if there's a reason to make this container high-performance
         nextMaybeChild = InfinimapNode(childKeyList, self)
         nextNode = self.children.setdefault(key, nextMaybeChild)
         return nextNode.getNodeRecurse(keyList[1:], doCreate)
      else:
         nextNode = self.children.get(key)
         if nextNode is None:
            return None
         else:
            return nextNode.getNodeRecurse(keyList[1:], doCreate)



   ############################################################################
   def pprintRecurse(self, indentCt=0, indentSz=3):
      print self.prettyString(indentCt * indentSz)
      for key,child in self.children.iteritems():
         child.pprintRecurse(indentCt+1, indentSz)



   ############################################################################
   def applyToBranchRecurse(self, funcInputNode, topFirst=True):
      if topFirst:
         funcInputNode(self)

      for key,child in self.children.iteritems():
         child.applyToBranchRecurse(funcInputNode, topFirst)

      if not topFirst:
         funcInputNode(self)


   ############################################################################
   def recurseDelete(self):
      keysToDelete = []
      for key,child in self.children.iteritems():
         child.recurseDelete()
         keysToDelete.append(key)

      for key in keysToDelete:
         del self.children[key]


   ############################################################################
   def isEmpty(self):
      return self.awdObj is None or self.awdObj.isEmpty()



###############################################################################
class Infinimap(object):

   MAX_DEPTH = 32

   ############################################################################
   def __init__(self):
      self.root = InfinimapNode()

   ############################################################################
   @staticmethod
   def checkKeyList(keyList, data=None):
      listSize = len(keyList)
      if listSize > Infinimap.MAX_DEPTH:
         raise MaxDepthExceeded('KeyList size/depth is %d' % listSize)

      for key in keyList:
         if not isinstance(key, str):
            raise KeyError('All keys in path must be reg strings, no unicode')

      if data and not isinstance(data, str):
         raise TypeError('Data for infinimap must be reg string, no unicode')



   ############################################################################
   def getNode(self, keyList, doCreate=False):
      self.checkKeyList(keyList)
      return self.root.getNodeRecurse(keyList, doCreate=doCreate)

   ############################################################################
   # Shortcut function to directly get AWD data in the map
   def getData(self, keyList):
      node = self.getNode(keyList)
      return None if node is None else node.getPlainDataCopy()


   ############################################################################
   # Shortcut function to directly set AWD data in the map
   # If the AWD object uses encryption, the ekey needs to be unlocked before
   # calling this method.  theData should always be unencrypted, and this
   # method will encrypt it on the way into the map.
   def setData(self, keyList, theData, doCreate=True, errorIfDup=False):
      # By default we create the key path
      node = self.getNode(keyList, doCreate=doCreate)
      if node is None:
         raise KeyError('Key path does not exist to be set: %s' % keyList)

      if node.noEncryption():
         if not isinstance(theData, str):
            raise TypeError('Data for infinimap must be reg string (no unicode)')
      else:
         if not isinstance(theData, SecureBinaryData):
            raise TypeError('Data for encrypted entry must be SecureBinaryData')

      if errorIfDup and node.awdObj.dataStr and len(node.awdObj.dataStr)>0:
         raise KeyError('Infinimap entry already has a value: %s' % str(keyList))

      node.awdObj.keyList = node.keyList[:]

      if node.useEncryption():
         node.awdObj.setPlaintextToEncrypt(theData)
      else:
         node.awdObj.setPlaintext(theData if theData is not None else '')

   ############################################################################
   def createEncryptedEntry(self, keyList, cryptInfo, ekeyRef, errorIfDup=True):
      node = self.getNode(keyList, doCreate=True)
      if not node.isEmpty() and errorIfDup:
         raise KeyError('Attempted create node that exists: %s' % str(keyList))


      node.enableEncryption(cryptInfo, ekeyRef)
      return node



   ############################################################################
   def clearData(self, keyList, andEncryptionInfo=False):
      self.checkKeyList(keyList)
      node = self.root.getNodeRecurse(keyList, doCreate=False)
      if node is None:
         LOGWARN('Trying to clear a node that does not exist')

      node.awdObj.dataStr = ''

      if andEncryptionInfo:
         node.cryptInfo = NULLCRYPTINFO()
         node.ekeyRef   = None




   ############################################################################
   def pprint(self):
      self.root.pprintRecurse()

   ############################################################################
   def applyToMap(self, funcInputNode, topFirst=True, withRoot=False):
      if withRoot:
         self.root.applyToBranchRecurse(funcInputNode, topFirst)
      else:
         for key,child in self.root.children.iteritems():
            self.applyToBranch([key], funcInputNode, topFirst)

   ############################################################################
   def applyToBranch(self, keyList, funcInputNode, topFirst=True):
      self.checkKeyList(keyList)
      node = self.root.getNodeRecurse(keyList, doCreate=False)
      if node is None:
         raise KeyError('Key path does not exist:  %s' % str(keyList))

      node.applyToBranchRecurse(funcInputNode, topFirst)

   ############################################################################
   def clearMap(self):
      self.root.recurseDelete()

   ############################################################################
   def clearBranch(self, keyList, andBranchPoint=True):
      self.checkKeyList(keyList)
      node = self.root.getNodeRecurse(keyList, doCreate=False)
      if node is None:
         raise KeyError('Key path does not exist:  %s' % str(keyList))

      node.recurseDelete()

      if andBranchPoint:
         del node.parent.children[node.keyList[-1]]


   ############################################################################
   def countNodes(self, keyList=None):
      ct = [0]
      def ctfunc(node):
         ct[0] += 1

      if keyList is None:
         self.applyToMap(ctfunc)
      else:
         self.applyToBranch(keyList, ctfunc)

      return ct[0]


   ############################################################################
   def countLeaves(self, keyList=None):
      if len(self.root.children)==0:
         return 0

      ct = [0]
      def ctfunc(node):
         ct[0] += 1 if len(node.children)==0 else 0

      if keyList is None:
         self.applyToMap(ctfunc)
      else:
         self.applyToBranch(keyList, ctfunc)

      return ct[0]

   ############################################################################
   def countNonEmpty(self, keyList=None):
      ct = [0]
      def ctfunc(node):
         if not node.isEmpty():
            ct[0] += 1

      if keyList is None:
         self.applyToMap(ctfunc)
      else:
         self.applyToBranch(keyList, ctfunc)

      return ct[0]

