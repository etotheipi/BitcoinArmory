from armoryengine.ArmoryUtils import *
from armoryengine.Transaction import *

MULTISIG_VERSION = 1

################################################################################
#
# Multi-signature transactions are going to require a ton of different 
# primitives to be both useful and safe for escrow.  All primitives should
# have an ASCII-armored-esque form for transmission through email or text
# file, as well as binary form for when file transfer is guaranteed
#
# Until Armory implements BIP 32, these utilities are more suited to
# low-volume use cases, such as one-time escrow, or long-term savings
# using multi-device authentication.  Multi-signature *wallets* which
# behave like regular wallets but spit out P2SH addresses and usable 
# in every day situations -- those will have to wait for Armory's new
# wallet format.
#
# Concepts:
#     "Lockbox":  A "lock box" for putting coins that will be protected
#                  with multiple signatures.  The lockbox contains both
#                  the script info as well as meta-data, like participants'
#                  names and emails associated with each public key.
#
#
# 
#     
#                  
################################################################################
"""
Use-Case 1 -- Protecting coins with 2-of-3 computers (2 offline, 1 online):

   Create or access existing wallet on each of three computers. 

   Online computer will create the lockbox - needs one public key from its
   own wallet, and one from each offline wallet.  Can have both WO wallets
   on the online computer, and pull keys directly from those.

   User creates an lockbox with all three keys, labeling them appropriately
   This lockbox will be added to the global list.

   User will fund the lockbox from an existing offline wallet with lots of
   money.  He does not need to use the special funding procedure, which is
   only needed if there's multiple people involved with less than full trust.
   
   Creates the transaction as usual, but uses the "lockbox" button for the
   recipient instead of normal address.  The address line will show the 
   lockbox ID and short description.  

   Will save the lockbox and the offline transaction to the USB drive

"""

LOCKBOXIDSIZE = 8
PROMIDSIZE = 4
LBPREFIX, LBSUFFIX = 'Lockbox[Bare:', ']'
LBP2SHPREFIX = 'Lockbox['

################################################################################
def calcLockboxID(script=None, scraddr=None):
   # ScrAddr is "Script/Address" and for multisig it is 0xfe followed by
   # M and N, then the SORTED hash160 values of the public keys
   # Part of the reason for using "ScrAddrs" is to bundle together
   # different scripts that have the same effective signing authority.
   # Different sortings of the same public key list have same signing
   # authority and therefore should have the same ScrAddr

   if script is not None:
      scrType = getTxOutScriptType(script)
      if not scrType==CPP_TXOUT_MULTISIG:
         LOGERROR('Not a multisig script!')
         return None
      scraddr = script_to_scrAddr(script)

   if not scraddr.startswith(SCRADDR_MULTISIG_BYTE):
      LOGERROR('ScrAddr is not a multisig script!')
      return None

   hashedData = hash160(MAGIC_BYTES + scraddr)
   return binary_to_base58(hashedData)[1:9]


################################################################################
def createLockboxEntryStr(lbID, isBareMultiSig=False):
   return '%s%s%s' % (LBPREFIX if isBareMultiSig else LBP2SHPREFIX,
                       lbID, LBSUFFIX)

################################################################################
def readLockboxEntryStr(addrtext):
   result = None
   if isBareLockbox(addrtext) or isP2SHLockbox(addrtext):
      len(LBPREFIX if isBareLockbox(addrtext) else LBP2SHPREFIX)
      idStr = addrtext[len(LBPREFIX if isBareLockbox(addrtext) else LBP2SHPREFIX):
                       addrtext.find(LBSUFFIX)]
      if len(idStr)==LOCKBOXIDSIZE:
         result = idStr
   return result

################################################################################
def isBareLockbox(addrtext):
   return addrtext.startswith(LBPREFIX)

def scrAddr_to_displayStr(scrAddr, wltMap, lbMap):
   retStr = ''
   if scrAddr[0] in (SCRADDR_P2PKH_BYTE, SCRADDR_P2SH_BYTE):
      retStr = scrAddr_to_addrStr(scrAddr)
   elif scrAddr[0] == SCRADDR_MULTISIG_BYTE:
      retStr = getDisplayStringForScript(scrAddr[1:], wltMap, lbMap)
   else:
      LOGERROR('scrAddr %s is invalid.' % binary_to_hex(scrAddr))

   return retStr


################################################################################
def isP2SHLockbox(addrtext):
   # Bugfix:  Bare prefix includes P2SH prefix, whoops.  Return false if Bare
   return addrtext.startswith(LBP2SHPREFIX) and not isBareLockbox(addrtext)

################################################################################
def getWltFromB58ID(inB58ID, inWltMap, inLBMap, inLBWltMap):
   retWlt = None
   retWltIsCPP = True

   if inB58ID in inWltMap.keys():
      retWlt = inWltMap[inB58ID]
      retWltIsCPP = False
   elif inB58ID in inLBMap.keys():
      retWlt = inLBWltMap[inB58ID]
   else:
      LOGERROR('Base58 ID %s does not represent a valid wallet or lockbox.' % \
               inB58ID)

   return (retWlt, retWltIsCPP)

