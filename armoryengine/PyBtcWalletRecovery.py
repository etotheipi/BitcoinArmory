################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from armoryengine.BinaryUnpacker import BinaryUnpacker
from armoryengine.ArmoryUtils import UINT32_MAX, KeyDataError, \
                                     verifyChecksum, int_to_bitset, \
                                     KILOBYTE, RightNowStr, hex_to_binary
from armoryengine.BinaryPacker import UINT16, UINT32, UINT64, INT64, \
                                      BINARY_CHUNK
from armoryengine.PyBtcAddress import PyBtcAddress
from armoryengine.PyBtcWallet import (PyBtcWallet, WLT_DATATYPE_KEYDATA, \
                                      WLT_DATATYPE_ADDRCOMMENT, \
                                      WLT_DATATYPE_TXCOMMENT, \
                                      WLT_DATATYPE_OPEVAL, \
                                      WLT_DATATYPE_DELETED, WLT_UPDATE_ADD, \
                                      getSuffixedPath)
from CppBlockUtils import SecureBinaryData, CryptoECDSA, CryptoAES, BtcWallet 
import os
import shutil
from time import sleep, ctime
from armoryengine.ArmoryUtils import AllowAsync, emptyFunc, LOGEXCEPT, \
                                     LOGINFO, LOGERROR, SECP256K1_ORDER, \
                                     binary_to_int, BIGENDIAN, int_to_binary, \
                                     binary_to_hex, enum, HMAC256


#                      0          1        2       3       4        5 
RECOVERMODE = enum('NotSet', 'Stripped', 'Bare', 'Full', 'Meta', 'Check')


class InvalidEntry(Exception): pass