################################################################################
# Function that writes a lockbox to a file. The lockbox can be appended to a
# previously existing file or can overwrite what was already in the file.
def writeLockboxesFile(inLockboxes, lbFilePath, append=False):
   writeMode = 'w'
   if append:
      writeMode = 'a'

   # Do all the serializing and bail-on-error before opening the file 
   # for writing, or we might delete it all by accident
   textOut = '\n\n'.join([lb.serializeAscii() for lb in inLockboxes]) + '\n'
   with open(lbFilePath, writeMode) as f:
      f.write(textOut)
      f.flush()
      os.fsync(f.fileno())


################################################################################
# Function that can be used to send an e-mail to multiple recipients.
def readLockboxesFile(lbFilePath):
   retLBList = []

   # Read in the lockbox file.
   with open(lbFilePath, 'r') as lbFileData:
      allData = lbFileData.read()

   # Find the lockbox starting point.
   startMark = '=====LOCKBOX'
   if startMark in allData:
      try:
         # Find the point where the start mark begins and collect either all the
         # data before the next LB or the remaining data in the file (i.e.,
         # we're on the final LB).
         pos = allData.find(startMark)
         while pos >= 0:
            nextPos = allData.find(startMark, pos+1)
            if nextPos < 0:
               nextPos = len(allData)

            # Pull in all the LB data, process it and add it to the LB list.
            lbBlock = allData[pos:nextPos].strip()
            lbox = MultiSigLockbox().unserializeAscii(lbBlock)
            LOGINFO('Read in Lockbox: %s' % lbox.uniqueIDB58)
            retLBList.append(lbox)
            pos = allData.find(startMark, pos+1)
      except:
         LOGEXCEPT('Error reading lockboxes file')
         shutil.copy(lbFilePath, lbFilePath+'.%d.bak'% long(RightNow()))

   return retLBList


#############################################################################
def getLockboxFilePaths():
   '''Function that finds the paths of all lockboxes in the Armory
      home directory.'''
   lbPaths = []

   # Return the multisig file path.
   if os.path.isfile(MULTISIG_FILE):
      lbPaths.append(MULTISIG_FILE)

   # For now, no standalone lockboxes will be returned. Maybe later....
   #for f in os.listdir(ARMORY_HOME_DIR):
   #   fullPath = os.path.join(ARMORY_HOME_DIR, f)
   #   if os.path.isfile(fullPath) and not fullPath.endswith('lockbox.txt'):
   #      lbPaths.append(fullPath)

   return lbPaths

#############################################################################
def isMofNNonStandardToSpend(m, n):
   # Minimum non-standard tx spends
   # 4 of 4
   # 3 of 5
   # 2 of 6
   # any of 7
   return (n > 3 and m > 3) or \
          (n > 4 and m > 2) or \
          (n > 5 and m > 1) or \
           n > 6
          
################################################################################
################################################################################
class MultiSigLockbox(AsciiSerializable):

   OBJNAME   = 'Lockbox'
   BLKSTRING = 'LOCKBOX'
   EMAILSUBJ = 'Armory Lockbox Definition - %s'
   EMAILBODY = """
               The chunk of text below is a complete lockbox definition 
               needed to track the balance of this multi-sig lockbox, as well
               as create signatures for proposed spending transactions.  Open
               the Lockbox Manager, click "Import Lockbox" in the first row,
               then copy the text below into the import box, including the
               first and last lines.  You will need to restart Armory and let
               it rescan if this lockbox has already been used."""

   #############################################################################
   def __init__(self, name=None, descr=None, M=None, N=None, dPubKeys=None, 
                                     createDate=None, version=MULTISIG_VERSION):
      
      self.version     = MULTISIG_VERSION
      self.shortName   = toUnicode(name)
      self.longDescr   = toUnicode(descr)
      self.createDate  = long(RightNow()) if createDate is None else createDate
      self.magicBytes  = MAGIC_BYTES
      self.uniqueIDB58 = None
      self.asciiID     = None

      if (M is not None) and (N is not None) and (dPubKeys is not None):
         self.setParams(name, descr, M, N, dPubKeys, createDate, version)

   #############################################################################
   def setParams(self, name, descr, M, N, dPubKeys, createDate=None, 
                                                   version=MULTISIG_VERSION):
      
      
      self.version = version
      self.magicBytes = MAGIC_BYTES

      self.shortName = name
      self.longDescr = toUnicode(descr)
      self.M         = M
      self.N         = N
      self.dPubKeys  = dPubKeys[:]
      binPubKeys     = [p.binPubKey for p in dPubKeys]
      self.a160List  = [hash160(p)  for p in binPubKeys]

      if createDate is not None:
         self.createDate = createDate

      script = pubkeylist_to_multisig_script(binPubKeys, self.M, True)

      # Computed some derived members
      self.binScript    = script
      self.scrAddr      = script_to_scrAddr(script)
      self.p2shScrAddr  = script_to_scrAddr(script_to_p2sh_script(script))
      self.uniqueIDB58  = calcLockboxID(script)
      self.opStrList    = convertScriptToOpStrings(script)
      self.asciiID = self.uniqueIDB58 # need a common member name in all classes
      
      
   #############################################################################
   def serialize(self):

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES)
      bp.put(UINT64,       self.createDate)
      bp.put(VAR_STR,      toBytes(self.shortName))
      bp.put(VAR_STR,      toBytes(self.longDescr))
      bp.put(UINT8,        self.M)
      bp.put(UINT8,        self.N)
      for i in range(self.N):
         bp.put(VAR_STR,   self.dPubKeys[i].serialize())

      return bp.getBinaryString()


   #############################################################################
   # In the final stages of lockbox design, I changed up the serialization 
   # format for lockboxes, and decided to see how easy it was to transition
   # using the version numbers.   Here's the old unserialize version, modified
   # to map the old data to the new format.  ArmoryQt will read all the
   # lockboxes in the file, it will call this on each one of them, and then
   # it will write out all the lockboxes whic effectively, immediately upgrades
   # all of them.
   def unserialize_v0(self, rawData, expectID=None, skipMagicCheck=False):
      LOGWARN('Version 0 lockbox detected.  Reading and converting')
      bu = BinaryUnpacker(rawData)
      boxVersion = bu.get(UINT32)
      boxMagic   = bu.get(BINARY_CHUNK, 4)
      created    = bu.get(UINT64)
      boxScript  = bu.get(VAR_STR)
      boxName    = toUnicode(bu.get(VAR_STR))
      boxDescr   = toUnicode(bu.get(VAR_STR))
      nComment   = bu.get(UINT32)

      boxComms = ['']*nComment
      for i in range(nComment):
         boxComms[i] = toUnicode(bu.get(VAR_STR))

      # Check the magic bytes of the lockbox match
      if not boxMagic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    Lockbox Magic: ' + binary_to_hex(boxMagic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')

      
      # Lockbox ID is written in the first line, it should match the script
      # If not maybe a version mistmatch, serialization error, or bug
      # (unfortunately, for mixed network testing, the lockbox ID is the
      #  hash of the script & the MAGIC_BYTES, which means we need to
      #  skip checking the ID if we are skipping MAGIC)
      if expectID and not calcLockboxID(boxScript) == expectID and not skipMagicCheck:
         LOGERROR('ID on lockbox block does not match script')
         raise UnserializeError('ID on lockbox does not match!')


      # Now we switch to the new setParams method
      M,N,a160s,pubs = getMultisigScriptInfo(boxScript) 
      dPubKeys = [DecoratedPublicKey(pub, com) for pub,com in zip(pubs,boxComms)]

      # No need to read magic bytes -- already checked & bailed if incorrect
      self.setParams(boxName, boxDescr, M, N, dPubKeys, created)
      return self


   #############################################################################
   def unserialize(self, rawData, expectID=None, skipMagicCheck=False):

      bu = BinaryUnpacker(rawData)
      lboxVersion = bu.get(UINT32)

      # If this is an older version, use conversion method
      if lboxVersion==0:
         return self.unserialize_v0(rawData, expectID)

      lboxMagic   = bu.get(BINARY_CHUNK, 4)
      created    = bu.get(UINT64)
      lboxName    = toUnicode(bu.get(VAR_STR))
      lboxDescr   = toUnicode(bu.get(VAR_STR))
      M          = bu.get(UINT8)
      N          = bu.get(UINT8)

      dPubKeys = []
      for i in range(N):
         dPubKeys.append(DecoratedPublicKey().unserialize(bu.get(VAR_STR), 
                                                skipMagicCheck=skipMagicCheck))


      # Issue a warning if the versions don't match
      if not lboxVersion == MULTISIG_VERSION:
         LOGWARN('Unserialing lockbox of different version')
         LOGWARN('   Lockbox Version: %d' % lboxVersion)
         LOGWARN('   Armory  Version: %d' % MULTISIG_VERSION)

      # Check the magic bytes of the lockbox match
      if not lboxMagic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    Lockbox Magic: ' + binary_to_hex(lboxMagic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')

      
      binPubKeys = [p.binPubKey for p in dPubKeys]
      lboxScript = pubkeylist_to_multisig_script(binPubKeys, M)

      # Lockbox ID is written in the first line, it should match the script
      # If not maybe a version mistmatch, serialization error, or bug
      if expectID and not calcLockboxID(lboxScript) == expectID and not skipMagicCheck:
         LOGERROR('ID on lockbox block does not match script')
         LOGERROR('    Expecting:   %s' % str(expectID))
         LOGERROR('    Calculated:  %s' % str(calcLockboxID(lboxScript)))
         raise UnserializeError('ID on lockbox does not match!')

      # No need to read magic bytes -- already checked & bailed if incorrect
      self.setParams(lboxName, lboxDescr, M, N, dPubKeys, created)

      return self




   #############################################################################
   def toJSONMap(self):
      outjson = {}
      outjson['version']      = self.version
      outjson['magicbytes']   = binary_to_hex(MAGIC_BYTES)
      outjson['id']           = self.asciiID

      outjson['lboxname'] =  self.shortName
      outjson['lboxdescr'] =  self.longDescr
      outjson['M'] = self.M
      outjson['N'] = self.N

      outjson['pubkeylist'] = [dpk.toJSONMap() for dpk in self.dPubKeys]

      outjson['a160list'] = [binary_to_hex(hash160(p.binPubKey)) \
                             for p in self.dPubKeys]
      outjson['addrstrs'] = [hash160_to_addrStr(hex_to_binary(a)) \
                             for a in outjson['a160list']]

      outjson['txoutscript'] = binary_to_hex(self.binScript)
      outjson['p2shscript']  = binary_to_hex(scrAddr_to_script(self.p2shScrAddr))
      outjson['p2shaddr']    = scrAddr_to_addrStr(self.p2shScrAddr)
      outjson['createdate']  = self.createDate

      return outjson


   #############################################################################
   def fromJSONMap(self, jsonMap, skipMagicCheck=False):
      ver   = jsonMap['version'] 
      magic = hex_to_binary(jsonMap['magicbytes'])
      uniq  = jsonMap['id']
   
      # Issue a warning if the versions don't match
      if not ver == UNSIGNED_TX_VERSION:
         LOGWARN('Unserializing Lockbox of different version')
         LOGWARN('   USTX    Version: %d' % ver)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      # Check the magic bytes of the lockbox match
      if not magic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    USTX    Magic: ' + binary_to_hex(magic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')

      name   = jsonMap['lboxname']
      descr  = jsonMap['lboxdescr']
      M      = jsonMap['M']
      N      = jsonMap['N']
      
      pubs = []
      for i in range(N):
         pubs.append(DecoratedPublicKey().fromJSONMap(jsonMap['pubkeylist'][i], skipMagicCheck))

      created = jsonMap['createdate']
      self.setParams(name, descr, M, N, pubs, created)
      return self


   #############################################################################
   def pprint(self):
      print 'Multi-signature %d-of-%d lockbox:' % (self.M, self.N)
      print '   Unique ID:  ', self.uniqueIDB58
      print '   Created:    ', unixTimeToFormatStr(self.createDate)
      print '   LBox Name:  ', self.shortName
      print '   P2SHAddr:   ', scrAddr_to_addrStr(self.p2shScrAddr)
      print '   Box Desc:   '
      print '     ', self.longDescr[:70]
      print '   Key List:   '
      print '   Script Ops: '
      for opStr in self.opStrList:
         print '       ', opStr
      print''
      print '   Key Info:   '
      for i in range(len(self.dPubKeys)):
         print '            Key %d' % i
         print '           ', binary_to_hex(self.dPubKeys[i].binPubKey)[:40] + '...'
         print '           ', hash160_to_addrStr(self.a160List[i])
         print ''

   #############################################################################
   def pprintOneLine(self):
      print 'LockBox %s:  %s-of-%s, created: %s;  "%s"' % (self.uniqueIDB58, 
         self.M, self.N, unixTimeToFormatStr(self.createDate), self.shortName)


   ################################################################################
   def createDecoratedTxOut(self, value=0, asP2SH=False):
      if not asP2SH:
         dtxoScript = self.binScript
         p2shScript = None
      else:
         dtxoScript = script_to_p2sh_script(self.binScript)
         p2shScript = self.binScript

      return DecoratedTxOut(dtxoScript, value, p2shScript)
      


   ################################################################################
   def makeFundingTxFromPromNotes(self, promList):
      ustxiAccum = []
      
      totalPay = sum([prom.dtxoTarget.value for prom in promList])
      totalFee = sum([prom.feeAmt for prom in promList])

      # DTXO list always has at least the lockbox itself
      dtxoAccum  = [self.createDecoratedTxOut(value=totalPay, asP2SH=False)]

      # Errors with the change values should've been caught in prom::setParams
      totalInputs = 0
      totalChange = 0
      for prom in promList:
         for ustxi in prom.ustxInputs:
            ustxiAccum.append(ustxi)
            totalInputs += ustxi.value

         # Add any change outputs
         if prom.dtxoChange and prom.dtxoChange.value > 0:
            dtxoAccum.append(prom.dtxoChange)
            totalChange += prom.dtxoChange.value
      
      if not totalPay + totalFee == totalInputs - totalChange:
         raise ValueError('Promissory note values do not add up correctly')

      return UnsignedTransaction().createFromUnsignedTxIO(ustxiAccum, dtxoAccum)


   ################################################################################
   def makeSpendingTx(self, rawFundTxIdxPairs, dtxoList, feeAmt):

      ustxiAccum = []
      
      # Errors with the change values should've been caught in setParams
      totalInputs = 0
      anyP2SH = False
      for rawTx,txoIdx in rawFundTxIdxPairs:
         fundTx    = PyTx().unserialize(rawTx)
         txout     = fundTx.outputs[txoIdx]
         txoScript = txout.getScript()
         txoValue  = txout.getValue()

         if not calcLockboxID(txoScript)==self.uniqueIDB58:
            raise InvalidScriptError('Given OutPoint is not for this lockbox')

         # If the funding tx is P2SH, make sure it matches the lockbox
         # then include the subscript in the USTXI
         p2shSubscript = None
         if getTxOutScriptType(txoScript) == CPP_TXOUT_P2SH:
            # setParams guarantees self.binScript is bare multi-sig script
            txP2SHScrAddr = script_to_scrAddr(txoScript)
            lbP2SHScrAddr = script_to_p2sh_script(self.binScript)
            if not lbP2SHScrAddr == txP2SHScrAddr:
               LOGERROR('Given utxo script hash does not match this lockbox')
               raise InvalidScriptError('P2SH input does not match lockbox')
            p2shSubscript = self.binScript
            anyP2SH = True
            

         ustxiAccum.append(UnsignedTxInput(rawTx, txoIdx, p2shSubscript))
         totalInputs += txoValue


      # Copy the dtxoList since we're probably adding a change output
      dtxoAccum = dtxoList[:]

      totalOutputs = sum([dtxo.value for dtxo in dtxoAccum])
      changeAmt = totalInputs - (totalOutputs + feeAmt)
      if changeAmt < 0:
         raise ValueError('More outputs than inputs!')
      elif changeAmt > 0:
         # If adding change output, make it P2SH if any inputs were P2SH
         if not anyP2SH:
            txoScript = self.binScript
            p2shScript = None
         else:
            txoScript = script_to_p2sh_script(self.binScript)
            p2shScript = self.binScript
         dtxoAccum.append( DecoratedTxOut(txoScript, changeAmt, p2shScript))

      return UnsignedTransaction().createFromUnsignedTxIO(ustxiAccum, dtxoAccum)
      