class PyBtcWalletRecovery(object):
   """
   Fail safe wallet recovery tool. Reads a wallet, verifies and extracts 
   sensitive data to a new file.
   """  
   
   def __init__(self):
      """
      Set of lists holding various errors at given indexes. Used at the end of 
      the recovery process to compile a wallet specific log of encountered
      inconsistencies
      """
      self.byteError = [] #byte errors
      self.brokenSequence = [] #inconsistent address entry order in the file
      self.sequenceGaps = [] #gaps in key pair chain
      self.forkedPublicKeyChain = [] #for public keys: (N-1)*chaincode != N
      self.chainCodeCorruption = [] #addr[N] chaincode != addr[0] chaincode
      self.invalidPubKey = [] #pub key isnt a valid EC point
      self.missingPubKey = [] #addr[N] has no pub key
      self.hashValMismatch = [] #addrStr20 doesnt match hashVal entry in file
      self.unmatchedPair = [] #private key doesnt yield public key
      self.importedErr = [] #all imported keys related errors
      self.negativeImports = [] #lists forked imports in wallet
      
      #inconsistent private keys as P/HMAC512(rootKey, 'LogMult') mod N
      self.privKeyMultipliers = []
      
      """
      Object wide identifiers. To make sure certain sensitive objects are 
      deleted after us, they are only defined within ProcessWallet's scope 
      """
      self.newwalletPath = None
      self.WO = False
      self.UIreport = ''
      self.UID = ''
      self.labelName = ''
      self.WalletPath = ''

      self.pybtcaddrSize = len(PyBtcAddress().serialize())
      
      """
      Modes:
         1) Stripped: Only recover the root key and chaincode (it all sits in 
         the header). As fail safe as it gets.

         2) Bare: Recover root key, chaincode and valid private/public key 
         pairs. Verify integrity of the wallet and consistency of all entries 
         encountered. Skips comments, unprocessed public keys and otherwise 
         corrupted data without attempting to fix it.

         3) Full: Recovers as much data as possible from the wallet.

         4) Meta: Get all labels and comment entries from the wallet, return as 
         list
         
         5) Check: checks wallet for consistency. Does not yield a recovered 
         file, does not enforce unlocking encrypted wallets.

         returned values:
         -1: invalid path or file isn't a wallet

         In meta mode, a dict is returned holding all comments and labels in 
         the wallet
      """
      
      self.smode = RECOVERMODE.NotSet
      
   ###########################################################################
   def BuildLogFile(self, errorCode, Progress, returnError=False, nErrors=0):
      """
      The recovery function has ended and called this. Review the analyzed 
      data, build a log and return negative values if the recovery couldn't 
      complete
      """
      
      '''
      error codes:
      0 - no errors in wallet
      1 - found errors, fixed them
      <0 - error prcoessing wallet, read description below
      '''

      self.strOutput = []
      
      self.UIreport = self.UIreport + '<b>- Building log file...</b><br>'
      Progress(self.UIreport)

      if errorCode < 0:
         if errorCode == -1:
            errorstr = \
               'ERROR: Invalid path, or file is not a valid Armory wallet\r\n'
         elif errorCode == -2:
            errorstr = \
               'ERROR: file I/O failure. Do you have proper credentials?\r\n'
         elif errorCode == -3:
            errorstr = \
               'ERROR: This wallet file is for another network/blockchain\r\n'
         elif errorCode == -4:
            errorstr = \
               'ERROR: invalid or missing passphrase for encrypted wallet\r\n'
         elif errorCode == -10:
            errorstr = 'ERROR: no kdf parameters available\r\n'
         elif errorCode == -12:
            errorstr = 'ERROR: failed to unlock root key\r\n'

         self.strOutput.append('   %s' % (errorstr))

         self.UIreport = self.UIreport + errorstr
         Progress(self.UIreport)
         return self.FinalizeLog(errorCode, Progress, returnError)
      
            
      if returnError == 'Dict':
         errors = {}
         errors['byteError'] = self.byteError
         errors['brokenSequence'] = self.brokenSequence
         errors['sequenceGaps'] = self.sequenceGaps
         errors['forkedPublicKeyChain'] = self.forkedPublicKeyChain
         errors['chainCodeCorruption'] = self.chainCodeCorruption
         errors['invalidPubKey'] = self.invalidPubKey
         errors['missingPubKey'] = self.missingPubKey
         errors['hashValMismatch'] = self.hashValMismatch
         errors['unmatchedPair'] = self.unmatchedPair
         errors['misc'] = self.misc
         errors['importedErr'] = self.importedErr
         errors['negativeImports'] = self.negativeImports
         errors['nErrors'] = nErrors
         errors['privMult'] = self.privKeyMultipliers
         
         return errors
      
      
      if self.newwalletPath != None:
         self.LogPath = self.newwalletPath + ".log"
      else:
         self.LogPath = self.WalletPath + ".log"
      basename = os.path.basename(self.WalletPath)
      
      if self.smode == RECOVERMODE.Check:
         self.strOutput.append('Checking wallet %s (ID: %s) on %s \r\n' % \
                              ('\'' + self.labelName + '\'' \
                               if len(self.labelName) != 0 else basename, \
                               self.UID, ctime()))
      else:
         self.strOutput.append('Analyzing wallet %s (ID: %s) on %s \r\n' % \
                              ('\'' + self.labelName + '\'' if \
                               len(self.labelName) != 0 else basename, \
                               self.UID, ctime()))
         self.strOutput.append('Using recovery mode: %d\r\n' % (self.smode))

      if self.WO:
         self.strOutput.append('Wallet is Watch Only\r\n')
      else:
         self.strOutput.append('Wallet contains private keys ')
         if self.useEnc == 0:
            self.strOutput.append('and doesn\'t use encryption\r\n')
         else:
            self.strOutput.append('and uses encryption\r\n')

      # If all we have is these logs, should know num used, if avail
      self.strOutput.append('Highest used index: %d\r\n' % self.highestUsed)


      if self.smode == RECOVERMODE.Stripped and not self.WO:
         self.strOutput.append('   Recovered root key and chaincode, stripped recovery done.')
         return self.FinalizeLog(errorCode, Progress, returnError)

      self.strOutput.append('The wallet file is %d bytes, of which %d bytes were read\r\n' % \
                             (self.fileSize, self.dataLastOffset))
      self.strOutput.append('%d chain addresses, %d imported keys and %d comments were found\r\n' % \
                            (self.naddress, self.nImports, self.ncomments))

      nErrors = 0
      #### chained keys
      self.strOutput.append('Found %d chained address entries\r\n' \
                            % (self.naddress))

      if len(self.byteError) == 0:
         self.strOutput.append('No byte errors were found in the wallet file\r\n')
      else:
         nErrors = nErrors + len(self.byteError)
         self.strOutput.append('%d byte errors were found in the wallet file:\r\n' % (len(self.byteError)))
         for i in range(0, len(self.byteError)):
            self.strOutput.append('   chainIndex %s at file offset %s\r\n' \
                              % (self.byteError[i][0], self.byteError[i][1]))


      if len(self.brokenSequence) == 0:
         self.strOutput.append('All chained addresses were arranged sequentially in the wallet file\r\n')
      else:
         #nErrors = nErrors + len(self.brokenSequence)
         self.strOutput.append('The following %d addresses were not arranged sequentially in the wallet file:\r\n' % \
                               (len(self.brokenSequence)))
         for i in range(0, len(self.brokenSequence)):
            self.strOutput.append('   chainIndex %s at file offset %s\r\n' % \
                        (self.brokenSequence[i][0], self.brokenSequence[i][1]))

      if len(self.sequenceGaps) == 0:
         self.strOutput.append('There are no gaps in the address chain\r\n')
      else:
         nErrors = nErrors + len(self.sequenceGaps)
         self.strOutput.append('Found %d gaps in the address chain:\r\n' % \
                               (len(self.sequenceGaps)))
         for i in range(0, len(self.sequenceGaps)):
            self.strOutput.append('   from chainIndex %s to %s\r\n' % \
                           (self.sequenceGaps[i][0], self.sequenceGaps[i][1]))

      if len(self.forkedPublicKeyChain) == 0:
         self.strOutput.append('No chained address fork was found\r\n')
      else:
         nErrors = nErrors + len(self.forkedPublicKeyChain)
         self.strOutput.append('Found %d forks within the address chain:\r\n' \
                               % (len(self.forkedPublicKeyChain)))
         for i in range(0, len(self.forkedPublicKeyChain)):
            self.strOutput.append('   at chainIndex %s, file offset %s\r\n' \
                                  % (self.forkedPublicKeyChain[i][0], \
                                     self.forkedPublicKeyChain[i][1]))

      if len(self.chainCodeCorruption) == 0:
         self.strOutput.append('No chaincode corruption was found\r\n')
      else:
         nErrors = nErrors + len(self.chainCodeCorruption)
         self.strOutput.append(' \
            Found %d instances of chaincode corruption:\r\n' % \
            (len(self.chainCodeCorruption)))
         for i in range(0, len(self.chainCodeCorruption)):
            self.strOutput.append('   at chainIndex %s, file offset %s\r\n' % (self.chainCodeCorruption[i][0], \
                              self.chainCodeCorruption[i][1]))

      if len(self.invalidPubKey) == 0:
         self.strOutput.append('All chained public keys are valid EC points\r\n')
      else:
         nErrors = nErrors + len(self.invalidPubKey)
         self.strOutput.append('%d chained public keys are invalid EC points:\r\n' % (len(self.invalidPubKey)))
         for i in range(0, len(self.invalidPubKey)):
            self.strOutput.append('   at chainIndex %s, file offset %s' % \
                                  (self.invalidPubKey[i][0], \
                                   self.invalidPubKey[i][1]))

      if len(self.missingPubKey) == 0:
         self.strOutput.append('No chained public key is missing\r\n')
      else:
         nErrors = nErrors + len(self.missingPubKey)
         self.strOutput.append('%d chained public keys are missing:\r\n' % \
                               (len(self.missingPubKey)))
         for i in range(0, len(self.missingPubKey)):
            self.strOutput.append('   at chainIndex %s, file offset %s' % \
                                  (self.missingPubKey[i][0], \
                                   self.missingPubKey[i][1]))

      if len(self.hashValMismatch) == 0:
         self.strOutput.append('All entries were saved under their matching hashVal\r\n')
      else:
         nErrors = nErrors + len(self.hashValMismatch)
         self.strOutput.append('%d address entries were saved under an erroneous hashVal:\r\n' % \
                                (len(self.hashValMismatch)))
         for i in range(0, len(self.hashValMismatch)):
            self.strOutput.append('   at chainIndex %s, file offset %s\r\n' \
                                  % (self.hashValMismatch[i][0], \
                                     self.hashValMismatch[i][1]))

      if not self.WO:
         if len(self.unmatchedPair) == 0:
            self.strOutput.append('All chained public keys match their respective private keys\r\n')
         else:
            nErrors = nErrors + len(self.unmatchedPair)
            self.strOutput.append('%d public keys do not match their respective private key:\r\n' % \
                                  (len(self.unmatchedPair)))
            for i in range(0, len(self.unmatchedPair)):
               self.strOutput.append('   at chainIndex %s, file offset %s\r\n' \
                                     % (self.unmatchedPair[i][0], 
                                        self.unmatchedPair[i][1]))

      if len(self.misc) > 0:
         nErrors = nErrors + len(self.misc)
         self.strOutput.append('%d miscalleneous errors were found:\r\n' % \
                               (len(self.misc)))
         for i in range(0, len(self.misc)):
            self.strOutput.append('   %s\r\n' % self.misc[i])

      #### imported keys
      self.strOutput.append('Found %d imported address entries\r\n' % \
                            (self.nImports))

      if self.nImports > 0:
         if len(self.importedErr) == 0:
            self.strOutput.append('No errors were found within the imported address entries\r\n')
         else:
            nErrors = nErrors + len(self.importedErr)
            self.strOutput.append('%d errors were found within the imported address entries:\r\n' % \
                                  (len(self.importedErr)))
            for i in range(0, len(self.importedErr)):
               self.strOutput.append('   %s\r\n' % (self.importedErr[i]))
               
      if len(self.privKeyMultipliers) > 0:
         self.strOutput.append('Inconsistent private keys were found!\r\n')
         self.strOutput.append('Logging Multipliers (no private key data):\r\n')
         
         for i in range(0, len(self.privKeyMultipliers)):
            self.strOutput.append('   %s\r\n' % (self.privKeyMultipliers[i]))

      ####TODO: comments error log
      self.strOutput.append('%d errors were found\r\n' % (nErrors))
      #self.UIreport += '<b%s>- %d errors were found</b><br>' % \
      #( ' style="color: red;"' if nErrors else '', nErrors)
      return self.FinalizeLog(errorCode, Progress, returnError)
      

   ############################################################################
   def FinalizeLog(self, errorcode, Progress, returnError=False):

      self.EndLog = ''

      if errorcode < 0:
         self.strOutput.append( \
                  'Recovery failed: error code %d\r\n\r\n\r\n' % (errorcode))

         self.EndLog = '<b>- Recovery failed: error code %d</b><br>' % \
                        (errorcode)
         Progress(self.UIreport + self.EndLog)
         return errorcode
      else:

         self.strOutput.append('Recovery done\r\n\r\n\r\n')            
         self.EndLog = self.EndLog + '<b>- Recovery done</b><br>'
         if self.newwalletPath: self.EndLog = self.EndLog + \
                        '<br>Recovered wallet saved at:<br>- %s<br>' % \
                        (self.newwalletPath)
         Progress(self.UIreport + self.EndLog)

         self.strOutput.append('\r\n\r\n\r\n')

      if not returnError:      
         self.EndLog = self.EndLog + '<br>Recovery log saved at:<br>- %s<br>' \
                                      % (self.LogPath)
         Progress(self.UIreport + self.EndLog, True)  
             
         self.logfile = open(self.LogPath, 'ab')
         
         for s in self.strOutput:
            self.logfile.write(s)
         
         self.logfile.close()

         return errorcode
      else:
         return [errorcode, self.strOutput]

   ############################################################################
   def RecoverWallet(self, WalletPath, Passphrase=None, Mode=RECOVERMODE.Bare,
                     returnError=False, Progress=emptyFunc):

      return self.ProcessWallet(WalletPath, None, Passphrase, Mode, None, 
                                returnError, async=True, Progress=Progress)

   ############################################################################
   @AllowAsync
   def ProcessWallet(self, WalletPath=None, Wallet=None, Passphrase=None, 
                     Mode=RECOVERMODE.Stripped, prgAt=None, 
                     returnError=False, Progress=emptyFunc):
      
      self.__init__()

      if not WalletPath:
         if not Wallet: return -1
         WalletPath = Wallet.walletPath
      
      self.WalletPath = WalletPath      
      
      RecoveredWallet = None
      SecurePassphrase = None
      
      self.naddress = 0
      #holds address chain sequentially, ordered by chainIndex, as lists: 
      #[addrEntry, hashVal, naddress, byteLocation, rawData]
      #validChainDict uses the same list format, and is used to hold computed
      #valid chain address entries
      addrDict = {} 
      validChainDict = {}

      self.nImports = 0
      #holds imported address, by order of apparition, as lists: 
      #[addrEntry, hashVal, byteLocation, rawData]
      importedDict = {} 

      self.ncomments = 0
      #holds all comments entries, as lists: [rawData, hashVal, dtype]
      commentDict = {} 
      
      #in meta mode, the wallet's short and long labels are saved in entries 
      #shortLabel and longLabel, pointing to a single str object

      rmode      = Mode
      self.smode = Mode
      if Mode == RECOVERMODE.Meta:
         self.WO = True

      self.fileSize=0
      if not os.path.exists(WalletPath): 
         return self.BuildLogFile(-1, Progress, returnError)
      else: self.fileSize = os.path.getsize(WalletPath)

      toRecover = PyBtcWallet()
      toRecover.walletPath = WalletPath

      #consistency check
      try:
         toRecover.doWalletFileConsistencyCheck()
      except: 
         #I expect 99% of errors raised here would be by Python's "os" module
         #failing an I/O operations, mainly for lack of credentials.
         LOGEXCEPT('')
         return self.BuildLogFile(-2, Progress, returnError)

      #fetch wallet content
      wltfile = open(WalletPath, 'rb')
      wltdata = BinaryUnpacker(wltfile.read())
      wltfile.close()

      #unpack header
      try:
         returned = toRecover.unpackHeader(wltdata)
      except: 
         LOGEXCEPT('')
         #Raises here come from invalid header parsing, meaning the file isn't 
         #an Armory wallet to begin with, or the header is fubar 
         return self.BuildLogFile(-1, Progress, returnError) 

      self.UID = toRecover.uniqueIDB58
      self.labelName = toRecover.labelName
      self.highestUsed = toRecover.highestUsedChainIndex
      #TODO: try to salvage broken header
      #      compare uniqueIDB58 with recovered wallet
      

      self.UIreport = '<b>Analyzing wallet:</b> %s<br>' % (toRecover.labelName \
                       if len(toRecover.labelName) != 0 \
                       else os.path.basename(WalletPath))
      Progress(self.UIreport)
      
      if returned < 0: return self.BuildLogFile(-3, Progress, returnError)

      self.useEnc=0
      rootAddr = toRecover.addrMap['ROOT']

      #check for private keys (watch only?)
      if toRecover.watchingOnly is True:
         self.WO = True

      if not self.WO:
         #check if wallet is encrypted
         if toRecover.isLocked==True and rmode != RECOVERMODE.Meta:
            '''
            Passphrase can one of be 3 things:
               1) str
               2) SecureBinaryData
               3) a function that will return the passphrase (think user prompt)
            '''
            if isinstance(Passphrase, str):
               SecurePassphrase = SecureBinaryData(Passphrase)
               Passphrase = ''
            elif isinstance(Passphrase, SecureBinaryData):
                  SecurePassphrase = Passphrase.copy()
            elif hasattr(Passphrase, '__call__'):
               getPassphrase = Passphrase(toRecover)
               
               if isinstance(getPassphrase, SecureBinaryData):
                  SecurePassphrase = getPassphrase.copy()
                  getPassphrase.destroy()                       
               else:
                  if rmode==RECOVERMODE.Check: 
                     self.WO = True
                  else: 
                     return self.BuildLogFile(-4, Progress, returnError)
            else:
               if rmode==RECOVERMODE.Check:
                  self.WO = True
               else: 
                  return self.BuildLogFile(-4, Progress, returnError)

         #if the wallet uses encryption, unlock ROOT and verify it
         if toRecover.isLocked and not self.WO:
            self.useEnc=1
            if not toRecover.kdf:
               SecurePassphrase.destroy() 
               return self.BuildLogFile(-10, Progress, returnError)

            secureKdfOutput = toRecover.kdf.DeriveKey(SecurePassphrase)

            if not toRecover.verifyEncryptionKey(secureKdfOutput):
               SecurePassphrase.destroy()
               secureKdfOutput.destroy()
               return self.BuildLogFile(-4, Progress, returnError)

            #DlgUnlockWallet may have filled kdfKey. Since this code can be 
            #called with no UI and just the passphrase, gotta make sure this 
            #member is cleaned up before setting it
            if isinstance(toRecover.kdfKey, SecureBinaryData): 
               toRecover.kdfKey.destroy()
            toRecover.kdfKey = secureKdfOutput

            try:
               rootAddr.unlock(toRecover.kdfKey)
            except:
               LOGEXCEPT('')
               SecurePassphrase.destroy()
               return self.BuildLogFile(-12, Progress, returnError)
         else:
            SecurePassphrase = None

         #stripped recovery, we're done
         if rmode == RECOVERMODE.Stripped:
            RecoveredWallet = self.createRecoveredWallet(toRecover, rootAddr, \
                                       SecurePassphrase, Progress, returnError)
            rootAddr.lock()   
            if SecurePassphrase: SecurePassphrase.destroy()
            
            if not isinstance(RecoveredWallet, PyBtcWallet):  
               return RecoveredWallet
            
            if isinstance(toRecover.kdfKey, SecureBinaryData): 
               toRecover.kdfKey.destroy()
            if isinstance(RecoveredWallet.kdfKey, SecureBinaryData): 
               RecoveredWallet.kdfKey.destroy()
            
            #stripped recovery, we are done
            return self.BuildLogFile(1, Progress, returnError) 

      if rmode == RECOVERMODE.Meta:
         commentDict["shortLabel"] = toRecover.labelName
         commentDict["longLabel"]  = toRecover.labelDescr

      '''
      address entries may not be saved sequentially. To check the address 
      chain is valid, all addresses will be unserialized and saved by 
      chainIndex in addrDict. Then all addresses will be checked for 
      consistency and proper chaining. Imported private keys and comments 
      will be added at the tail of the file.
      '''
         
      UIupdate = ""
      self.misc = [] #miscellaneous errors
      self.rawError = [] #raw binary errors'
      
      if prgAt:
         prgAt_in = prgAt[0]
         prgAt[0] = prgAt_in +prgAt[1]*0.01 

      
      #move on to wallet body
      toRecover.lastComputedChainIndex = -UINT32_MAX
      toRecover.lastComputedChainAddr160  = None
      while wltdata.getRemainingSize()>0:
         byteLocation = wltdata.getPosition()


         UIupdate =  '<b>- Reading wallet:</b>   %0.1f/%0.1f kB<br>' % \
            (float(byteLocation)/KILOBYTE, float(self.fileSize)/KILOBYTE)
         if Progress(self.UIreport + UIupdate) == 0:
            if SecurePassphrase: SecurePassphrase.destroy()
            if toRecover.kdfKey: toRecover.kdfKey.destroy()
            rootAddr.lock()
            return 0

         newAddr = None
         try:
            dtype, hashVal, rawData = toRecover.unpackNextEntry(wltdata)
         except NotImplementedError:
            self.misc.append('Found OPEVAL data entry at offest: %d' % \
                             (byteLocation))
            pass
         except:
            LOGEXCEPT('')
            #Error in the binary file content. Try to skip an entry size amount
            #of bytes to find a valid entry.
            self.rawError.append('Raw binary error found at offset: %d' \
                                  % (byteLocation))

            dtype, hashVal, rawData, dataList = self.LookForFurtherEntry( \
                                                      wltdata, byteLocation)

            if dtype is None:
               #could not find anymore valid data
               self.rawError.append('Could not find anymore valid data past \
                                                offset: %d' % (byteLocation))
               break

            byteLocation = dataList[1]
            self.rawError.append('   Found a valid data entry at offset: %d' \
                                 % (byteLocation))

            if dataList[0] == 0:
               #found an address entry, but it has checksum errors
               newAddr = dataList[2]

         if dtype==WLT_DATATYPE_KEYDATA:
            if rmode != RECOVERMODE.Meta:
               if newAddr is None:
                  newAddr = PyBtcAddress()
                  try:
                     newAddr.unserialize(rawData)
                  except:
                     LOGEXCEPT('')
                     #unserialize error, try to recover the entry
                     self.rawError.append( \
                        '   Found checksum errors in address entry starting at offset: %d' \
                        % (byteLocation))
                     
                     try:
                        newAddr, chksumError = \
                              self.addrEntry_unserialize_recover(rawData)
                        self.rawError.append('   Recovered damaged entry')
                     except:
                        LOGEXCEPT('')
                        #failed to recover the entry
                        self.rawError.append( \
                              '   Could not recover damaged entry')
                        newAddr = None

               if newAddr is not None:
                  newAddr.walletByteLoc = byteLocation + 21

                  if newAddr.useEncryption:
                     newAddr.isLocked = True

                  #save address entry count in the file, to check 
                  #for entry sequence
                  if newAddr.chainIndex > -2 :
                     addrDict[newAddr.chainIndex] = \
                        [newAddr, hashVal, self.naddress, byteLocation, rawData]
                     self.naddress = self.naddress +1
                  else:
                     importedDict[self.nImports] = \
                        [newAddr, hashVal, byteLocation, rawData]
                     self.nImports = self.nImports +1

            else: self.naddress = self.naddress +1


         elif dtype in (WLT_DATATYPE_ADDRCOMMENT, WLT_DATATYPE_TXCOMMENT):
            #if rmode > 2:
            if rmode in [RECOVERMODE.Full, RECOVERMODE.Meta, RECOVERMODE.Check]:
               commentDict[self.ncomments] = [rawData, hashVal, dtype]
               self.ncomments = self.ncomments +1

         elif dtype==WLT_DATATYPE_OPEVAL:
            self.misc.append('Found OPEVAL data entry at offest: %d' % \
                             (byteLocation))
            pass
         elif dtype==WLT_DATATYPE_DELETED:
            pass
         else:
            self.misc.append('Found unknown data entry type at offset: %d' % \
                             (byteLocation))
            #TODO: try same trick as recovering from unpack errors?

      self.dataLastOffset = wltdata.getPosition()
      UIupdate = '<b>- Reading wallet:</b>   %0.1f/%0.1f kB<br>' % \
         (float(self.dataLastOffset)/KILOBYTE, float(self.fileSize)/KILOBYTE)
      self.UIreport = self.UIreport + UIupdate

      #verify the root address is derived from the root key
      if not self.WO:
         testroot = PyBtcAddress().createFromPlainKeyData( \
                                   rootAddr.binPrivKey32_Plain, None, None, \
                                   generateIVIfNecessary=True)
         if rootAddr.addrStr20 != testroot.addrStr20:
            self.rawError.append( \
                           '   root address was not derived from the root key')
   
   
         #verify chainIndex 0 was derived from the root address
         firstAddr = rootAddr.extendAddressChain(toRecover.kdfKey)
         if firstAddr.addrStr20 != addrDict[0][0].addrStr20:
            self.rawError.append('   chainIndex 0 was not derived from the \
                                  root address')

         testroot.binPrivKey32_Plain.destroy()

      if rmode != RECOVERMODE.Meta:
         currSequence = addrDict[0][2]
         chaincode = addrDict[0][0].chaincode.toHexStr()
      else:
         currSequence = None
         chaincode = None
         commentDict['naddress'] = self.naddress
         self.naddress = 0
         commentDict['ncomments'] = self.ncomments

      if prgAt:
         prgTotal = len(addrDict) + len(importedDict) + len(commentDict)



      #chained key pairs. for rmode is 4, no need to skip this part, 
      #naddress will be 0
      n=0
      for i in addrDict:
         entrylist = []
         entrylist = list(addrDict[i])
         newAddr = entrylist[0]
         rawData = entrylist[4]
         byteLocation = entrylist[3]

         n = n+1
         UIupdate = '<b>- Processing address entries:</b>   %d/%d<br>' % \
                     (n, self.naddress)
         if Progress(self.UIreport + UIupdate) == 0:
            if SecurePassphrase: SecurePassphrase.destroy()
            if toRecover.kdfKey: toRecover.kdfKey.destroy()
            rootAddr.lock()
            return 0
         if prgAt:
            prgAt[0] = prgAt_in + (0.01 + 0.99*n/prgTotal)*prgAt[1]
         
         # Fix byte errors in the address data
         fixedAddrData = newAddr.serialize()
         if not rawData==fixedAddrData:
            self.byteError.append([newAddr.chainIndex, byteLocation])
            fixedAddr = PyBtcAddress()
            fixedAddr.unserialize(fixedAddrData)
            newAddr = PyBtcAddress()
            newAddr.unserialize(fixedAddrData)
            entrylist[0] = newAddr
            addrDict[i] = entrylist

         #check public key is a valid EC point
         if newAddr.hasPubKey():
            if not CryptoECDSA().VerifyPublicKeyValid(newAddr.binPublicKey65):
               self.invalidPubKey.append([newAddr.chainIndex, byteLocation])
         else: self.missingPubKey.append([newAddr.chainIndex, byteLocation])

         #check chaincode consistency
         newCC = newAddr.chaincode.toHexStr()
         if newCC != chaincode:
            self.chainCodeCorruption.append([newAddr.chainIndex, byteLocation])

         #check the address entry sequence
         nextSequence = entrylist[2]
         if nextSequence != currSequence:
            if (nextSequence - currSequence) != 1:
               self.brokenSequence.append([newAddr.chainIndex, byteLocation])
         currSequence = nextSequence

         #check for gaps in the sequence
         isPubForked = False
         if newAddr.chainIndex > 0:
            seq = newAddr.chainIndex -1
            prevEntry = []
            while seq > -1:
               if seq in addrDict: break
               seq = seq -1

            prevEntry = list(addrDict[seq])
            prevAddr = prevEntry[0]

            gap = newAddr.chainIndex - seq
            if gap > 1:
               self.sequenceGaps.append([seq, newAddr.chainIndex])

            #check public address chain
            if newAddr.hasPubKey():
               cid = 0
               extended = prevAddr.binPublicKey65
               while cid < gap:
                  extended = CryptoECDSA().ComputeChainedPublicKey( \
                                                extended, prevAddr.chaincode)
                  cid = cid +1

               if extended.toHexStr() != newAddr.binPublicKey65.toHexStr():
                  self.forkedPublicKeyChain.append([newAddr.chainIndex, \
                                                    byteLocation])
                  isPubForked = True


         if not self.WO:
            #not a watch only wallet, check private/public key chaining and 
            #integrity

            if newAddr.useEncryption != toRecover.useEncryption:
               if newAddr.useEncryption:
                  self.misc.append('Encrypted address entry in a non encrypted \
                                    wallet at chainIndex %d in wallet %s' % \
                                    (newAddr.chainIndex, os.path.basename( \
                                     WalletPath)))
               else:
                  self.misc.append('Unencrypted address entry in an encrypted wallet at chainIndex %d in wallet %s' % \
                                    (newAddr.chainIndex, os.path.basename( \
                                     WalletPath)))                  
            
            keymismatch=0
            """
            0: public key matches private key
            1: public key doesn't match private key
            2: private key is missing (encrypted)
            3: public key is missing
            4: private key is missing (unencrypted)
            """
            if not newAddr.hasPrivKey():
               #entry has no private key
               keymismatch=2
                  
               if not newAddr.useEncryption:
                  #uncomputed private key in a non encrypted wallet? 
                  #definitely not supposed to happen
                  keymismatch = 4 
                  self.misc.append('Uncomputed private key in unencrypted wallet at chainIndex %d in wallet %s' \
                                    % (newAddr.chainIndex, os.path.basename \
                                    (WalletPath)))
               else:
                  self.misc.append('Missing private key is not flagged for computation at chainIndex %d in wallet %s'\
                                    % (newAddr.chainIndex, os.path.basename \
                                    (WalletPath)))
                                       
            else:
               if newAddr.createPrivKeyNextUnlock:
                  #have to build the private key on unlock; we can use prevAddr
                  #for that purpose, used to chain the public key off of
                  newAddr.createPrivKeyNextUnlock_IVandKey[0] = \
                                             prevAddr.binInitVect16.copy()
                  newAddr.createPrivKeyNextUnlock_IVandKey[1] = \
                                             prevAddr.binPrivKey32_Encr.copy()
   
                  newAddr.createPrivKeyNextUnlock_ChainDepth = \
                                       newAddr.chainIndex - prevAddr.chainIndex


            #unlock if necessary
            if keymismatch == 0:
               if newAddr.isLocked:
                  try:
                     newAddr.unlock(toRecover.kdfKey)
                     keymismatch = 0
                  except KeyDataError:
                     keymismatch = 1
            
            isPrivForked = False
            validAddr = None
            if newAddr.chainIndex > 0 and keymismatch != 2:
               #if the wallet has the private key, derive it from the 
               #chainIndex and compare. If they mismatch, save the bad 
               #private key as -3 -chainIndex in the saved wallet. Additionally, 
               #derive the private key in case it is missing (keymismatch==4)
               
               gap = newAddr.chainIndex
               prevkey = None
               
               if prevAddr.useEncryption:
                  if prevAddr.binPrivKey32_Encr.getSize() == 32:
                     gap = newAddr.chainIndex - prevAddr.chainIndex
                     prevkey = CryptoAES().DecryptCFB( \
                                     prevAddr.binPrivKey32_Encr, \
                                     SecureBinaryData(toRecover.kdfKey), \
                                     prevAddr.binInitVect16)
               else:
                  if prevAddr.binPrivKey32_Plain.getSize() == 32:
                     gap = newAddr.chainIndex - prevAddr.chainIndex
                     prevkey = prevAddr.binPrivKey32_Plain
                  
               if gap == newAddr.chainIndex:
                  #coudln't get a private key from prevAddr, 
                  #derive from root addr
                  prevAddr = addrDict[0][0]
                  
                  if prevAddr.useEncryption:
                     prevkey = CryptoAES().DecryptCFB( \
                                     prevAddr.binPrivKey32_Encr, \
                                     SecureBinaryData(toRecover.kdfKey), \
                                     prevAddr.binInitVect16)
                  else:
                     prevkey = prevAddr.binPrivKey32_Plain                  
                  
               for t in range(0, gap):
                  prevkey = prevAddr.safeExtendPrivateKey( \
                                                prevkey, \
                                                prevAddr.chaincode)                  
               
               if keymismatch != 4:
                  if prevkey.toHexStr() != \
                     newAddr.binPrivKey32_Plain.toHexStr():
                     """
                     Special case: The private key saved in the wallet doesn't 
                     match the extended private key.
                     
                     2 things to do:
                     1) Save the current address entry as an import, 
                        as -chainIndex -3
                     2) After the address entry has been analyzed, replace it 
                        with a valid one, to keep on checking the chain.
                     """
                     isPrivForked = True
                     validAddr = newAddr.copy()
                     validAddr.binPrivKey32_Plain = prevkey.copy()
                     validAddr.binPublicKey65 = CryptoECDSA().ComputePublicKey(\
                                                   validAddr.binPrivKey32_Plain)
                     validAddr.chainCode = prevAddr.chaincode.copy()
                     validAddr.keyChanged = True
                     
                     if validAddr.useEncryption:
                        validAddr.keyChanged = True
                        validAddr.lock(secureKdfOutput=toRecover.kdfKey)
                     
                     if isPubForked is not True:
                        self.forkedPublicKeyChain.append([newAddr.chainIndex, \
                                                    byteLocation])                        
               
                  if isPrivForked is False:
                     chID = newAddr.chainIndex
                     validchID = 0
                     for ids in range(chID -1, 0, -1):
                        if ids in validChainDict:
                           validchID = ids 
                           break 
                     
                     validChainAddr = validChainDict[validchID]
                     if validChainAddr.useEncryption:
                        validPrivKey = CryptoAES().DecryptCFB( \
                                     validChainAddr.binPrivKey32_Encr, \
                                     SecureBinaryData(toRecover.kdfKey), \
                                     validChainAddr.binInitVect16)
                     else: 
                        validPrivKey = validChainAddr.binPrivKey32_Plain.copy()
                                     
                     gap = chID - validchID
                     for t in range(0, gap):
                        validPrivKey = validChainAddr.safeExtendPrivateKey( \
                                                      validPrivKey, \
                                                      validChainAddr.chaincode)
                        
                     if prevkey.toHexStr() != validPrivKey.toHexStr():
                        isPrivForked = True
                        validAddr = newAddr.copy()
                        validAddr.binPrivKey32_Plain = validPrivKey.copy()
                        validAddr.binPublicKey65 = \
                                 CryptoECDSA().ComputePublicKey( \
                                 validAddr.binPrivKey32_Plain)
                                 
                        validAddr.chainCode = validChainAddr.chaincode.copy()                        
                        
                        if validAddr.useEncryption:
                           validAddr.keyChanged = True
                           validAddr.lock(secureKdfOutput=toRecover.kdfKey)
                                                                                                 
                     validPrivKey.destroy()   
                                       
               else:
                  newAddr.binPrivKey32_Plain = prevkey.copy()

               prevkey.destroy()
            
            if validAddr is None:
               validChainDict[i] = newAddr
            else:
               validChainDict[i] = validAddr
            
            
            #deal with mismatch scenarios
            if keymismatch == 1:
               self.unmatchedPair.append([newAddr.chainIndex, byteLocation])

            #TODO: needs better handling for keymismatch == 2
            elif keymismatch == 2:
               self.misc.append('no private key at chainIndex %d in wallet %s'\
                                 % (newAddr.chainIndex, WalletPath))

            elif keymismatch == 3:
               newAddr.binPublicKey65 = \
                     CryptoECDSA().ComputePublicKey(newAddr.binPrivKey32_Plain)
               newAddr.addrStr20 = newAddr.binPublicKey65.getHash160()

            #if we have clear possible mismatches (or there were none), 
            #proceed to consistency checks
            if keymismatch == 0:
               if not CryptoECDSA().CheckPubPrivKeyMatch( \
                                    newAddr.binPrivKey32_Plain, \
                                    newAddr.binPublicKey65):
                  self.unmatchedPair.append([newAddr.chainIndex, byteLocation])

            if newAddr.addrStr20 != entrylist[1]:
               self.hashValMismatch.append([newAddr.chainIndex, byteLocation])
               

            
            if isPrivForked:
               negImport = newAddr.copy()
               negImport.chainIndex = -3 -newAddr.chainIndex
               
               if negImport.useEncryption:
                  negImport.lock()
                                             
               importedDict[self.nImports] = [negImport, 0, 0, 0]
               self.nImports = self.nImports +1
                      
            if newAddr.useEncryption:
               newAddr.lock()      
               
      if self.naddress > 0: self.UIreport = self.UIreport + UIupdate

      #imported addresses
      if not self.WO:
         for i in range(0, self.nImports):
            entrylist = []
            entrylist = list(importedDict[i])
            newAddr = entrylist[0]
            rawData = entrylist[3]
   
            UIupdate = '<b>- Processing imported address entries:</b> \
                          %d/%d<br>' % (i +1, self.nImports)
            if Progress(self.UIreport + UIupdate) == 0:
               if SecurePassphrase: SecurePassphrase.destroy()
               if toRecover.kdfKey: toRecover.kdfKey.destroy()
               rootAddr.lock()
               return 0
            if prgAt:
               prgAt[0] = prgAt_in + (0.01 + 0.99*(newAddr.chainIndex +1) \
                                      /prgTotal)*prgAt[1]            
            
            if newAddr.chainIndex <= -2:
               if newAddr.chainIndex < -2:
                  self.negativeImports.append(newAddr.addrStr20)
               else:                                              
                  # Fix byte errors in the address data
                  fixedAddrData = newAddr.serialize()
                  if not rawData==fixedAddrData:
                     self.importedErr.append('found byte error in imported \
                              address %d at file offset %d' % (i, entrylist[2]))
                     newAddr = PyBtcAddress()
                     newAddr.unserialize(fixedAddrData)
                     entrylist[0] = newAddr
                     importedDict[i] = entrylist
                     
               #check public key is a valid EC point
               if newAddr.hasPubKey():
                  if not CryptoECDSA().VerifyPublicKeyValid( \
                                                      newAddr.binPublicKey65):
                     self.importedErr.append('invalid pub key for imported \
                        address %d at file offset %d\r\n' % (i, entrylist[2]))
               else:
                  self.importedErr.append('missing pub key for imported \
                        address %d at file offset %d\r\n' % (i, entrylist[2]))
      
               #if there a private key in the entry, check for consistency
               if not newAddr.hasPrivKey():
                  self.importedErr.append('missing private key for imported \
                        address %d at file offset %d\r\n' % (i, entrylist[2]))
               else:
                  
                  if newAddr.useEncryption != toRecover.useEncryption:
                     if newAddr.useEncryption:
                        self.importedErr.append('Encrypted address entry in \
                           a non encrypted wallet for imported address %d at \
                           file offset %d\r\n' % (i, entrylist[2]))
                     else:
                        self.importedErr.append('Unencrypted address entry in \
                           an encrypted wallet for imported address %d at file \
                           offset %d\r\n' % (i, entrylist[2]))                 
                     
                  keymismatch = 0
                  if newAddr.isLocked:
                     try:
                        newAddr.unlock(toRecover.kdfKey)
                     except KeyDataError:
                        keymismatch = 1
                        self.importedErr.append('pub key doesnt match private \
                           key for imported address %d at file offset %d\r\n' \
                           % (i, entrylist[2]))
      
      
                  if keymismatch == 0:
                     #pubkey is present, check against priv key
                     if not CryptoECDSA().CheckPubPrivKeyMatch( \
                           newAddr.binPrivKey32_Plain, newAddr.binPublicKey65):
                        keymismatch = 1
                        self.importedErr.append('pub key doesnt match private \
                           key for imported address %d at file offset %d\r\n' \
                           % (i, entrylist[2]))
      
                  if keymismatch == 1:
                     #compute missing/invalid pubkey
                     newAddr.binPublicKey65 = CryptoECDSA().ComputePublicKey( \
                                                    newAddr.binPrivKey32_Plain)
      
                  #check hashVal
                  if newAddr.addrStr20 != entrylist[1] and newAddr.chainIndex == 2:
                     newAddr.addrStr20 = newAddr.binPublicKey65.getHash160()
                     self.importedErr.append('hashVal doesnt match addrStr20 \
                              for imported address %d at file offset %d\r\n' \
                              % (i, entrylist[2]))
      
                  #if the entry was encrypted, lock it back with the new wallet
                  #kdfkey
                  if newAddr.useEncryption:
                     newAddr.lock()
                  

      if self.nImports > 0: self.UIreport = self.UIreport + UIupdate
      #TODO: check comments consistency
      
      nerrors = len(self.rawError) + len(self.byteError) + \
      len(self.sequenceGaps) + len(self.forkedPublicKeyChain) + \
      len(self.chainCodeCorruption) + len(self.invalidPubKey) + \
      len(self.missingPubKey) + len(self.hashValMismatch) + \
      len(self.unmatchedPair) + len(self.importedErr) + len(self.misc)
         
      if nerrors:
         if not self.WO or rmode == RECOVERMODE.Full:
            if rmode < RECOVERMODE.Meta:
               
               #create recovered wallet
               RecoveredWallet = self.createRecoveredWallet(toRecover, \
                           rootAddr, SecurePassphrase, Progress, returnError)
               if SecurePassphrase: RecoveredWallet.kdfKey = \
                           RecoveredWallet.kdf.DeriveKey(SecurePassphrase)               
               rootAddr.lock()
               
               if not isinstance(RecoveredWallet, PyBtcWallet):
                  if SecurePassphrase: SecurePassphrase.destroy()
                  if toRecover.kdfKey: toRecover.kdfKey.destroy() 
                  return RecoveredWallet
                              
               #build address pool
               for i in range(1, self.naddress):
                  UIupdate = '<b>- Building address chain:</b>   %d/%d<br>' % \
                             (i+1, self.naddress)
                  if Progress(self.UIreport + UIupdate) == 0:
                     if SecurePassphrase: SecurePassphrase.destroy()
                     if toRecover.kdfKey: toRecover.kdfKey.destroy()
                     if RecoveredWallet.kdfKey: RecoveredWallet.kdfKey.destroy()
                     return 0
   
                  #TODO: check this builds the proper address chain, 
                  #and saves encrypted private keys
                  RecoveredWallet.computeNextAddress(None, False, True)
   
               if Progress and self.naddress > 0: 
                  self.UIreport = self.UIreport + UIupdate
   
               #save imported addresses
               if rootAddr.isLocked:
                  rootAddr.unlock(toRecover.kdfKey)
               invQ = self.getInvModOfHMAC(rootAddr.binPrivKey32_Plain.toBinStr())
               regQ = self.getValidKeyHMAC(rootAddr.binPrivKey32_Plain.toBinStr())
               rootAddr.lock()
               
               for i in range(0, self.nImports):
                  UIupdate = '<b>- Saving imported addresses:</b>   %d/%d<br>' \
                              % (i+1, self.nImports)
                  if Progress(self.UIreport + UIupdate) == 0:
                     if SecurePassphrase: SecurePassphrase.destroy()
                     if toRecover.kdfKey: toRecover.kdfKey.destroy()
                     if RecoveredWallet.kdfKey: RecoveredWallet.kdfKey.destroy()
                     return 0
   
                  entrylist = []
                  entrylist = list(importedDict[i])
                  newAddr = entrylist[0]
                  
                  if newAddr.isLocked:
                     newAddr.unlock(toRecover.kdfKey)
                    
                  if newAddr.chainIndex < -2:
                     privMultiplier = CryptoECDSA().ECMultiplyScalars( \
                                           newAddr.binPrivKey32_Plain.toBinStr(),
                                           invQ.toBinStr())
                     self.privKeyMultipliers.append(binary_to_hex(privMultiplier))

                     # Sanity check that the multipliers are correct
                     recov = CryptoECDSA().ECMultiplyScalars(privMultiplier,
                                                             regQ.toBinStr())
                     if not recov==newAddr.binPrivKey32_Plain.toBinStr():
                        # Unfortunately I'm not sure what to do here if it doesn't match
                        # We know no ther way to handle it...
                        LOGERROR('Logging a multiplier that does not match!?')
                     
                  if newAddr.useEncryption:
                     newAddr.keyChanged = 1
                     newAddr.lock(RecoveredWallet.kdfKey)
                                          
                  RecoveredWallet.walletFileSafeUpdate([[WLT_UPDATE_ADD, \
                           WLT_DATATYPE_KEYDATA, newAddr.addrStr20, newAddr]])
   
               if Progress and self.nImports > 0: self.UIreport = \
                                                      self.UIreport + UIupdate

               invQ,regQ = None,None
   
               #save comments
               if rmode == RECOVERMODE.Full:
                  for i in range(0, self.ncomments):
                     UIupdate = '<b>- Saving comment entries:</b>   %d/%d<br>' \
                                 % (i+1, self.ncomments)
                     if Progress(self.UIreport + UIupdate) == 0:
                        if SecurePassphrase: SecurePassphrase.destroy()
                        if toRecover.kdfKey: toRecover.kdfKey.destroy()
                        if RecoveredWallet.kdfKey: 
                           RecoveredWallet.kdfKey.destroy()                           
                        return 0
   
                     entrylist = []
                     entrylist = list(commentDict[i])
                     RecoveredWallet.walletFileSafeUpdate([[WLT_UPDATE_ADD, \
                                    entrylist[2], entrylist[1], entrylist[0]]])
   
                  if Progress and self.ncomments > 0: self.UIreport = \
                                                      self.UIreport + UIupdate
   
      if isinstance(rootAddr.binPrivKey32_Plain, SecureBinaryData): 
         rootAddr.lock()
      
      #TODO: nothing to process anymore at this point. if the recovery mode 
      #is 4 (meta), just return the comments dict
      if isinstance(toRecover.kdfKey, SecureBinaryData): 
         toRecover.kdfKey.destroy()
      if RecoveredWallet is not None:
         if isinstance(RecoveredWallet.kdfKey, SecureBinaryData): 
            RecoveredWallet.kdfKey.destroy()

      if SecurePassphrase: SecurePassphrase.destroy()

      if rmode != RECOVERMODE.Meta:
         if nerrors == 0:
            return self.BuildLogFile(0, Progress, returnError, nerrors)
         else:
            return self.BuildLogFile(1, Progress, returnError, nerrors)
      else:
         return commentDict

   ############################################################################
   def createRecoveredWallet(self, toRecover, rootAddr, SecurePassphrase, 
                             Progress, returnError):
      self.newwalletPath = os.path.join(os.path.dirname(toRecover.walletPath), 
                           'armory_%s_RECOVERED%s.wallet' % \
                           (toRecover.uniqueIDB58, '_WatchOnly' \
                            if self.WO else ''))
      
      if os.path.exists(self.newwalletPath):
         try: 
            os.remove(self.newwalletPath)
         except: 
            LOGEXCEPT('')
            return self.BuildLogFile(-2, Progress, returnError)

      try:
         if not self.WO:
            RecoveredWallet = PyBtcWallet()
            withEncrypt = SecurePassphrase != None
            RecoveredWallet.createNewWallet( \
                           newWalletFilePath=self.newwalletPath, \
                           securePassphrase=SecurePassphrase, \
                           plainRootKey=rootAddr.binPrivKey32_Plain, \
                           chaincode=rootAddr.chaincode, \
                           withEncrypt=withEncrypt, \
                           #not registering with the BDM, 
                           #so no addresses are computed
                           doRegisterWithBDM=False, \
                           shortLabel=toRecover.labelName, \
                           longLabel=toRecover.labelDescr)
         else:
            RecoveredWallet = self.createNewWO(toRecover, \
                                               self.newwalletPath, rootAddr)
      except:
         LOGEXCEPT('')
         #failed to create new file
         return self.BuildLogFile(-2, Progress, returnError) 
      
      return RecoveredWallet
   ############################################################################
   def LookForFurtherEntry(self, rawdata, loc):
      """
      Attempts to find valid data entries in wallet file by skipping known byte
      widths.

      The process:
      1) Assume an address entry with invalid data type key and/or the hash160. 
      Read ahead and try to unserialize a valid PyBtcAddress
      2) Assume a corrupt address entry. Move 1+20+237 bytes ahead, try to 
      unpack the next entry

      At this point all entries are of random length. The most accurate way to
      define them as valid is to try and unpack the next entry, or check end of
      file has been hit gracefully

      3) Try for address comment
      4) Try for transaction comment
      5) Try for deleted entry

      6) At this point, can still try for random byte search. Essentially, push
      an incremental amount of bytes until a valid entry or the end of the file
      is hit. Simplest way around it is to recursively call this member with an
      incremented loc



      About address entries: currently, the code tries to fully unserialize 
      tentative address entries. It will most likely raise at the slightest 
      error. However, that doesn't mean the entry is entirely bogus, or not an 
      address entry at all. Individual data packets should be checked against 
      their checksum for validity in a full implementation of the raw data 
      recovery layer of this tool. Other entries do not carry checksums and 
      thus appear opaque to this recovery layer.

      TODO:
         1) verify each checksum data block in address entries
         2) same with the file header
      """

      #check loc against data end.
      if loc >= rawdata.getSize():
         return None, None, None, [0]

      #reset to last known good offset
      rawdata.resetPosition(loc)

      #try for address entry: push 1 byte for the key, 20 for the public key 
      #hash, try to unpack the next 237 bytes as an address entry
      try:
         rawdata.advance(1)
         hash160 = rawdata.get(BINARY_CHUNK, 20)
         chunk = rawdata.get(BINARY_CHUNK, self.pybtcaddrSize)

         newAddr, chksumError = self.addrEntry_unserialize_recover(chunk)
         #if we got this far, no exception was raised, return the valid entry
         #and hash, but invalid key

         if chksumError != 0:
            #had some checksum errors, pass the data on
            return 0, hash160, chunk, [0, loc, newAddr, chksumError]

         return 0, hash160, chunk, [1, loc]
      except:
         LOGEXCEPT('')
         #unserialize error, move on
         rawdata.resetPosition(loc)

      #try for next entry
      try:
         rawdata.advance(1+20+237)
         dtype, hash, chunk = PyBtcWallet().unpackNextEntry(rawdata)
         if dtype>-1 and dtype<5:
            return dtype, hash, chunk, [1, loc +1+20+237]
         else:
            rawdata.resetPosition(loc)
      except:
         LOGEXCEPT('')
         rawdata.resetPosition(loc)

      #try for addr comment: push 1 byte for the key, 20 for the hash160, 
      #2 for the N and N for the comment
      try:
         rawdata.advance(1)
         hash160 = rawdata.get(BINARY_CHUNK, 20)
         chunk_length = rawdata.get(UINT16)
         chunk = rawdata.get(BINARY_CHUNK, chunk_length)

         #test the next entry
         dtype, hash, chunk2 = PyBtcWallet().unpackNextEntry(rawdata)
         if dtype>-1 and dtype<5:
            #good entry, return it
            return 1, hash160, chunk, [1, loc]
         else:
            rawdata.resetPosition(loc)
      except:
         LOGEXCEPT('')
         rawdata.resetPosition(loc)

      #try for txn comment: push 1 byte for the key, 32 for the txnhash, 
      #2 for N, and N for the comment
      try:
         rawdata.advance(1)
         hash256 = rawdata.get(BINARY_CHUNK, 32)
         chunk_length = rawdata.get(UINT16)
         chunk = rawdata.get(BINARY_CHUNK, chunk_length)

         #test the next entry
         dtype, hash, chunk2 = PyBtcWallet().unpackNextEntry(rawdata)
         if dtype>-1 and dtype<5:
            #good entry, return it
            return 2, hash256, chunk, [1, loc]
         else:
            rawdata.resetPosition(loc)
      except:
         LOGEXCEPT('')
         rawdata.resetPosition(loc)

      #try for deleted entry: 1 byte for the key, 2 bytes for N, N bytes
      #worth of 0s
      try:
         rawdata.advance(1)
         chunk_length = rawdata.get(UINT16)
         chunk = rawdata.get(BINARY_CHUNK, chunk_length)

         #test the next entry
         dtype, hash, chunk2 = PyBtcWallet().unpackNextEntry(rawdata)
         if dtype>-1 and dtype<5:
            baddata = 0
            for i in len(chunk):
               if i != 0:
                  baddata = 1
                  break

            if baddata != 0:
               return 4, None, chunk, [1, loc]

         rawdata.resetPosition(loc)
      except:
         LOGEXCEPT('')
         rawdata.resetPosition(loc)

      #couldn't find any valid entries, push loc by 1 and try again
      loc = loc +1
      return self.LookForFurtherEntry(rawdata, loc)

   ############################################################################
   def addrEntry_unserialize_recover(self, toUnpack):
      """
      Unserialze a raw address entry, test all checksum carrying members

      On errors, flags chksumError bits as follows:

         bit 0: addrStr20 error

         bit 1: private key error
         bit 2: contains a valid private key even though containsPrivKey is 0

         bit 3: iv error
         bit 4: contains a valid iv even though useEncryption is 0

         bit 5: pubkey error
         bit 6: contains a valid pubkey even though containsPubKey is 0

         bit 7: chaincode error
      """

      if isinstance(toUnpack, BinaryUnpacker):
         serializedData = toUnpack
      else:
         serializedData = BinaryUnpacker( toUnpack )


      def chkzero(a):
         """
         Due to fixed-width fields, we will get lots of zero-bytes
         even when the binary data container was empty
         """
         if a.count('\x00')==len(a):
            return ''
         else:
            return a

      chksumError = 0

      # Start with a fresh new address
      retAddr = PyBtcAddress()

      retAddr.addrStr20 = serializedData.get(BINARY_CHUNK, 20)
      chkAddr20      = serializedData.get(BINARY_CHUNK,  4)

      addrVerInt     = serializedData.get(UINT32)
      flags          = serializedData.get(UINT64)
      retAddr.addrStr20 = verifyChecksum(self.addrStr20, chkAddr20)
      flags = int_to_bitset(flags, widthBytes=8)

      # Interpret the flags
      containsPrivKey              = (flags[0]=='1')
      containsPubKey               = (flags[1]=='1')
      retAddr.useEncryption           = (flags[2]=='1')
      retAddr.createPrivKeyNextUnlock = (flags[3]=='1')

      if len(self.addrStr20)==0:
         chksumError |= 1



      # Write out address-chaining parameters (for deterministic wallets)
      retAddr.chaincode   = chkzero(serializedData.get(BINARY_CHUNK, 32))
      chkChaincode        =         serializedData.get(BINARY_CHUNK,  4)
      retAddr.chainIndex  =         serializedData.get(INT64)
      depth               =         serializedData.get(INT64)
      retAddr.createPrivKeyNextUnlock_ChainDepth = depth

      # Correct errors, convert to secure container
      retAddr.chaincode = SecureBinaryData(verifyChecksum(retAddr.chaincode, \
                                                          chkChaincode))
      if retAddr.chaincode.getSize == 0:
         chksumError |= 128


      # Write out whatever is appropriate for private-key data
      # Binary-unpacker will write all 0x00 bytes if empty values are given
      iv      = chkzero(serializedData.get(BINARY_CHUNK, 16))
      chkIv   =         serializedData.get(BINARY_CHUNK,  4)
      privKey = chkzero(serializedData.get(BINARY_CHUNK, 32))
      chkPriv =         serializedData.get(BINARY_CHUNK,  4)
      iv      = SecureBinaryData(verifyChecksum(iv, chkIv))
      privKey = SecureBinaryData(verifyChecksum(privKey, chkPriv))


      # If this is SUPPOSED to contain a private key...
      if containsPrivKey:
         if privKey.getSize()==0:
            chksumError |= 2
            containsPrivKey = 0
      else:
         if privKey.getSize()==32:
            chksumError |= 4
            containsPrivKey = 1

      if retAddr.useEncryption:
         if iv.getSize()==0:
            chksumError |= 8
            retAddr.useEncryption = 0
      else:
         if iv.getSize()==16:
            chksumError |= 16
            retAddr.useEncryption = 1

      if retAddr.useEncryption:
         if retAddr.createPrivKeyNextUnlock:
            retAddr.createPrivKeyNextUnlock_IVandKey[0] = iv.copy()
            retAddr.createPrivKeyNextUnlock_IVandKey[1] = privKey.copy()
         else:
            retAddr.binInitVect16     = iv.copy()
            retAddr.binPrivKey32_Encr = privKey.copy()
      else:
         retAddr.binInitVect16      = iv.copy()
         retAddr.binPrivKey32_Plain = privKey.copy()

      pubKey = chkzero(serializedData.get(BINARY_CHUNK, 65))
      chkPub =         serializedData.get(BINARY_CHUNK, 4)
      pubKey = SecureBinaryData(verifyChecksum(pubKey, chkPub))

      if containsPubKey:
         if not pubKey.getSize()==65:
            chksumError |= 32
            if retAddr.binPrivKey32_Plain.getSize()==32:
               pubKey = CryptoECDSA().ComputePublicKey(
                                      retAddr.binPrivKey32_Plain)
      else:
         if pubKey.getSize()==65:
            chksumError |= 64

      retAddr.binPublicKey65 = pubKey

      retAddr.timeRange[0] = serializedData.get(UINT64)
      retAddr.timeRange[1] = serializedData.get(UINT64)
      retAddr.blkRange[0]  = serializedData.get(UINT32)
      retAddr.blkRange[1]  = serializedData.get(UINT32)

      retAddr.isInitialized = True

      if (chksumError and 171) == 171:
         raise InvalidEntry

      if chksumError != 0:
         #write out errors to the list
         self.rawError.append('   Encountered checksum errors in follolwing \
                               address entry members:')

         if chksumError and 1:
            self.rawError.append('      - addrStr20')
         if chksumError and 2:
            self.rawError.append('      - private key')
         if chksumError and 4:
            self.rawError.append('      - hasPrivatKey flag')
         if chksumError and 8:
            self.rawError.append('      - Encryption IV')
         if chksumError and 16:
            self.rawError.append('      - useEncryption flag')
         if chksumError and 32:
            self.rawError.append('      - public key')
         if chksumError and 64:
            self.rawError.append('      - hasPublicKey flag')
         if chksumError and 128:
            self.rawError.append('      - chaincode')

      return retAddr, chksumError

   ############################################################################
   def createNewWO(self, toRecover, newPath, rootAddr):
      newWO = PyBtcWallet()
      
      newWO.version = toRecover.version
      newWO.magicBytes = toRecover.magicBytes
      newWO.wltCreateDate = toRecover.wltCreateDate
      newWO.uniqueIDBin = toRecover.uniqueIDBin
      newWO.useEncryption = False
      newWO.watchingOnly = True
      newWO.walletPath = newPath
           
      if toRecover.labelName:
         newWO.labelName = toRecover.labelName[:32]
      if toRecover.labelDescr:
         newWO.labelDescr = toRecover.labelDescr[:256]
      
         
      newAddr = rootAddr.copy()
      newAddr.binPrivKey32_Encr = SecureBinaryData()
      newAddr.binPrivKey32_Plain = SecureBinaryData()
      newAddr.useEncryption = False
      newAddr.createPrivKeyNextUnlock = False
      
      newWO.addrMap['ROOT'] = newAddr
      firstAddr = newAddr.extendAddressChain()
      newWO.addrMap[firstAddr.getAddr160()] = firstAddr
      
      newWO.lastComputedChainAddr160 = firstAddr.getAddr160()
      newWO.lastComputedChainIndex  = firstAddr.chainIndex
      newWO.highestUsedChainIndex   = toRecover.highestUsedChainIndex
      
      newWO.writeFreshWalletFile(newPath)
      
      return newWO
   
   ############################################################################
   def getValidKeyHMAC(self, Q):
      nonce = 0
      while True:
         hmacQ = HMAC256(Q, 'LogMult%d' % nonce)
         if binary_to_int(hmacQ, BIGENDIAN) >= SECP256K1_ORDER:
            nonce += 1
            continue

         return SecureBinaryData(hmacQ)

   ############################################################################
   def getInvModOfHMAC(self, Q):
      hmacQ = self.getValidKeyHMAC(Q)
      return CryptoECDSA().InvMod(SecureBinaryData(hmacQ))