################################################################################
################################################################################
class DecoratedPublicKey(AsciiSerializable):

   OBJNAME   = 'PublicKey'
   BLKSTRING = 'PUBLICKEY'
   EMAILSUBJ = 'Armory Public Key for Lockbox Creation - %s'
   EMAILBODY = """
               The chunk of text below is a public key that can be imported
               into the lockbox creation window in Armory.  
               Open the lockbox manager, 
               click on "Create Lockbox", and then use the "Import" button
               next to the address book button.  Copy the following text
               into the box, including the first and last lines."""


   EQ_ATTRS_SIMPLE = ['version', 'binPubKey', 'keyComment', 'wltLocator',
                      'pubKeyID', 'asciiID', 'authMethod', 'authData']

                      

   #############################################################################
   def __init__(self, binPubKey=None, keyComment=None, wltLoc=None, 
                                             authMethod=None, authData=None):
      self.version    = MULTISIG_VERSION
      self.binPubKey  = binPubKey
      self.keyComment = ''
      self.wltLocator = ''
      self.authMethod = ''
      self.authData   = authData if authData else NullAuthData()

      self.pubKeyID   = None
      self.asciiID    = None

      if binPubKey is not None:
         self.setParams(binPubKey, keyComment, wltLoc, authMethod, authData,
                                                          version=self.version)


   #############################################################################
   def setParams(self, binPubKey, keyComment=None, wltLoc=None, authMethod=None,
                                      authData=None, version=MULTISIG_VERSION):
      
      # Set params will only overwrite with non-None data
      self.binPubKey = binPubKey
      
      if keyComment is not None:
         self.keyComment = toUnicode(keyComment)

      if wltLoc is not None:
         self.wltLocator = wltLoc

      if authMethod is not None:
         self.authMethod = authMethod

      if authData is not None:
         self.authData = authData

      self.version = version

      pubkeyAddr = hash160_to_addrStr(hash160(binPubKey))
      self.pubKeyID = pubkeyAddr[:12]
      self.asciiID = self.pubKeyID # need a common member name in all classes
      


   #############################################################################
   def serialize(self):

      if not self.binPubKey:
         LOGERROR('Cannot serialize uninitialized pubkey')
         return None

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES)
      bp.put(VAR_STR,      self.binPubKey)
      bp.put(VAR_STR,      toBytes(self.keyComment))
      bp.put(VAR_STR,      self.wltLocator)
      bp.put(VAR_STR,      self.authMethod)
      bp.put(VAR_STR,      self.authData.serialize())
      return bp.getBinaryString()

   #############################################################################
   def unserialize(self, rawData, expectID=None, skipMagicCheck=False):
      ustxiList = []
      
      bu = BinaryUnpacker(rawData)
      version     = bu.get(UINT32)
      magicBytes  = bu.get(BINARY_CHUNK, 4)
      binPubKey   = bu.get(VAR_STR)
      keyComment  = toUnicode(bu.get(VAR_STR))
      wltLoc      = bu.get(VAR_STR)
      authMeth    = bu.get(VAR_STR)
      authDataStr = bu.get(VAR_STR)
      authData    = NullAuthData().unserialize(authDataStr)

      # Check the magic bytes of the lockbox match
      if not magicBytes == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    PubKey Magic: ' + binary_to_hex(magicBytes))
         LOGERROR('    Armory Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')
      
      if not version==MULTISIG_VERSION:
         LOGWARN('Unserializing LB pubkey of different version')
         LOGWARN('   PubKey  Version: %d' % version)
         LOGWARN('   Armory  Version: %d' % MULTISIG_VERSION)

      self.setParams(binPubKey, keyComment, wltLoc, authMeth, authData, version)

      if expectID and not expectID==self.pubKeyID:
         LOGERROR('Pubkey block ID does not match expected')
         return None

      return self



   #############################################################################
   def toJSONMap(self):
      outjson = {}
      outjson['version']      = self.version
      outjson['magicbytes']   = binary_to_hex(MAGIC_BYTES)
      outjson['id']           = self.asciiID

      outjson['pubkeyhex']  = binary_to_hex(self.binPubKey)
      outjson['keycomment'] = self.keyComment
      outjson['wltLocator'] = binary_to_hex(self.wltLocator)
      outjson['authmethod'] = self.authMethod # we expect plaintext
      outjson['authdata']   = binary_to_hex(self.authData.serialize()) 
      
      return outjson


   #############################################################################
   def fromJSONMap(self, jsonMap, skipMagicCheck=False):
      ver   = jsonMap['version'] 
      magic = jsonMap['magicbytes'] 
      uniq  = jsonMap['id']
   
      # Issue a warning if the versions don't match
      if not ver == UNSIGNED_TX_VERSION:
         LOGWARN('Unserializing DPK of different version')
         LOGWARN('   USTX    Version: %d' % ver)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      # Check the magic bytes of the lockbox match
      if not magic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    USTX    Magic: ' + binary_to_hex(magic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')
   

      pub  = hex_to_binary(jsonMap['pubkeyhex'])
      comm =               jsonMap['keycomment']
      loc  = hex_to_binary(jsonMap['wltLocator'])
      meth =               jsonMap['authmethod']
      data = hex_to_binary(jsonMap['authdata'])

      authobj = NullAuthData().unserialize(data)

      self.setParams(pub, comm, loc, meth, authobj)
      
      return self


   #############################################################################
   def pprint(self):
      print 'pprint of DecoratedPublicKey is not implemented'
      