###############################################################################
def WalletConsistencyCheck(wallet, prgAt=None):
   """
   Checks consistency of non encrypted wallet data
   Returns 0 if no error was found, otherwise a 
   string list of the scan full log
   """

   return PyBtcWalletRecovery().ProcessWallet(None, wallet, None, 
                                    RECOVERMODE.Check, prgAt, True)

#############################################################################
# We don't have access to the qtdefines:tr function, but we still want
# the capability to print multi-line strings within the code.  This simply
# strips each line and then concatenates them together
def tr_(s):
   return ' '.join([line.strip() for line in s.split('\n')])

#############################################################################
@AllowAsync
def FixWallet(wltPath, wlt, mode=RECOVERMODE.Full, DoNotMove=False, 
              Passphrase=None, Progress=emptyFunc):
   
   '''
   return code:
   0 - no wallet errors found, nothing to fix
   1 - errors found, wallet fixed
   str - errors found, couldnt fix wallet, returning the error as a str
   '''
   fixer = PyBtcWalletRecovery()
   frt = fixer.ProcessWallet(wltPath, wlt, Passphrase, mode, Progress=Progress)

   # Shorten a bunch of statements
   datestr = RightNowStr('%Y-%m-%d-%H%M')
   if wlt:
      homedir = os.path.dirname(wlt.walletPath)
      wltID   = wlt.uniqueIDB58
   else:
      homedir = os.path.dirname(wltPath)
      wltID   = fixer.UID
   
      
   if frt == 0:
      Progress(fixer.UIreport + fixer.EndLog) 
      return 0, 0, fixer
                 
   elif frt == 1 or (isinstance(frt, dict) and frt['nErrors'] != 0):
      Progress(fixer.UIreport)
      
      if DoNotMove:
         Progress(fixer.UIreport + fixer.EndLog)
         return 1, 0, fixer
      else:   
         #move the old wallets and log files to another folder
         corruptFolder = os.path.join(homedir, wltID, datestr)
         if not os.path.exists(corruptFolder):
            os.makedirs(corruptFolder)

         logsToCopy = ['armorylog.txt', 'armorycpplog.txt', 'multipliers.txt', 'dbLog.txt']
         wltCopyName = 'armory_%s_ORIGINAL_%s.wallet' % (wltID, '_WatchOnly')
         wltLogName  = 'armory_%s_LOGFILE_%s.log' % \
                                 (wltID, '_WatchOnly' if fixer.WO else '')
   
         corruptWltPath = os.path.join(corruptFolder, wltCopyName)
         recoverLogPath = os.path.join(corruptFolder, wltLogName)
            
         try:
   
            if not fixer.WO:
               #wallet has private keys, make a WO version and delete it
               wlt.forkOnlineWallet(corruptWltPath, wlt.labelName, 
                                    wlt.labelDescr)
               os.remove(wlt.walletPath)
            else:
               os.rename(wlt.walletPath, corruptWltPath)
   
                  
            if os.path.exists(fixer.LogPath):
               os.rename(fixer.LogPath, os.path.join(corruptFolder, 
                                                        wltLogName))
               
            if os.path.exists(fixer.newwalletPath):
               os.rename(fixer.newwalletPath, wlt.walletPath)
               
            #remove backups
            origBackup = getSuffixedPath(wlt.walletPath, 'backup')
            if os.path.exists(origBackup):
               os.remove(origBackup)
   
            newBackup = getSuffixedPath(fixer.newwalletPath, 'backup')
            if os.path.exists(newBackup):
               os.remove(newBackup)
               
            # Copy all the relevant log files
            for fn in logsToCopy:
               fullpath = os.path.join(homedir, fn)
               if os.path.exists(fullpath):
                  shutil.copy(fullpath,  corruptFolder)
               else:
                  LOGERROR('Expected log file was not copied: %s', fn)
   
               
            fixer.EndLog = ("""
                  <br><b>Wallet analysis and restoration complete.</b><br>
                  The inconsistent wallet and log files were moved to:
                  <br>%s/<br><br>""") % corruptFolder
                                 
            Progress(fixer.UIreport + fixer.EndLog)
            return 1, corruptFolder, fixer
      
         except Exception as e:
            #failed to move files around, most likely a credential error
            LOGEXCEPT(str(e))
            errStr = '<br><b>An error occurred moving wallet files:</b> %s' % e
            Progress(fixer.UIreport + errStr)
            
            return -1, fixer.UIreport + errStr, fixer
   else:
      Progress(fixer.UIreport + fixer.EndLog)
      return -1, fixer.UIreport + fixer.EndLog, fixer

###############################################################################
@AllowAsync
def FixWalletList(wallets, dlg, Progress=emptyFunc): 
   
   #It's the caller's responsibility to unload the wallets from his app
   
   #fix the wallets
   fixedWlt = []
   wlterror = []
   goodWallets = []
   fixerObjs = []
   logsSaved = []   

   for wlt in wallets:
      if dlg: 
         status = [0]         
         dlg.sigSetNewProgress(status)
         while not status[0]:
            sleep(0.01)
         
      wltStatus, extraData, recovObj = FixWallet( \
         '', wlt, Passphrase=dlg.AskUnlock, Progress=Progress)


      fixerObjs.append(recovObj)

      if wltStatus == 0:
         goodWallets.append(wlt.uniqueIDB58)
         fixedWlt.append(wlt.walletPath)
                 
      elif wltStatus == 1:
         fixedWlt.append(wlt.walletPath)
         logsSaved.append([wlt.uniqueIDB58, extraData])
      elif wltStatus == -1:
         wlterror.append([wlt.uniqueIDB58, extraData])
   
   if dlg:                  
      dlg.setRecoveryDone(wlterror, goodWallets, fixedWlt, fixerObjs)
            
      #load the new wallets
      dlg.loadFixedWallets(fixedWlt)
      
   else:
      return wlterror
   