################################################################################
def computePromissoryID(ustxiList=None, dtxoTarget=None, feeAmt=None, 
                        dtxoChange=None, prom=None):

   if prom:
      ustxiList  = prom.ustxInputs
      dtxoTarget = prom.dtxoTarget
      feeAmt     = prom.feeAmt
      dtxoChange = prom.dtxoChange

   if not ustxiList:
      LOGERROR("Empty ustxiList in computePromissoryID")
      return None

   outptList = sorted([ustxi.outpoint.serialize() for ustxi in ustxiList])
   targStr  = dtxoTarget.binScript 
   targStr += int_to_binary(dtxoTarget.value, widthBytes=8)
   targStr += dtxoChange.binScript if dtxoChange else ''
   return binary_to_base58(hash256(''.join(outptList) + targStr))[:8]
   


################################################################################
################################################################################
class MultiSigPromissoryNote(AsciiSerializable):

   OBJNAME   = 'PromNote'
   BLKSTRING = 'PROMISSORY'
   EMAILSUBJ = 'Armory Promissory Note for Simulfunding - %s'
   EMAILBODY = """
               The chunk of text below describes how this wallet will 
               contribute to a simulfunding transaction.  In the lockbox
               manager, go to "Merge Promissory Notes" and then click on 
               "Import Promissory Note."  Copy and paste the block of text 
               into the import box, including the first and last lines.  
               You should receive a block of text like this from each party 
               funding this transaction."""


   EQ_ATTRS_SIMPLE = ['version', 'dtxoTarget', 'feeAmt', 'dtxoChange',
                      'promID', 'asciiID', 'promLabel']
   EQ_ATTRS_LISTS  = ['ustxInputs']



   #############################################################################
   def __init__(self, dtxoTarget=None, feeAmt=None, ustxInputs=None, 
                                    dtxoChange=None, promLabel=None,
                                    version=MULTISIG_VERSION):
      self.version     = MULTISIG_VERSION
      self.dtxoTarget  = dtxoTarget
      self.feeAmt      = feeAmt
      self.ustxInputs  = ustxInputs
      self.dtxoChange  = dtxoChange
      self.promID      = None
      self.asciiID     = None
      self.promLabel   = promLabel if promLabel else ''

      # We MIGHT use this object to simultaneously promise funds AND 
      # provide a key to include in the target multisig lockbox (which would 
      # save a round of exchanging data, if the use-case allows it)
      self.lockboxKey = ''

      if dtxoTarget is not None:
         self.setParams(dtxoTarget, feeAmt, dtxoChange, ustxInputs, 
                                                   promLabel, version)


   #############################################################################
   def setParams(self, dtxoTarget=None, feeAmt=None, dtxoChange=None,
                    ustxInputs=None, promLabel=None, version=MULTISIG_VERSION):
      
      # Set params will only overwrite with non-None data
      if dtxoTarget is not None:
         self.dtxoTarget = dtxoTarget

      if feeAmt is not None:
         self.feeAmt = feeAmt

      if dtxoChange is not None:
         self.dtxoChange = dtxoChange

      if ustxInputs is not None:
         self.ustxInputs = ustxInputs

      if promLabel is not None:
         self.promLabel = promLabel

      # Compute some other data members
      self.version = version
      self.magicBytes = MAGIC_BYTES

      self.promID  = computePromissoryID(prom=self)
      self.asciiID = self.promID  # need a common member name in all classes

      # Make sure that the change output matches expected, also set contribIDs
      totalInputs = 0
      for ustxi in self.ustxInputs:
         totalInputs += ustxi.value
         ustxi.contribID = self.promID

      changeAmt = totalInputs - (self.dtxoTarget.value + self.feeAmt)
      if changeAmt > 0:
         if not self.dtxoChange.value==changeAmt:
            LOGERROR('dtxoChange.value==%s, computed %s',
               coin2strNZS(self.dtxoChange.value), coin2strNZS(changeAmt))
            raise ValueError('Change output on prom note is unexpected')
      elif changeAmt < 0:
         LOGERROR('Insufficient prom inputs for payAmt and feeAmt')
         LOGERROR('Total inputs: %s', coin2strNZS(totalInputs))
         LOGERROR('(Amt, Fee)=(%s,%s)', coin2strNZS(self.dtxoTarget.value), 
                                              coin2strNZS(self.feeAmt))
         raise ValueError('Insufficient prom inputs for pay & fee')


   #############################################################################
   def setLockboxKey(self, binPubKey):
      keyPair = [binPubKey[0], len(binPubKey)] 
      if not keyPair in [['\x02', 33], ['\x03', 33], ['\x04', 65]]:
         LOGERROR('Invalid public key supplied')
         return False
      
      if keyPair[0] == '\x04':
         if not CryptoECDSA().VerifyPublicKeyValid(SecureBinaryData(binPubKey)):
            LOGERROR('Invalid public key supplied')
            return False

      self.lockboxKey = binPubKey[:]
      return True
      
      
   #############################################################################
   def serialize(self):

      if not self.dtxoTarget:
         LOGERROR('Cannot serialize uninitialized promissory note')
         return None

      if self.dtxoChange is None:
         serChange = ''
      else:
         serChange = self.dtxoChange.serialize()

      bp = BinaryPacker()
      bp.put(UINT32,       self.version)
      bp.put(BINARY_CHUNK, MAGIC_BYTES)
      bp.put(VAR_STR,      self.dtxoTarget.serialize())
      bp.put(VAR_STR,      serChange)
      bp.put(UINT64,       self.feeAmt)
      bp.put(VAR_INT,      len(self.ustxInputs))
      for ustxi in self.ustxInputs:
         bp.put(VAR_STR,      ustxi.serialize())

      bp.put(VAR_STR,      toBytes(self.promLabel))
      bp.put(VAR_STR,      self.lockboxKey)

      return bp.getBinaryString()

   #############################################################################
   def unserialize(self, rawData, expectID=None, skipMagicCheck=False):
      ustxiList = []
      
      bu = BinaryUnpacker(rawData)
      version     = bu.get(UINT32)
      magicBytes  = bu.get(BINARY_CHUNK, 4)
      target      = bu.get(VAR_STR)
      change      = bu.get(VAR_STR)
      feeAmt      = bu.get(UINT64)
      numUSTXI    = bu.get(VAR_INT)

      # Check the magic bytes of the lockbox match
      if not magicBytes == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    PromNote Magic: ' + binary_to_hex(magicBytes))
         LOGERROR('    Armory   Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')
      
      for i in range(numUSTXI):
         ustxiList.append( UnsignedTxInput().unserialize(bu.get(VAR_STR), skipMagicCheck=skipMagicCheck) )

      promLabel   = toUnicode(bu.get(VAR_STR))
      lockboxKey  = bu.get(VAR_STR)

      if not version==MULTISIG_VERSION:
         LOGWARN('Unserialing promissory note of different version')
         LOGWARN('   PromNote Version: %d' % version)
         LOGWARN('   Armory   Version: %d' % MULTISIG_VERSION)

      dtxoTarget = DecoratedTxOut().unserialize(target, skipMagicCheck=skipMagicCheck)
      dtxoChange = DecoratedTxOut().unserialize(change, skipMagicCheck=skipMagicCheck) if change else None

      self.setParams(dtxoTarget, feeAmt, dtxoChange, ustxiList, promLabel)

      if expectID and not expectID==self.promID:
         LOGERROR('Promissory note ID does not match expected')
         return None

      if len(lockboxKey)>0:
         self.setLockboxKey(lockboxKey)
      

      return self






   #############################################################################
   def toJSONMap(self, lite=False):
      outjson = {}
      outjson['version']      = self.version
      outjson['magicbytes']   = binary_to_hex(MAGIC_BYTES)
      outjson['id']           = self.asciiID

      #bp = BinaryPacker()
      #bp.put(UINT32,       self.version)
      #bp.put(BINARY_CHUNK, MAGIC_BYTES)
      #bp.put(VAR_STR,      self.dtxoTarget.serialize())
      #bp.put(VAR_STR,      serChange)
      #bp.put(UINT64,       self.feeAmt)
      #bp.put(VAR_INT,      len(self.ustxInputs))
      #for ustxi in self.ustxInputs:
         #bp.put(VAR_STR,      ustxi.serialize())
      #bp.put(VAR_STR,      toBytes(self.promLabel))
      #bp.put(VAR_STR,      self.lockboxKey)

      if self.dtxoChange is None:
         dtxoChangeMap = {}
      else:
         dtxoChangeMap = self.dtxoChange.toJSONMap()

      outjson['txouttarget'] = self.dtxoTarget.toJSONMap()
      outjson['txoutchange'] = dtxoChangeMap
      outjson['fee'] = self.feeAmt

      outjson['numinputs'] = len(self.ustxInputs)
      outjson['promlabel'] = self.promLabel
      outjson['lbpubkey'] = self.lockboxKey
      
      if not lite:
         outjson['inputs'] = []
         for ustxi in self.ustxInputs:
            outjson['inputs'].append(ustxi.toJSONMap())

      return outjson


   #############################################################################
   def fromJSONMap(self, jsonMap, skipMagicCheck=False):
      ver   = jsonMap['version'] 
      magic = jsonMap['magicbytes'] 
      uniq  = jsonMap['id']
   
      # Issue a warning if the versions don't match
      if not ver == UNSIGNED_TX_VERSION:
         LOGWARN('Unserializing Lockbox of different version')
         LOGWARN('   USTX    Version: %d' % ver)
         LOGWARN('   Armory  Version: %d' % UNSIGNED_TX_VERSION)

      # Check the magic bytes of the lockbox match
      if not magic == MAGIC_BYTES and not skipMagicCheck:
         LOGERROR('Wrong network!')
         LOGERROR('    USTX    Magic: ' + binary_to_hex(magic))
         LOGERROR('    Armory  Magic: ' + binary_to_hex(MAGIC_BYTES))
         raise NetworkIDError('Network magic bytes mismatch')


      targ = DecoratedTxOut().fromJSONMap(jsonMap['txouttarget'])
      fee  = jsonMap['fee']

      if len(jsonMap['txoutchange'])>0:
         chng = DecoratedTxOut().fromJSONMap(jsonMap['txoutchange'])
      else:
         chng = None

      nin = jsonMap['numinputs']
      inputs = []
      for i in range(nin):
         inputs.append(UnsignedTxInput().fromJSONMap(jsonMap['inputs'][i], skipMagicCheck))
         
      lbl = jsonMap['promlabel']
      self.setParams(targ, fee, chng, inputs, lbl)
      
      return self
      



   #############################################################################
   def pprint(self):

      print 'Promissory Note:'
      print '   Version     :', self.version
      print '   Unique ID   :', self.promID
      print '   Num Inputs  :', len(self.ustxInputs)
      print '   Target Addr :', self.dtxoTarget.getRecipStr()
      print '   Pay Amount  :', self.dtxoTarget.value
      print '   Fee Amount  :', self.feeAmt
      if self.dtxoChange is not None:
         print '   ChangeAddr  :', self.dtxoChange.getRecipStr()
      print '   LB Key      :', self.lockboxKey
      print '   LB Key Info :', self.promLabel


# Resolve circular dependencies here.
from armoryengine.UserAddressUtils import getDisplayStringForScript