###############################################################################
'''
Stand alone, one wallet a time, all purpose recovery call.
Used with unloaded wallets or modes other than Full, and for armoryd
If dlg is set, it will report to it (UI)
If not, it will log the wallet status with LOGERROR and LOGINFO, and return the
status code to the caller
''' 
@AllowAsync
def ParseWallet(wltPath, wlt, mode, dlg, Progress=emptyFunc): 
   fixedWlt = []
   wlterror = []
   goodWallets = []
   inPassphrase = dlg.AskUnlock if dlg else None
   
   wltStatus, extraData, recovObj = FixWallet(wltPath, wlt, mode, True, 
                                              Passphrase=inPassphrase, 
                                              Progress=Progress)
   if wltStatus == 0:
      goodWallets.append(1)
      fixedWlt.append(1)
      
      if dlg is None:
         if wlt: LOGINFO('Wallet %s is consistent' % (wlt.uniqueIDB58))
         elif wltPath: LOGINFO('Wallet %s is consistent' % (wltPath))
                 
   elif wltStatus == 1:
      fixedWlt.append(1)
      
      if dlg is None:
         if wlt: LOGERROR('Wallet %s is inconsistent!!!' % (wlt.uniqueIDB58))
         elif wltPath: LOGERROR('Wallet %s is inconsistent!!!' % (wltPath))
         
   elif wltStatus == -1:
      wlterror.append(extraData)
      
      if dlg is None:
         if wlt: 
            LOGERROR('Failed to perform consistency check on wallet %s!!!'\
                      % (wlt.uniqueIDB58))
         elif wltPath: 
            LOGERROR('Failed to perform consistency check on wallet %s!!!'\
                      % (wltPath))
   
   if dlg:                  
      dlg.setRecoveryDone(wlterror, goodWallets, fixedWlt, [recovObj])
   else: 
      return wltStatus


