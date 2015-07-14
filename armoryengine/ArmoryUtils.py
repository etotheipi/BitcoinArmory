################################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory
# Author:     Alan Reiner
# Website:    www.bitcoinarmory.com
# Orig Date:  20 November, 2011
#
################################################################################
import sys
sys.path.append('..')

import base64
import hashlib
import locale
import math
import multiprocessing
import os
import platform
import shutil
import signal
import smtplib
import socket
import subprocess
import time

from datetime import datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from qrcodenative import QRCode, QRErrorCorrectLevel
from twisted.internet.protocol import ClientFactory, Protocol

from Constants import *
from Exceptions import *
from ArmoryOptions import *
from ArmoryLog import *

################################################################################
# Load the C++ utilites here
#
#    The SWIG/C++ block utilities give us access to the blockchain, fast ECDSA
#    operations, and general encryption/secure-binary containers
################################################################################
try:
   from CppBlockUtils import BtcUtils, CryptoAES, CryptoECDSA, KdfRomix, \
      SecureBinaryData
   LOGINFO('C++ block utilities loaded successfully')
except:
   initializeOptions()
   initializeLog()
   LOGCRIT('C++ block utilities not available.')
   LOGCRIT('   Make sure that you have the SWIG-compiled modules')
   LOGCRIT('   in the current directory (or added to the PATH)')
   LOGCRIT('   Specifically, you need:')
   LOGCRIT('       CppBlockUtils.py     and')
   if isLinux() or isMac():
      LOGCRIT('       _CppBlockUtils.so')
   elif isWindows():
      LOGCRIT('       _CppBlockUtils.pyd')
   else:
      LOGCRIT('\n\n... UNKNOWN operating system')
   raise


# Version Handling Code
def getVersionString(vquad, numPieces=4):
   vstr = '%d.%02d' % vquad[:2]
   if (vquad[2] > 0 or vquad[3] > 0) and numPieces>2:
      vstr += '.%d' % vquad[2]
   if vquad[3] > 0 and numPieces>3:
      vstr += '.%d' % vquad[3]
   return vstr

def getVersionInt(vquad, numPieces=4):
   vint  = int(vquad[0] * 1e7)
   vint += int(vquad[1] * 1e5)
   if numPieces>2:
      vint += int(vquad[2] * 1e3)
   if numPieces>3:
      vint += int(vquad[3])
   return vint

def readVersionString(verStr):
   verList = [int(piece) for piece in verStr.split('.')]
   while len(verList)<4:
      verList.append(0)
   return tuple(verList)

def readVersionInt(verInt):
   verStr = str(verInt).rjust(10,'0')
   verList = []
   verList.append( int(verStr[       -3:]) )
   verList.append( int(verStr[    -5:-3 ]) )
   verList.append( int(verStr[ -7:-5    ]) )
   verList.append( int(verStr[:-7       ]) )
   return tuple(verList[::-1])
 

################################################################################
def launchProcess(cmd, useStartInfo=True, *args, **kwargs):
   LOGINFO('Executing popen: %s', str(cmd))
   if isWindows():
      from subprocess_win import Popen, PIPE, STARTUPINFO, STARTF_USESHOWWINDOW

      if useStartInfo:
         startinfo = STARTUPINFO()
         startinfo.dwFlags |= STARTF_USESHOWWINDOW
         return Popen(cmd, *args, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                      startupinfo=startinfo, **kwargs)
      else:
         return Popen(cmd, *args, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                      **kwargs)
   else:
      from subprocess import Popen, PIPE
      return Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, *args, **kwargs)


################################################################################
def killProcess(pid, sig='default'):
   # I had to do this, because killing a process in Windows has issues
   # when using py2exe (yes, os.kill does not work, for the same reason
   # I had to pass stdin/stdout/stderr everywhere...
   LOGWARN('Killing process pid=%d', pid)
   if isWindows():
      import sys, os.path, ctypes, ctypes.wintypes
      k32 = ctypes.WinDLL('kernel32.dll')
      k32.OpenProcess.restype = ctypes.wintypes.HANDLE
      k32.TerminateProcess.restype = ctypes.wintypes.BOOL
      hProcess = k32.OpenProcess(1, False, pid)
      k32.TerminateProcess(hProcess, 1)
      k32.CloseHandle(hProcess)
   else:
      import os
      sig = signal.SIGKILL if sig=='default' else sig
      os.kill(pid, sig)


################################################################################
def removeIfExists(*args):
   for fileName in args:
      if os.path.exists(fileName):
         os.remove(fileName)


################################################################################
def deleteBitcoindDBs():
   if not os.path.exists(getBitcoinHomeDir()):
      LOGERROR('Could not find Bitcoin-Qt/bitcoind home dir to remove blk data')
      LOGERROR('  Does not exist: %s' % getBitcoinHomeDir())
   else:
      LOGINFO('Found bitcoin home dir, removing blocks and databases')

      # Remove directories
      for btcDir in ['blocks', 'chainstate', 'database']:
         fullPath = os.path.join(getBitcoinHomeDir(), btcDir)
         if os.path.exists(fullPath):
            LOGINFO('   Removing dir:  %s' % fullPath)
            shutil.rmtree(fullPath)

      # Remove files
      for btcFile in ['DB_CONFIG', 'db.log', 'debug.log', 'peers.dat']:
         fullPath = os.path.join(getBitcoinHomeDir(), btcFile)
         removeIfExists(fullPath)


################################################################################
def _processDeletions():

   # Flag to remove everything in Bitcoin dir except wallet.dat (if requested)
   if os.path.exists(getRedownloadFile()):
      # Flag to remove *BITCOIN-QT* databases so it will have to re-download
      LOGINFO('Found %s, will delete Bitcoin DBs & redownload' % getRedownloadFile())

      removeIfExists(getRedownloadFile(), getRebuildFile(), getRescanFile())
      setRedownloadFlag(True)
      setRebuildFlag(True)

   elif os.path.exists(getRebuildFile()):
      # Flag to remove Armory databases so it will have to rebuild
      LOGINFO('Found %s, will destroy and rebuild databases' % getRebuildFile())

      removeIfExists(getRebuildFile(), getRescanFile())
      setRebuildFlag(True)

   elif os.path.exists(getRescanFile()):
      LOGINFO('Found %s, will throw out saved history, rescan' % getRescanFile())
      removeIfExists(getRescanFile(), getRebuildFile())
      setRescanFlag(True)

   if os.path.exists(getClearMempoolFile()):
      # Flag to clear all ZC transactions from database
      LOGINFO('Found %s, will destroy all zero conf txs in DB'
              % getClearMempoolFile())
      removeIfExists(getClearMempoolFile())
      setClearMempoolFlag(True)

   # Separately, we may want to delete the settings file, which couldn't
   # be done easily from the GUI, because it frequently gets rewritten to
   # file before shutdown is complete.  The best way is to delete it on start.
   if os.path.exists(getDelSettingsFile()):
      removeIfExists(getSettingsPath(), getDelSettingsFile())

   # finally, do the deletions
   if getRedownloadFlag():
      deleteBitcoindDBs()
      removeIfExists(getRedownloadFile())

   if getRebuildFlag() and os.path.exists(getArmoryDatabaseDir()):
      LOGINFO('Found existing databases dir; removing before rebuild')
      shutil.rmtree(getArmoryDatabaseDir())
      os.mkdir(getArmoryDatabaseDir())

def _logTestAnnounce():
   if getTestAnnounceFlag():
      LOGERROR('*'*60)
      LOGERROR('You are currently using a developer mode intended for ')
      LOGERROR('to help with testing of announcements, which is considered')
      LOGERROR('a security risk.  ')
      LOGERROR('*'*60)


def _logTor():
   if getTorFlag():
      LOGWARN('Option --tor was supplied, forcing --skip-announce-check,')
      LOGWARN('--skip-online-check and --skip-stats-report')
      setSkipAnnounceFlag(True)
      setSkipStatsFlag(True)
      setForceOnlineFlag(True)


################################################################################
def getPrintableArmoryInfo():
   armoryVersion = getVersionString(BTCARMORY_VERSION)
   walletVersion = getVersionString(ARMORY_WALLET_VERSION)
   ret = '***********************************************' \
         '*********************************\n' \
         'Loading Armory Engine:\n' \
         '   Armory Version        : %(armoryVersion)s\n' \
         '   Armory Build          : %(build)s\n' \
         '   Armory Wallet Version : %(walletVersion)s\n' \
         'Detected Operating system: %(osName)s\n' \
         '   OS Variant            : %(osVariant)s\n' \
         '   User home-directory   : %(userHomeDir)s\n' \
         '   Satoshi BTC directory : %(bitcoinHomeDir)s\n' \
         '   Armory home dir       : %(armoryHomeDir)s\n' \
         '   ArmoryDB directory    : %(armoryDatabaseDir)s\n' \
         '   Armory settings file  : %(settingsPath)s\n' \
         '   Armory log file       : %(armoryLogFile)s\n' \
         '   Armory cpp log file   : %(armoryCppLogFile)s\n' \
         '   Do wallet checking    : %(doWalletCheck)s\n'
   return ret % dict(
      armoryCppLogFile=getArmoryCppLogFile(),
      armoryDatabaseDir=getArmoryDatabaseDir(),
      armoryHomeDir=getArmoryHomeDir(),
      armoryLogFile=getArmoryLogFile(),
      armoryVersion=armoryVersion, 
      bitcoinHomeDir=getBitcoinHomeDir(),
      build=getArmoryBuild(),
      doWalletCheck=getWalletCheckFlag(),
      osName=getOS(),
      osVariant=getOSVariant(),
      settingsPath=getSettingsPath(),
      userHomeDir=getUserHomeDir(), 
      walletVersion=walletVersion, 
   )

def _getArmoryDetailStr():
   ret = '\n\n\n' \
         '************************************************************\n' \
         'Invoked: %(args)s\n' \
         '************************************************************\n' \
         'Loading Armory Engine:' \
         '   Armory Version        : %(armoryVersion)s\n' \
         '   Armory Build:         : %(armoryBuild)s\n' \
         '   Armory Wallet Version : %(walletVersion)s\n' \
         'Detected Operating system: %(osName)s\n' \
         '   OS Variant            : %(osVariant)s\n' \
         '   User home-directory   : %(userHomeDir)s\n' \
         '   Satoshi BTC directory : %(bitcoinHomeDir)s\n' \
         '   Armory home dir       : %(armoryHomeDir)s\n' \
         'Detected System Specs    : \n' \
         '   Total Available RAM   : %(memory)0.2f GB\n' \
         '   CPU ID string         : %(cpu)s\n' \
         '   Number of CPU cores   : %(cores)d cores\n' \
         '   System is 64-bit      : %(x64)s\n' \
         '   Preferred Encoding    : %(encoding)s\n' \
         '   Machine Arch          : %(arch)s\n' \
         '   Available HDD (ARM)   : %(armoryHD)d GB\n' \
         '   Available HDD (BTC)   : %(bitcoinHD)d GB\n' \
         '\n' \
         'Network Name             : %(network)s\n' \
         'Satoshi Port             : %(bitcoinPort)d\n' \
         'Do wlt check             : %(walletCheck)s\n' \
         'Named options/arguments to armoryengine.py:\n'
   optionsDict = getOptionsDict()
   for key in sorted(optionsDict.keys()):
      ret += '    %-16s: %s\n' % (key,optionsDict[key])
   ret += 'Other arguments:\n'
   for val in getCommandLineArgs():
      ret += '    %s\n' % val
   ret += '************************************************************\n'
   args = ' '.join(sys.argv)
   armoryVersion = getVersionString(BTCARMORY_VERSION)
   walletVersion = getVersionString(ARMORY_WALLET_VERSION)
   return ret % dict(
      arch=getMachine(),
      args=args,
      armoryBuild=getArmoryBuild(),
      armoryHD=getArmoryHDSpace(),
      armoryHomeDir=getArmoryHomeDir(),
      armoryVersion=armoryVersion,
      bitcoinHD=getBitcoinHDSpace(),
      bitcoinHomeDir=getBitcoinHomeDir(),
      bitcoinPort=getBitcoinPort(),
      cores=getNumCores(),
      cpu=getCPU(),
      encoding=locale.getpreferredencoding(),
      memory=getMemory(),
      network=NETWORKS[getAddrByte()],
      osName=getOS(),
      osVariant=getOSVariant(),
      userHomeDir=getUserHomeDir(),
      walletCheck=getWalletCheckFlag(),
      walletVersion=walletVersion,
      x64=getX64Flag(),
   )


################################################################################
def _addWalletToList(inWltPath, inWltList):
   '''Helper function that checks to see if a path contains a valid wallet. If
      so, the wallet will be added to the incoming list.'''
   if os.path.isfile(inWltPath):
      # ignore backups
      if inWltPath.endswith(b'backup.wallet') \
         or inWltPath.endswith(b'backup.wlt'):
         return
      openfile = open(inWltPath, 'rb')
      first8 = openfile.read(8)
      openfile.close()

      # version 1.35 is '\xbaWALLET\x00', version 2.0 is '\xffARMORY\xff'
      if first8 in(b'\xbaWALLET\x00', b'\xffARMORY\xff'):
         inWltList.append(inWltPath)
   else:
      if not os.path.isdir(inWltPath):
         LOGWARN('Path %s does not exist.' % inWltPath)
      else:
         LOGDEBUG('%s is a directory.' % inWltPath)


################################################################################
def readWalletFiles():
   '''Function that finds the paths of all non-backup wallets in the Armory
      data directory (nothing passed in) or in a list of wallet paths (paths
      passed in.'''
   wltPaths = []

   for f in os.listdir(getArmoryHomeDir()):
      fullPath = os.path.join(getArmoryHomeDir(), f)
      _addWalletToList(fullPath, wltPaths)

   return wltPaths


def GetExecDir():
   """
   Return the path from where armoryengine was imported.  Inspect method
   expects a function or module name, it can actually inspect its own
   name...
   """
   srcpath = os.path.dirname(__file__)
   srcpath = os.path.abspath(srcpath)
   if isWindows() and srcpath.endswith('.zip'):
      srcpath = os.path.dirname(srcpath)

   # Right now we are at the armoryengine dir... walk up one more
   srcpath = os.path.dirname(srcpath)

   LOGINFO('Determined that execution dir is: %s' % srcpath)
   if not os.path.exists(srcpath):
      LOGERROR('Exec dir %s does not exist!' % srcpath)
      LOGERROR('Continuing anyway...' % srcpath)

   return srcpath


def coin2str(nSatoshi, ndec=8, rJust=True, maxZeros=8):
   """
   Converts a raw value (1e-8 BTC) into a formatted string for display

   ndec, guarantees that we get get a least N decimal places in our result

   maxZeros means we will replace zeros with spaces up to M decimal places
   in order to declutter the amount field

   """

   nBtc = float(nSatoshi) / float(ONE_BTC)
   s = ('%%0.%df' % ndec) % nBtc
   s = s.rjust(18, ' ')

   if maxZeros < ndec:
      maxChop = ndec - maxZeros
      nChop = min(len(s) - len(str(s.strip('0'))), maxChop)
      if nChop>0:
         s  = s[:-nChop] + nChop*' '

   if nSatoshi < 10000*ONE_BTC:
      s.lstrip()

   if not rJust:
      s = s.strip(' ')

   s = s.replace('. ', '')

   return s

def coin2strNZS(nSatoshi):
   """ Right-justified, minimum zeros, stripped """
   return coin2str(nSatoshi, 8, True, 0).strip()

def coin2str_approx(nSatoshi, sigfig=3):
   posVal = nSatoshi
   isNeg = False
   if nSatoshi<0:
      isNeg = True
      posVal *= -1

   nDig = max(round(math.log(posVal+1, 10)-0.5), 0)
   nChop = max(nDig-2, 0 )
   approxVal = round((10**nChop) * round(posVal / (10**nChop)))
   return coin2str( (-1 if isNeg else 1)*approxVal,  maxZeros=0)


def str2coin(theStr, negAllowed=True, maxDec=8, roundHighPrec=True):
   coinStr = str(theStr)
   if len(coinStr.strip())==0:
      raise ValueError

   isNeg = ('-' in coinStr)
   coinStrPos = coinStr.replace('-','')
   if not '.' in coinStrPos:
      if not negAllowed and isNeg:
         raise NegativeValueError
      return (int(coinStrPos)*ONE_BTC)*(-1 if isNeg else 1)
   else:
      lhs,rhs = coinStrPos.strip().split('.')
      if len(lhs.strip('-'))==0:
         lhs='0'
      if len(rhs)>maxDec and not roundHighPrec:
         raise TooMuchPrecisionError
      if not negAllowed and isNeg:
         raise NegativeValueError
      fullInt = (int(lhs + rhs[:9].ljust(9,'0')) + 5) / 10
      return fullInt*(-1 if isNeg else 1)


################################################################################
# A bunch of convenience methods for converting between:
#  -- Raw binary scripts (as seen in the blockchain)
#  -- Address strings (exchanged between people for paying each other)
#  -- ScrAddr strings (A unique identifier used by the DB)
################################################################################

################################################################################
# Convert a 20-byte hash to a "pay-to-public-key-hash" script to be inserted
# into a TxOut script
def hash160_to_p2pkhash_script(binStr20):
   if not len(binStr20)==20:
      raise InvalidHashError('Tried to convert non-20-byte str to p2pkh script')

   from Transaction import getOpCode
   from Script import scriptPushData
   outScript = ''.join([  getOpCode('OP_DUP'        ), \
                          getOpCode('OP_HASH160'    ), \
                          scriptPushData(binStr20),
                          getOpCode('OP_EQUALVERIFY'), \
                          getOpCode('OP_CHECKSIG'   )])
   return outScript


################################################################################
# Convert a 20-byte hash to a "pay-to-script-hash" script to be inserted
# into a TxOut script
def hash160_to_p2sh_script(binStr20):
   if not len(binStr20)==20:
      raise InvalidHashError('Tried to convert non-20-byte str to p2sh script')

   from Transaction import getOpCode
   from Script import scriptPushData
   outScript = ''.join([  getOpCode('OP_HASH160'),
                          scriptPushData(binStr20),
                          getOpCode('OP_EQUAL')])
   return outScript

################################################################################
# Convert an arbitrary script into a P2SH script
def script_to_p2sh_script(binScript):
   scriptHash = hash160(binScript)
   return hash160_to_p2sh_script(scriptHash)


################################################################################
# Convert a 33-byte or 65-byte hash to a "pay-to-pubkey" script to be inserted
# into a TxOut script
def pubkey_to_p2pk_script(binStr33or65):

   if not len(binStr33or65) in [33, 65]:
      raise KeyDataError('Invalid public key supplied to p2pk script')

   from Transaction import getOpCode
   from Script import scriptPushData
   serPubKey = scriptPushData(binStr33or65)
   outScript = serPubKey + getOpCode('OP_CHECKSIG')
   return outScript


################################################################################
# Convert a list of public keys to an OP_CHECKMULTISIG script.  There will be
# use cases where we require the keys to be sorted lexicographically, so we
# will do that by default.  If you require a different order, pre-sort them
# and pass withSort=False.
#
# NOTE:  About the hardcoded bytes in here: the mainnet addrByte and P2SH
#        bytes are hardcoded into DB format.  This means that
#        that any ScrAddr object will use the mainnet prefix bytes, regardless
#        of whether it is in testnet.
def pubkeylist_to_multisig_script(pkList, M, withSort=True):

   if sum([  (0 if len(pk) in [33,65] else 1)   for pk in pkList]) > 0:
      raise KeyDataError('Not all strings in pkList are 33 or 65 bytes!')

   from Transaction import getOpCode
   opM = getOpCode('OP_%d' % M)
   opN = getOpCode('OP_%d' % len(pkList))

   newPkList = pkList[:] # copy
   if withSort:
      newPkList = sorted(pkList)

   outScript = opM
   for pk in newPkList:
      outScript += int_to_binary(len(pk), widthBytes=1)
      outScript += pk
   outScript += opN
   outScript += getOpCode('OP_CHECKMULTISIG')

   return outScript

################################################################################
def scrAddr_to_script(scraddr):
   """
   Convert a scrAddr string (used by BDM) to the correct TxOut script
   Note this only works for P2PKH and P2SH scraddrs.  Multi-sig and
   all non-standard scripts cannot be derived from scrAddrs.  In a way,
   a scrAddr is intended to be an intelligent "hash" of the script,
   and it's a perk that most of the time we can reverse it to get the script.
   """
   if len(scraddr)==0:
      raise BadAddressError('_empty scraddr')

   prefix = scraddr[0]
   if not prefix in SCRADDR_BYTE_LIST or not len(scraddr)==21:
      LOGERROR('Bad scraddr: "%s"' % binary_to_hex(scraddr))
      raise BadAddressError('Invalid ScrAddress')

   if prefix==SCRADDR_P2PKH_BYTE:
      return hash160_to_p2pkhash_script(scraddr[1:])
   elif prefix==SCRADDR_P2SH_BYTE:
      return hash160_to_p2sh_script(scraddr[1:])
   else:
      LOGERROR('Unsupported scraddr type: "%s"' % binary_to_hex(scraddr))
      raise BadAddressError('Can only convert P2PKH and P2SH scripts')


################################################################################
def script_to_scrAddr(binScript):
   """ Convert a binary script to scrAddr string (used by BDM) """
   return BtcUtils().getScrAddrForScript(binScript)

################################################################################
def script_to_addrStr(binScript):
   """ Convert a binary script to scrAddr string (used by BDM) """
   return scrAddr_to_addrStr(script_to_scrAddr(binScript))

################################################################################
def scrAddr_to_addrStr(scrAddr):
   if len(scrAddr)==0:
      raise BadAddressError('_empty scrAddr')

   prefix = scrAddr[0]
   if not prefix in SCRADDR_BYTE_LIST or not len(scrAddr)==21:
      raise BadAddressError('Invalid ScrAddress')

   if prefix==SCRADDR_P2PKH_BYTE:
      return hash160_to_addrStr(scrAddr[1:])
   elif prefix==SCRADDR_P2SH_BYTE:
      return hash160_to_p2shAddrStr(scrAddr[1:])
   else:
      LOGERROR('Unsupported scrAddr type: "%s"' % binary_to_hex(scrAddr))
      raise BadAddressError('Can only convert P2PKH and P2SH scripts')

################################################################################
# We beat around the bush here, to make sure it goes through addrStr which
# triggers errors if this isn't a regular addr or P2SH addr
def scrAddr_to_hash160(scrAddr):
   addr = scrAddr_to_addrStr(scrAddr)
   atype, a160 = addrStr_to_hash160(addr)
   return (atype, a160)


################################################################################
def addrStr_to_scrAddr(addrStr):
   if not checkAddrStrValid(addrStr):
      BadAddressError('Invalid address: "%s"' % addrStr)

   atype, a160 = addrStr_to_hash160(addrStr)
   if atype==getAddrByte():
      return SCRADDR_P2PKH_BYTE + a160
   elif atype==getP2SHByte():
      return SCRADDR_P2SH_BYTE + a160
   else:
      BadAddressError('Invalid address: "%s"' % addrStr)


################################################################################
def addrStr_to_script(addrStr):
   """ Convert an addr string to a binary script """
   return scrAddr_to_script(addrStr_to_scrAddr(addrStr))


################################################################################
def hash160_to_scrAddr(a160):
   if not len(a160)==20:
      LOGERROR('Invalid hash160 value!')
      raise BadAddressError("a160 should be a 20 byte string: %s" % (a160,))
   return HASH160PREFIX + a160

################################################################################
# We need to have some methods for casting ASCII<->Unicode<->Preferred

def isASCII(theStr):
   try:
      theStr.decode('ascii')
      return True
   except UnicodeEncodeError:
      return False
   except UnicodeDecodeError:
      return False
   except:
      LOGEXCEPT('What was passed to this function? %s', theStr)
      return False


def toBytes(theStr, theEncoding=DEFAULT_ENCODING):
   if isinstance(theStr, unicode):
      return theStr.encode(theEncoding)
   elif isinstance(theStr, str):
      return theStr
   else:
      LOGERROR('toBytes() not been defined for input: %s', str(type(theStr)))


def toUnicode(theStr, theEncoding=DEFAULT_ENCODING):
   if isinstance(theStr, unicode):
      return theStr
   elif isinstance(theStr, str):
      return unicode(theStr, theEncoding)
   else:
      try:
         return unicode(theStr)
      except:
         LOGEXCEPT('toUnicode() not defined for %s', str(type(theStr)))


def lenBytes(theStr, theEncoding=DEFAULT_ENCODING):
   return len(toBytes(theStr, theEncoding))

# Stolen from stackoverflow (google "stackoverflow 1809531")
def unicode_truncate(theStr, length, encoding='utf-8'):
    encoded = theStr.encode(encoding)[:length]
    return encoded.decode(encoding, 'ignore')


# The database uses prefixes to identify type of address.  Until the new
# wallet format is created that supports more than just hash160 addresses
# we have to explicitly add the prefix to any hash160 values that are being
# sent to any of the C++ utilities.  For instance, the BlockDataManager (BDM)
# (C++ stuff) tracks regular hash160 addresses, P2SH, multisig, and all
# non-standard scripts.  Any such "scrAddrs" (script-addresses) will eventually
# be valid entities for tracking in a wallet.  Until then, all of our python
# utilities all use just hash160 values, and we manually add the prefix
# before talking to the BDM.
def CheckHash160(scrAddr):
   if not len(scrAddr)==21:
      raise BadAddressError("Supplied scrAddr is not a Hash160 value!")
   if not scrAddr[0] in [HASH160PREFIX, P2SHPREFIX]:
      raise BadAddressError("Supplied scrAddr is not a Hash160 value!")
   return scrAddr[1:]

def RightNowUTC():
   return time.mktime(time.gmtime(time.time()))

def RightNowStr(fmt=DEFAULT_DATE_FORMAT):
   return unixTimeToFormatStr(time.time(), fmt)

# Define all the hashing functions we're going to need.  We don't actually
# use any of the first three directly (sha1, sha256, ripemd160), we only
# use hash256 and hash160 which use the first three to create the ONLY hash
# operations we ever do in the bitcoin network
# UPDATE:  mini-private-key format requires vanilla sha256...
def sha1(bits):
   return hashlib.new('sha1', bits).digest()
def sha224(bits):
   return hashlib.new('sha224', bits).digest()
def sha256(bits):
   return hashlib.new('sha256', bits).digest()
def sha512(bits):
   return hashlib.new('sha512', bits).digest()
def ripemd160(bits):
   # It turns out that not all python has ripemd160...?
   #return hashlib.new('ripemd160', bits).digest()
   return BtcUtils().ripemd160_SWIG(bits)
def hash256(s):
   """ Double-SHA256 """
   return sha256(sha256(s))
def hash160(s):
   """ RIPEMD160( SHA256( binaryStr ) ) """
   return BtcUtils().getHash160_SWIG(s)


def _HMAC(key, msg, hashfunc=sha512, blocksize=None):
   """ This is intended to be simple, not fast.  For speed, use HDWalletCrypto() """
   blocksize = len(hashfunc('')) if blocksize==None else blocksize
   key = (hashfunc(key) if len(key)>blocksize else key)
   key = key.ljust(blocksize, '\x00')
   okey = ''.join([chr(ord('\x5c')^ord(c)) for c in key])
   ikey = ''.join([chr(ord('\x36')^ord(c)) for c in key])
   return hashfunc( okey + hashfunc(ikey + msg) )

# Armory 0.92 and earlier had a buggy _HMAC implementation...!
def HMAC256_buggy(key,msg):
   return _HMAC(key, msg, sha256,  32)

def HMAC512_buggy(key,msg):
   return _HMAC(key, msg, sha512,  64)

def HMAC256(key,msg):
   return _HMAC(key, msg, sha256,  64)

def HMAC512(key,msg):
   return _HMAC(key, msg, sha512, 128)

###############################################################################
def prettyHex(theStr, indent='', withAddr=True, major=8, minor=8):
   """
   This is the same as pprintHex(), but returns the string instead of
   printing it to console.  This is useful for redirecting output to
   files, or doing further modifications to the data before display
   """
   outStr = ''
   sz = len(theStr)
   nchunk = int((sz-1)/minor) + 1;
   for i in range(nchunk):
      if i%major==0:
         outStr += '\n'  + indent
         if withAddr:
            locStr = int_to_hex(i*minor/2, widthBytes=2, endOut=BIGENDIAN)
            outStr +=  '0x' + locStr + ':  '
      outStr += theStr[i*minor:(i+1)*minor] + ' '
   return outStr

################################################################################
def pprintHex(theStr, indent='', withAddr=True, major=8, minor=8):
   """
   This method takes in a long hex string and prints it out into rows
   of 64 hex chars, in chunks of 8 hex characters, and with address
   markings on each row.  This means that each row displays 32 bytes,
   which is usually pleasant.

   The format is customizable: you can adjust the indenting of the
   entire block, remove address markings, or change the major/minor
   grouping size (major * minor = hexCharsPerRow)
   """
   print prettyHex(theStr, indent, withAddr, major, minor)


##### Switch endian-ness #####
def hex_switchEndian(s):
   """ Switches the endianness of a hex string (in pairs of hex chars) """
   pairList = [s[i]+s[i+1] for i in xrange(0,len(s),2)]
   return ''.join(pairList[::-1])

def binary_switchEndian(s):
   """ Switches the endianness of a binary string """
   return s[::-1]


##### INT/HEXSTR #####
def int_to_hex(i, widthBytes=0, endOut=LITTLEENDIAN):
   """
   Convert an integer (int() or long()) to hexadecimal.  Default behavior is
   to use the smallest even number of hex characters necessary, and using
   little-endian.   Use the widthBytes argument to add 0-padding where needed
   if you are expecting constant-length output.
   """
   h = hex(i)[2:]
   if isinstance(i,long):
      h = h[:-1]
   if len(h)%2 == 1:
      h = '0'+h
   if not widthBytes==0:
      nZero = 2*widthBytes - len(h)
      if nZero > 0:
         h = '0'*nZero + h
   if endOut==LITTLEENDIAN:
      h = hex_switchEndian(h)
   return h


def hex_to_int(h, endIn=LITTLEENDIAN):
   """
   Convert hex-string to integer (or long).  Default behavior is to interpret
   hex string as little-endian
   """
   hstr = h.replace(' ','')  # copies data, no references
   if endIn==LITTLEENDIAN:
      hstr = hex_switchEndian(hstr)
   return( int(hstr, 16) )


##### HEXSTR/BINARYSTR #####
def hex_to_binary(h, endIn=LITTLEENDIAN, endOut=LITTLEENDIAN):
   """
   Converts hexadecimal to binary (in a python string).  Endianness is
   only switched if (endIn != endOut)
   """
   bout = h.replace(' ','')  # copies data, no references
   if not endIn==endOut:
      bout = hex_switchEndian(bout)
   return bout.decode('hex_codec')


def binary_to_hex(b, endOut=LITTLEENDIAN, endIn=LITTLEENDIAN):
   """
   Converts binary to hexadecimal.  Endianness is only switched
   if (endIn != endOut)
   """
   hout = b.encode('hex_codec')
   if not endOut==endIn:
      hout = hex_switchEndian(hout)
   return hout

##### INT/BINARYSTR #####
def int_to_binary(i, widthBytes=0, endOut=LITTLEENDIAN):
   """
   Convert integer to binary.  Default behavior is use as few bytes
   as necessary, and to use little-endian.  This can be changed with
   the two optional input arguemnts.
   """
   h = int_to_hex(i,widthBytes)
   return hex_to_binary(h, endOut=endOut)

def binary_to_int(b, endIn=LITTLEENDIAN):
   """
   Converts binary to integer (or long).  Interpret as LE by default
   """
   h = binary_to_hex(b, endIn, LITTLEENDIAN)
   return hex_to_int(h)

##### INT/BITS #####
# These two methods are deprecated in favor of the BitSet class
def int_to_bitset(i, widthBytes=0):
   bitsOut = []
   while i>0:
      i,r = divmod(i,2)
      bitsOut.append(['0','1'][r])
   result = ''.join(bitsOut)
   if widthBytes != 0:
      result = result.ljust(widthBytes*8,'0')
   return result

def bitset_to_int(bitset):
   n = 0
   for i,bit in enumerate(bitset):
      n += (0 if bit=='0' else 1) * 2**i
   return n


################################################################################
# BINARY/BASE58 CONVERSIONS
def binary_to_base58(binstr):
   """
   This method applies the Bitcoin-specific conversion from binary to Base58
   which may includes some extra "zero" bytes, such as is the case with the
   main-network addresses.

   This method is labeled as outputting an "addrStr", but it's really this
   special kind of Base58 converter, which makes it usable for encoding other
   data, such as ECDSA keys or scripts.
   """
   padding = 0;
   for b in binstr:
      if b=='\x00':
         padding+=1
      else:
         break

   n = 0
   for ch in binstr:
      n *= 256
      n += ord(ch)

   b58 = ''
   while n > 0:
      n, r = divmod (n, 58)
      b58 = BASE58CHARS[r] + b58
   return '1'*padding + b58


################################################################################
def base58_to_binary(addr):
   """
   This method applies the Bitcoin-specific conversion from Base58 to binary
   which may includes some extra "zero" bytes, such as is the case with the
   main-network addresses.

   This method is labeled as inputting an "addrStr", but it's really this
   special kind of Base58 converter, which makes it usable for encoding other
   data, such as ECDSA keys or scripts.
   """
   # Count the zeros ('1' characters) at the beginning
   padding = 0;
   for c in addr:
      if c=='1':
         padding+=1
      else:
         break

   n = 0
   for ch in addr:
      n *= 58
      if ch in BASE58CHARS:
         n += BASE58CHARS.index(ch)
      else:
         raise NonBase58CharacterError("Unrecognized Base 58 Character: %s" % ch)

   binOut = ''
   while n>0:
      d,m = divmod(n,256)
      binOut = chr(m) + binOut
      n = d
   return '\x00'*padding + binOut


################################################################################
def privKey_to_base58(binKey, compressed=False):
   '''Convert a 32-byte private key to the Satoshi client Base58 format.'''

   retBase58 = ''
   # For now, we don't support compressed private keys. (When we do, add
   # 0x01 after the private key when returning a private key.)
   try:
      compByte = ''
      if compressed:
         compByte = '\x01'
      privHashAddr = SecureBinaryData(getPrivKeyByte() + binKey + compByte)
      privHash256 = \
                    SecureBinaryData(hash256(privHashAddr.toBinStr())[0:4])
      privHashFinal = \
              SecureBinaryData(binary_to_base58(privHashAddr.toBinStr() + \
                                                privHash256.toBinStr()))
      retBase58 = privHashFinal.toBinStr()
   finally:
      privHashAddr.destroy()
      privHash256.destroy()
      privHashFinal.destroy()

   return retBase58


################################################################################
def hash160_to_addrStr(binStr, netbyte=None):
   """
   Converts the 20-byte pubKeyHash to 25-byte binary Bitcoin address
   which includes the network byte (prefix) and 4-byte checksum (suffix)
   """
   if netbyte is None:
      netbyte = getAddrByte()

   if not len(binStr) == 20:
      raise InvalidHashError('Input string is %d bytes' % len(binStr))

   addr21 = netbyte + binStr
   addr25 = addr21 + hash256(addr21)[:4]
   return binary_to_base58(addr25);

################################################################################
def hash160_to_p2shAddrStr(binStr):
   if not len(binStr) == 20:
      raise InvalidHashError('Input string is %d bytes' % len(binStr))

   addr21 = getP2SHByte() + binStr
   addr25 = addr21 + hash256(addr21)[:4]
   return binary_to_base58(addr25);

################################################################################
def binScript_to_p2shAddrStr(binScript):
   return hash160_to_p2shAddrStr(hash160(binScript))

################################################################################
def addrStr_is_p2sh(b58Str):
   if len(b58Str)==0:
      return False

   if sum([(0 if c in BASE58CHARS else 1) for c in b58Str]) > 0:
      return False

   binStr = base58_to_binary(b58Str)
   if not len(binStr)==25:
      return False

   if not hash256(binStr[:21])[:4] == binStr[-4:]:
      return False

   return (binStr[0] == getP2SHByte())

################################################################################
# As of version 0.90.1, this returns the prefix byte with the hash160.  This is
# because we need to handle/distinguish regular addresses from P2SH.  All code
# using this method must be updated to expect 2 outputs and check the prefix.
def addrStr_to_hash160(b58Str, p2shAllowed=True):
   binStr = base58_to_binary(b58Str)
   if not p2shAllowed and binStr[0]==getP2SHByte():
      raise P2SHNotSupportedError
   if not len(binStr) == 25:
      raise BadAddressError('Address string is %d bytes' % len(binStr))

   if not hash256(binStr[:21])[:4] == binStr[-4:]:
      raise ChecksumError('Address string has invalid checksum')

   if not binStr[0] in (getAddrByte(), getP2SHByte()):
      raise BadAddressError('Unknown addr prefix: %s' % binary_to_hex(binStr[0]))

   return (binStr[0], binStr[1:-4])


###### Typing-friendly Base16 #####
#  Implements "hexadecimal" encoding but using only easy-to-type
#  characters in the alphabet.  Hex usually includes the digits 0-9
#  which can be slow to type, even for good typists.  On the other
#  hand, by changing the alphabet to common, easily distinguishable,
#  lowercase characters, typing such strings will become dramatically
#  faster.  Additionally, some default encodings of QRCodes do not
#  preserve the capitalization of the letters, meaning that Base58
#  is not a feasible options

def binary_to_easyType16(binstr):
   return ''.join([HEX_TO_BASE16_MAP[c] for c in binary_to_hex(binstr)])

# Treat unrecognized characters as 0, to facilitate possibly later recovery of
# their correct values from the checksum.
def easyType16_to_binary(b16str):
   return hex_to_binary(''.join([BASE16_TO_HEX_MAP.get(c, '0') for c in b16str]))

def makeSixteenBytesEasy(b16):
   if not len(b16)==16:
      raise ValueError('Must supply 16-byte input')
   chk2 = computeChecksum(b16, nBytes=2)
   et18 = binary_to_easyType16(b16 + chk2)
   nineQuads = [et18[i*4:(i+1)*4] for i in range(9)]
   first4  = ' '.join(nineQuads[:4])
   second4 = ' '.join(nineQuads[4:8])
   last1   = nineQuads[8]
   return '  '.join([first4, second4, last1])

def readSixteenEasyBytes(et18):
   b18 = easyType16_to_binary(et18.strip().replace(' ',''))
   if len(b18)!=18:
      raise ValueError('Must supply 18-byte input')
   b16 = b18[:16]
   chk = b18[ 16:]
   if chk=='':
      LOGWARN('Missing checksum when reading EasyType')
      return (b16, 'No_Checksum')
   b16new = verifyChecksum(b16, chk)
   if len(b16new)==0:
      return ('','Error_2+')
   elif not b16new==b16:
      return (b16new,'Fixed_1')
   else:
      return (b16new,None)


# From https://en.bitcoin.it/wiki/Proper_Money_Handling_(JSON-RPC)
def JSONtoAmount(value):
   return long(round(float(value) * 1e8))
def AmountToJSON(amount):
   return float(amount / 1e8)


##### And a few useful utilities #####
def unixTimeToFormatStr(unixTime, formatStr=DEFAULT_DATE_FORMAT):
   """
   Converts a unix time (like those found in block headers) to a
   pleasant, human-readable format
   """
   dtobj = datetime.fromtimestamp(unixTime)
   dtstr = u'' + dtobj.strftime(formatStr).decode('utf-8')
   dtstr = dtstr.encode('ascii', errors='replace')
   return dtstr[:-2] + dtstr[-2:].lower()

def secondsToHumanTime(nSec):
   strPieces = []
   floatSec = float(nSec)
   if floatSec < 0.9*MINUTE:
      strPieces = [floatSec, 'second']
   elif floatSec < 0.9*HOUR:
      strPieces = [floatSec/MINUTE, 'minute']
   elif floatSec < 0.9*DAY:
      strPieces = [floatSec/HOUR, 'hour']
   elif floatSec < 0.9*WEEK:
      strPieces = [floatSec/DAY, 'day']
   elif floatSec < 0.9*MONTH:
      strPieces = [floatSec/WEEK, 'week']
   elif floatSec < 0.9*YEAR:
      strPieces = [floatSec/MONTH, 'month']
   else:
      strPieces = [floatSec/YEAR, 'year']

   if strPieces[0]<1.25:
      return '1 '+strPieces[1]
   elif strPieces[0]<=1.75:
      return '1.5 '+strPieces[1]+'s'
   else:
      return '%d %ss' % (int(strPieces[0]+0.5), strPieces[1])

def bytesToHumanSize(nBytes):
   if nBytes<KILOBYTE:
      return '%d bytes' % nBytes
   elif nBytes<MEGABYTE:
      return '%0.1f kB' % (nBytes/KILOBYTE)
   elif nBytes<GIGABYTE:
      return '%0.1f MB' % (nBytes/MEGABYTE)
   elif nBytes<TERABYTE:
      return '%0.1f GB' % (nBytes/GIGABYTE)
   elif nBytes<PETABYTE:
      return '%0.1f TB' % (nBytes/TERABYTE)
   else:
      return '%0.1f PB' % (nBytes/PETABYTE)


#############################################################################
def _fixChecksumError(binaryStr, chksum, hashFunc=hash256):
   """
   Will only try to correct one byte, as that would be the most
   common error case.  Correcting two bytes is feasible, but I'm
   not going to bother implementing it until I need it.  If it's
   not a one-byte error, it's most likely a different problem
   """
   for byte in range(len(binaryStr)):
      binaryArray = [binaryStr[i] for i in range(len(binaryStr))]
      for val in range(256):
         binaryArray[byte] = chr(val)
         if hashFunc(''.join(binaryArray)).startswith(chksum):
            return ''.join(binaryArray)

   return ''

#############################################################################
def computeChecksum(binaryStr, nBytes=4, hashFunc=hash256):
   return hashFunc(binaryStr)[:nBytes]


#############################################################################
def verifyChecksum(binaryStr, chksum, hashFunc=hash256, fixIfNecessary=True, \
                                                              beQuiet=False):
   """
   Any time we are given a value and its checksum, we can use
   this method to verify it is valid.  If it's not valid, we
   try to correct up to a one-byte error.  Beyond that, we assume
   that the error is caused by something other than RAM/HDD error.

   The return value is:
      -- No error      :  return input
      -- One byte error:  return input with fixed byte
      -- 2+ bytes error:  return ''

   This method will check the CHECKSUM ITSELF for errors, but not correct them.
   """
   bin1 = str(binaryStr)
   bin2 = binary_switchEndian(binaryStr)


   if hashFunc(bin1).startswith(chksum):
      return bin1
   elif hashFunc(bin2).startswith(chksum):
      if not beQuiet: LOGWARN( '***Checksum valid for input with reversed endianness')
      if fixIfNecessary:
         return bin2
   elif fixIfNecessary:
      if not beQuiet: LOGWARN('***Checksum error!  Attempting to fix...'),
      fixStr = _fixChecksumError(bin1, chksum, hashFunc)
      if len(fixStr)>0:
         if not beQuiet: LOGWARN('fixed!')
         return fixStr
      else:
         # ONE LAST CHECK SPECIFIC TO MY SERIALIZATION SCHEME:
         # If the string was originally all zeros, chksum is hash256('')
         # ...which is a known value, and frequently used in my files
         if chksum==hex_to_binary('5df6e0e2'):
            if not beQuiet: LOGWARN('fixed!')
            return ''


   # ID a checksum byte error...
   origHash = hashFunc(bin1)
   for i in range(len(chksum)):
      chkArray = [chksum[j] for j in range(len(chksum))]
      for ch in range(256):
         chkArray[i] = chr(ch)
         if origHash.startswith(''.join(chkArray)):
            LOGWARN('***Checksum error!  Incorrect byte in checksum!')
            return bin1

   LOGWARN('Checksum fix failed')
   return ''


#############################################################################
# Taken directly from rpc.cpp in reference bitcoin client, 0.3.24
def binaryBits_to_difficulty(b):
   """ Converts the 4-byte binary difficulty string to a float """
   i = binary_to_int(b)
   nShift = (i >> 24) & 0xff
   dDiff = float(0x0000ffff) / float(i & 0x00ffffff)
   while nShift < 29:
      dDiff *= 256.0
      nShift += 1
   while nShift > 29:
      dDiff /= 256.0
      nShift -= 1
   return dDiff


#############################################################################
def roundUpMod(val, mod):
   return ((int(val)- 1) / mod + 1) * mod


#############################################################################
def padString(s, mod, pad='\x00'):
   currSz = len(s)
   needSz = roundUpMod(currSz, mod)
   return s + pad*(needSz-currSz)

################################################################################
def CreateQRMatrix(dataToEncode, errLevel=QRErrorCorrectLevel.L):
   dataLen = len(dataToEncode)
   baseSz = 4 if errLevel == QRErrorCorrectLevel.L else \
            5 if errLevel == QRErrorCorrectLevel.M else \
            6 if errLevel == QRErrorCorrectLevel.Q else \
            7 # errLevel = QRErrorCorrectLevel.H
   sz = baseSz if dataLen < 70 else  5 +  (dataLen - 70) / 30
   qrmtrx = [[]]
   while sz<20:
      try:
         errCorrectEnum = getattr(QRErrorCorrectLevel, errLevel.upper())
         qr = QRCode(sz, errCorrectEnum)
         qr.addData(dataToEncode)
         qr.make()
         success=True
         break
      except OverflowError:
         sz += 1

   if not success:
      LOGERROR('Unsuccessful attempt to create QR code')
      LOGERROR('Data to encode: (Length: %s, isAscii: %s)', \
                     len(dataToEncode), isASCII(dataToEncode))
      return [[0]], 1

   qrmtrx = []
   modCt = qr.getModuleCount()
   for r in range(modCt):
      tempList = [0]*modCt
      for c in range(modCt):
         # The matrix is transposed by default, from what we normally expect
         tempList[c] = 1 if qr.isDark(c,r) else 0
      qrmtrx.append(tempList)

   return [qrmtrx, modCt]


################################################################################
def checkAddrType(addrBin):
   """ Gets the network byte of the address.  Returns -1 if chksum fails """
   first21, chk4 = addrBin[:-4], addrBin[-4:]
   chkBytes = hash256(first21)
   return addrBin[0] if (chkBytes[:4] == chk4) else -1

################################################################################
def _checkAddrBinValid(addrBin, validPrefixes=None):
   """
   Checks whether this address is valid for the given network
   (set at the top of pybtcengine.py)
   """
   if validPrefixes is None:
      validPrefixes = [getAddrByte(), getP2SHByte()]

   if not isinstance(validPrefixes, list):
      validPrefixes = [validPrefixes]

   return (checkAddrType(addrBin) in validPrefixes)


################################################################################
def checkAddrStrValid(addrStr):
   """ Check that a Base58 address-string is valid on this network """
   return _checkAddrBinValid(base58_to_binary(addrStr))


################################################################################
def convertKeyDataToAddress(privKey=None, pubKey=None):
   """ Returns a hash160 value """
   if not privKey and not pubKey:
      raise BadAddressError('No key data supplied for conversion')
   elif privKey:
      if isinstance(privKey, str):
         privKey = SecureBinaryData(privKey)

      if not privKey.getSize()==32:
         raise BadAddressError('Invalid private key format!')
      else:
         pubKey = CryptoECDSA().ComputePublicKey(privKey)

   if isinstance(pubKey,str):
      pubKey = SecureBinaryData(pubKey)
   return pubKey.getHash160().toBinStr()



################################################################################
def _decodeMiniPrivateKey(keyStr):
   """
   Converts a 22, 26 or 30-character Base58 mini private key into a
   32-byte binary private key.
   """
   if not len(keyStr) in (22,26,30):
      return ''

   keyQ = keyStr + '?'
   theHash = sha256(keyQ)

   if binary_to_hex(theHash[0]) == '01':
      raise KeyDataError('PBKDF2-based mini private keys not supported!')
   elif binary_to_hex(theHash[0]) != '00':
      raise KeyDataError('Invalid mini private key... double check the entry')

   return sha256(keyStr)

################################################################################
def parseBip32KeyData(theStr, verifyPub=True):
   from BinaryPacker import BinaryUnpacker
   if not isLikelyDataType(theStr, DATATYPE.Base58):
      raise KeyDataError('Invalid BIP32 priv key format; not base58')

   binStr = base58_to_binary(theStr)
   if not len(binStr)==82:
      raise KeyDataError('Invalid BIP32 key serialize format; not 78+chk bytes')

   if not theStr[:4] in ['tprv','tpub','xprv','xpub']:
      raise KeyDataError('Invalid BIP32 key serialize format; wrong type bytes')

   binStr = base58_to_binary(theStr)
   bytes78,chk = binStr[:78],binStr[-4:]
   bytes78 = verifyChecksum(bytes78, chk)
   if len(bytes78)==0:
      raise KeyDataError('Unrecoverable checksum error')

   output = {}
   toUnpack = BinaryUnpacker(bytes78)
   ignoreData           = toUnpack.get(UINT32)  # xpub/tpub/xprv/tprv
   output['childDepth'] = toUnpack.get(UINT8)
   output['parFinger']  = toUnpack.get(BINARY_CHUNK, 4)
   output['childIndex'] = toUnpack.get(UINT32)
   output['chaincode']  = toUnpack.get(BINARY_CHUNK, 32)
   output['keyData']    = toUnpack.get(BINARY_CHUNK, 33)
   output['getTestnetFlag']  = theStr[:4] in ['tprv','tpub']
   output['isPublic']   = theStr[:4] in ['xpub','tpub']

   if output['isPublic']:
      sbdPubkCompressed = SecureBinaryData(output['keyData'])
      if not CryptoECDSA().VerifyPublicKeyValid(sbdPubkCompressed):
         raise KeyDataError('Not a valid public key!')

   return output


################################################################################
def parsePrivateKeyData(theStr, privkeybyte=None):
   """
   This handles most standard formats for private keys, including raw hex,
   sipa/wif format, xprv/tprv, and a few related serialization types

   This returns the raw private key, 32 bytes if uncompressed, 33 bytes ending
   with \x01 if compressed (calling code must check for this).  The second
   output is a string that can be displayed identifying the key type.
   """

   if privkeybyte is None:
      privkeybyte = getPrivKeyByte()

   # xprv/tprv keys are recognizable right away, do it immediately
   if len(theStr)>=4 and theStr[:4] in ['tprv','tpub','xprv','xpub']:
      bip32keymap = parseBip32KeyData(theStr)
      if bip32keymap['getTestnetFlag'] != getTestnetFlag():
         raise NetworkIDError('Key is for wrong network!')
      if bip32keymap['isPublic']:
         raise KeyDataError('Attempted to parse public key as a private key!')

      # Remove leading 0x00 byte which only identifies it's a priv key, add
      # a 0x01 byte to tell the caller this key requires using compressed pub
      privKey = bip32keymap['keyData'][1:] + '\x01'
      return privKey, 'BIP32 Private Key (%s)' % theStr[:4]


   # Now do all the other stuff
   hexChars = '01234567890abcdef'
   b58Chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

   hexCount = sum([1 if c in hexChars else 0 for c in theStr.lower()])
   b58Count = sum([1 if c in b58Chars else 0 for c in theStr])
   canBeHex = hexCount==len(theStr)
   canBeB58 = b58Count==len(theStr)

   binEntry = ''
   keyType = ''

   if canBeB58 and not canBeHex:
      if len(theStr) in (22, 30):
         # Mini-private key format!
         binEntry = _decodeMiniPrivateKey(theStr)
         keyType = 'Mini Private Key'
         return binEntry, keyType
      elif len(theStr) in [49,50,51,52]:
         binEntry = base58_to_binary(theStr)
         keyType = 'Base58'
      else:
         raise BadAddressError('Unrecognized key data')
   elif canBeHex:
      binEntry = hex_to_binary(theStr)
      keyType = 'hex'
   else:
      raise BadAddressError('Unrecognized key data')


   if len(binEntry)==37 and binEntry[0]==privkeybyte:
      # Assume leading 0x80 byte, and 4 byte checksum
      keydata = binEntry[ :1+32 ]
      chk     = binEntry[  1+32:]
      binEntry = verifyChecksum(keydata, chk)
      if len(binEntry)==0:
         raise InvalidHashError('Private Key checksum failed!')
      binEntry = binEntry[1:]
      keyType = 'Standard %s key with checksum' % keyType
   elif len(binEntry)==38 and [binEntry[0],binEntry[-5]] ==[privkeybyte,'\x01']:
      # Assume leading 0x80 byte, and 4 byte checksum
      keydata = binEntry[ :1+33 ]
      chk     = binEntry[  1+33:]
      binEntry = verifyChecksum(keydata, chk)
      if len(binEntry)==0:
         raise InvalidHashError('Private Key checksum failed!')
      binEntry = binEntry[1:]
      keyType = 'Standard %s key (compressed pub) with checksum' % keyType
   elif len(binEntry)==33 and binEntry[-1]=='\x01':
      # Leave the extra byte to be extra sure the calling codes knows
      keyType = 'Plain %s key (compressed pub)' % keyType
   #elif len(binEntry)==37 and binEntry[-5]=='\x01':
      # Leave the extra byte to be extra sure the calling codes knows
      #binEntry = binEntry[:33]
      #keyType = 'Plain %s key (compressed pub) with checksum' % keyType

   return binEntry, keyType


################################################################################
def encodePrivKeyBase58(privKeyBin, isCompressed=False):
   binPriv = getPrivKeyByte() + privKeyBin + ('\x01' if isCompressed else '')
   chk = computeChecksum(binPriv)
   return binary_to_base58(binPriv + chk)


################################################################################
# Take in a "bitcoin:" URI string and parse the data out into a dictionary. If
# the URI isn't a Bitcoin URI, return an empty dictionary.
def parseBitcoinURI(uriStr):
   """ Takes a URI string, returns normalized dicitonary with pieces """
   data = {}

   # Split URI into parts. Let Python do the heavy lifting.
   from urlparse import urlparse, parse_qs
   uri = urlparse(uriStr)
   query = parse_qs(uri.query)

   # If query entry has only 1 entry, flatten and remove entry from array.
   for k in query:
      v = query[k]
      if len(v) == 1:
         query[k] = v[0]

   # Now start walking through the parts and get the info out of it.
   if uri.scheme == 'bitcoin':
      data['address'] = uri.path

      # Apply filters to known keys. Do NOT filter based on the "req-"
      # prefix from BIP21. Leave that to code using the dict.
      for k in query:
         v = query[k]
         kl = k.lower()
         if kl == 'amount':
            data['amount'] = str2coin(v) # Convert to Satoshis
         else:
            data[k] = v

   return data


################################################################################
def _uriEncode(theStr):
   """
   Convert from a regular string to a percent-encoded string
   """
   #Must replace '%' first, to avoid recursive (and incorrect) replacement!
   reserved = "%!*'();:@&=+$,/?#[]\" "

   for c in reserved:
      theStr = theStr.replace(c, '%%%s' % int_to_hex(ord(c)))
   return theStr


################################################################################
def createBitcoinURI(addr, amt=None, msg=None):
   uriStr = 'bitcoin:%s' % addr
   if amt or msg:
      uriStr += '?'

   if amt:
      uriStr += 'amount=%s' % coin2str(amt, maxZeros=0).strip()

   if amt and msg:
      uriStr += '&'

   if msg:
      uriStr += 'label=%s' % _uriEncode(msg)

   return uriStr


################################################################################
def createDERSigFromRS(rBin, sBin):
   # Remove all leading zero-bytes (why didn't we use lstrip() here?)
   while rBin[0]=='\x00':
      rBin = rBin[1:]
   while sBin[0]=='\x00':
      sBin = sBin[1:]

   if binary_to_int(rBin[0])&128>0:  rBin = '\x00'+rBin
   if binary_to_int(sBin[0])&128>0:  sBin = '\x00'+sBin
   rSize  = int_to_binary(len(rBin))
   sSize  = int_to_binary(len(sBin))
   rsSize = int_to_binary(len(rBin) + len(sBin) + 4)
   sigScript = '\x30' + rsSize + \
               '\x02' + rSize + rBin + \
               '\x02' + sSize + sBin
   return sigScript


################################################################################
def getRSFromDERSig(derSig):
   if not isinstance(derSig, str):
      # In case this is a SecureBinaryData object...
      derSig = derSig.toBinStr()

   codeByte = derSig[0]
   nBytes   = binary_to_int(derSig[1])
   rsStr    = derSig[2:2+nBytes]
   assert(codeByte == '\x30')
   assert(nBytes == len(rsStr))
   # Read r
   codeByte  = rsStr[0]
   rBytes    = binary_to_int(rsStr[1])
   r         = rsStr[2:2+rBytes]
   assert(codeByte == '\x02')
   sStr      = rsStr[2+rBytes:]
   # Read s
   codeByte  = sStr[0]
   sBytes    = binary_to_int(sStr[1])
   s         = sStr[2:2+sBytes]
   assert(codeByte == '\x02')
   # Now we have the (r,s) values of the

   rFinal = r.lstrip('\x00').rjust(32, '\x00')
   sFinal = s.lstrip('\x00').rjust(32, '\x00')
   return rFinal, sFinal


def emptyFunc(*args, **kwargs):
   return


def EstimateCumulativeBlockchainSize(blkNum):
   # I tried to make a "static" variable here so that
   # the string wouldn't be parsed on every call, but
   # I botched that, somehow.
   #
   # It doesn't *have to* be fast, but why not?
   # Oh well..
   blksizefile = """
         0 285
         20160 4496226
         40320 9329049
         60480 16637208
         80640 31572990
         82656 33260320
         84672 35330575
         86688 36815335
         88704 38386205
         100800 60605119
         102816 64795352
         104832 68697265
         108864 79339447
         112896 92608525
         116928 116560952
         120960 140607929
         124992 170059586
         129024 217718109
         133056 303977266
         137088 405836779
         141120 500934468
         145152 593217668
         149184 673064617
         153216 745173386
         157248 816675650
         161280 886105443
         165312 970660768
         169344 1058290613
         173376 1140721593
         177408 1240616018
         179424 1306862029
         181440 1463634913
         183456 1639027360
         185472 1868851317
         187488 2019397056
         189504 2173291204
         191520 2352873908
         193536 2530862533
         195552 2744361593
         197568 2936684028
         199584 3115432617
         201600 3282437367
         203616 3490737816
         205632 3669806064
         207648 3848901149
         209664 4064972247
         211680 4278148686
         213696 4557787597
         215712 4786120879
         217728 5111707340
         219744 5419128115
         221760 5733907456
         223776 6053668460
         225792 6407870776
         227808 6652067986
         228534 6778529822
         257568 10838081536
         259542 11106516992
         271827 12968787968
         286296 15619588096
         290715 16626221056
         323285 24216006308
      """
   strList = [line.strip().split() for line in blksizefile.strip().split('\n')]
   BLK_SIZE_LIST = [[int(x[0]), int(x[1])] for x in strList]

   if blkNum < BLK_SIZE_LIST[-1][0]:
      # Interpolate
      bprev,bcurr = None, None
      for i,blkpair in enumerate(BLK_SIZE_LIST):
         if blkNum < blkpair[0]:
            b0,d0 = BLK_SIZE_LIST[i-1]
            b1,d1 = blkpair
            ratio = float(blkNum-b0)/float(b1-b0)
            return int(ratio*d1 + (1-ratio)*d0)
      raise ValueError('Interpolation failed for %d' % blkNum)

   else:
      bend,  dend  = BLK_SIZE_LIST[-1]
      bend2, dend2 = BLK_SIZE_LIST[-3]
      rate = float(dend - dend2) / float(bend - bend2)  # bytes per block
      extraOnTop = (blkNum - bend) * rate
      return dend+extraOnTop


################################################################################
# Function checks to see if a binary value that's passed in is a valid public
# key. The incoming key may be binary or hex. The return value is a boolean
# indicating whether or not the key is valid.
def isValidPK(inPK, inStr=False):
   retVal = False
   checkVal = '\x00'

   if inStr:
      checkVal = hex_to_binary(inPK)
   else:
      checkVal = inPK
   pkLen = len(checkVal)

   if pkLen == UNCOMP_PK_LEN or pkLen == COMP_PK_LEN:
      # The "proper" way to check the key is to feed it to Crypto++.
      if not CryptoECDSA().VerifyPublicKeyValid(SecureBinaryData(checkVal)):
         LOGWARN('Pub key %s is invalid.' % binary_to_hex(inPK))
      else:
         retVal = True
   else:
      LOGWARN('Pub key %s has an invalid length (%d bytes).' % \
              (len(inPK), binary_to_hex(inPK)))

   return retVal


################################################################################
# Function that extracts IDs from a given text block and returns a list of all
# the IDs. The format should follow the example below, with "12345678" and
# "AbCdEfGh" being the IDs, and "LOCKBOX" being the key. There may be extra
# newline characters. The characters will be ignored.
#
# =====LOCKBOX-12345678=====================================================
# ckhc3hqhhuih7gGGOUT78hweds
# ==========================================================================
# =====LOCKBOX-AbCdEfGh=====================================================
# ckhc3hqhhuih7gGGOUT78hweds
# ==========================================================================
#
# In addition, the incoming block of text must be from a file (using something
# like "with open() as x") or a StringIO/cStringIO object.
def getBlockID(asciiText, key):
   blockList = []

   # Iterate over each line in the text and get the IDs.
   for line in asciiText:
      if key in line:
         stripT = line.replace("=", "").replace(key, "").replace("\n", "")
         blockList.append(stripT)

   return blockList

################################################################################
# Function that can be used to send an e-mail to multiple recipients.
def send_email(send_from, server, password,
               send_to, subject, text, usebasic=False):
   # smtp.sendmail() requires a list of recipients. If we didn't get a list,
   # create one, and delimit based on a colon.
   if not type(send_to) == list:
      send_to = send_to.split(":")

   # Split the server info. Also, use a default port in case the user goofed and
   # didn't specify a port.
   server = server.split(":")
   serverAddr = server[0]
   serverPort = 587
   if len(server) > 1:
      serverPort = int(server[1])

   # Some of this may have to be modded to support non-TLS servers.
   msg = MIMEMultipart()
   msg['From'] = send_from
   msg['To'] = COMMASPACE.join(send_to)
   msg['Date'] = formatdate(localtime=True)
   msg['Subject'] = subject
   msg.attach(MIMEText(text))
   mailServer = smtplib.SMTP(serverAddr, serverPort)
   mailServer.ehlo()
   if not usebasic:
      mailServer.starttls()
   mailServer.ehlo()
   if not usebasic:
      mailServer.login(send_from, password)
   mailServer.sendmail(send_from, send_to, msg.as_string())
   mailServer.close()


#############################################################################
def DeriveChaincodeFromRootKey_135(sbdPrivKey):
   # The original 1.35 wallets use an HMAC256 implementation that had an
   # incorrect constant.  Apparently no one else tried to replicate the
   # process with an independent crypto library.   The end result is that
   # we must keep the buggy implementation with us for as long as we keep
   # supporting Armory 1.35 wallets.
   return SecureBinaryData( HMAC256_buggy( hash256(sbdPrivKey.toBinStr()), \
                                     'Derive Chaincode from Root Key') )


#############################################################################
def getLastBytesOfFile(filename, nBytes=500*KILOBYTE):
   if not os.path.exists(filename):
      LOGERROR('File does not exist!')
      return ''

   sz = os.path.getsize(filename)
   with open(filename, 'rb') as fin:
      if sz > nBytes:
         fin.seek(sz - nBytes)
      return fin.read()


################################################################################
def HardcodedKeyMaskParams():
   paramMap = {}

   # Nothing up my sleeve!  Need some hardcoded random numbers to use for
   # encryption IV and salt.  Using the first 256 digits of Pi for the
   # the IV, and first 256 digits of e for the salt (hashed)
   digits_pi = ( \
      'ARMORY_ENCRYPTION_INITIALIZATION_VECTOR_'
      '1415926535897932384626433832795028841971693993751058209749445923'
      '0781640628620899862803482534211706798214808651328230664709384460'
      '9550582231725359408128481117450284102701938521105559644622948954'
      '9303819644288109756659334461284756482337867831652712019091456485')
   digits_e = ( \
      'ARMORY_KEY_DERIVATION_FUNCTION_SALT_'
      '7182818284590452353602874713526624977572470936999595749669676277'
      '2407663035354759457138217852516642742746639193200305992181741359'
      '6629043572900334295260595630738132328627943490763233829880753195'
      '2510190115738341879307021540891499348841675092447614606680822648')

   paramMap['IV']    = SecureBinaryData( hash256(digits_pi)[:16] )
   paramMap['SALT']  = SecureBinaryData( hash256(digits_e) )
   paramMap['KDFBYTES'] = long(16*MEGABYTE)

   def hardcodeCreateSecurePrintPassphrase(secret):
      if isinstance(secret, basestring):
         secret = SecureBinaryData(secret)
      bin7 = HMAC512_buggy(secret.getHash256().toBinStr(), paramMap['SALT'].toBinStr())[:7]
      out,bin7 = SecureBinaryData(binary_to_base58(bin7 + hash256(bin7)[0])), None
      return out

   def hardcodeCheckSecurePrintCode(securePrintCode):
      if isinstance(securePrintCode, basestring):
         pwd = base58_to_binary(securePrintCode)
      else:
         pwd = base58_to_binary(securePrintCode.toBinStr())

      isgood,pwd = (hash256(pwd[:7])[0] == pwd[-1]), None
      return isgood

   def hardcodeApplyKdf(secret):
      if isinstance(secret, basestring):
         secret = SecureBinaryData(secret)
      kdf = KdfRomix()
      kdf.usePrecomputedKdfParams(paramMap['KDFBYTES'], 1, paramMap['SALT'])
      return kdf.DeriveKey(secret)

   def hardcodeMask(secret, passphrase=None, ekey=None):
      if not ekey:
         ekey = hardcodeApplyKdf(passphrase)
      return CryptoAES().EncryptCBC(secret, ekey, paramMap['IV'])

   def hardcodeUnmask(secret, passphrase=None, ekey=None):
      if not ekey:
         ekey = hardcodeApplyKdf(passphrase)
      return CryptoAES().DecryptCBC(secret, ekey, paramMap['IV'])

   paramMap['FUNC_PWD']    = hardcodeCreateSecurePrintPassphrase
   paramMap['FUNC_KDF']    = hardcodeApplyKdf
   paramMap['FUNC_MASK']   = hardcodeMask
   paramMap['FUNC_UNMASK'] = hardcodeUnmask
   paramMap['FUNC_CHKPWD'] = hardcodeCheckSecurePrintCode
   return paramMap

################################################################################
# Random method for creating
def touchFile(fname):
   try:
      os.utime(fname, None)
   except:
      f = open(fname, 'a')
      f.flush()
      os.fsync(f.fileno())
      f.close()


# Check general internet connection
# Do not Check when ForceOnline is true
def isInternetAvailable(forceOnline = False):
   internetStatus = INTERNET_STATUS.Unavailable
   if forceOnline:
      internetStatus = INTERNET_STATUS.DidNotCheck
   else:
      try:
         import urllib2
         urllib2.urlopen(ALWAYS_OPEN_URL, timeout=getNetTimeout())
         internetStatus = INTERNET_STATUS.Available
      except ImportError:
         LOGERROR('No module urllib2 -- cannot determine if internet is '
            'available')
      except urllib2.URLError:
         # In the extremely rare case that google might be down (or just to try
         # again...)
         try:
            urllib2.urlopen(ALWAYS_OPEN_URL2, timeout=getNetTimeout())
            internetStatus = INTERNET_STATUS.Available
         except:
            LOGEXCEPT('Error checking for internet connection')
            LOGERROR('Run --skip-online-check if you think this is an error')
      except:
         LOGEXCEPT('Error checking for internet connection')
         LOGERROR('Run --skip-online-check if you think this is an error')

   return internetStatus


#############################################################################
def satoshiIsAvailable(host='127.0.0.1', port=None, timeout=0.01):

   if port is None:
      port = getBitcoinPort()

   if not isinstance(port, (list,tuple)):
      port = [port]

   for p in port:
      s = socket.socket()
      s.settimeout(timeout)   # Most of the time checking localhost -- FAST
      try:
         s.connect((host, p))
         s.close()
         return p
      except:
         pass

   return 0


# Returns true if Online Mode is possible
def onlineModeIsPossible(btcdir=None):
   if btcdir is None:
      btcdir = getBitcoinHomeDir()
   return isInternetAvailable(forceOnline=getForceOnlineFlag()) != \
                INTERNET_STATUS.Unavailable and \
                satoshiIsAvailable() and \
                os.path.exists(getBlockFileDir())

def _crc24(m):
   INIT = 0xB704CE
   POLY = 0x1864CFB
   crc = INIT
   r = ''
   for o in m:
      o=ord(o)
      crc ^= (o << 16)
      for i in xrange(8):
         crc <<= 1
         if crc & 0x1000000:
            crc ^= POLY
   for i in range(3):
      r += chr( ( crc & (0xff<<(8*i))) >> (8*i) )
   return r


def _chunks(t, n):
   return [t[i:i+n] for i in range(0, len(t), n)]

def readSigBlock(r):
   r = standardizeMessage(r, True)
   # Take the name off of the end because the BEGIN markers are confusing
   try:
      name = r.split(BEGIN_MARKER)[1].split(DASHX5)[0]
   except IndexError as e:
      LOGERROR("index looks bad for this message %s" % r)
      return
   if name == BASE64_MSG_TYPE_MARKER:
      encoded, crc = r.split(BEGIN_MARKER)[1].split(END_MARKER)[0].split(
         DASHX5)[1].strip().split('\n=')
      crc = crc.strip()
      # Always starts with a blank line (\r\n\r\n) chop that off
      # with the comment oand process the rest
      encoded = encoded.split(RNRN)[1]
      # Combines 64 byte chunks that are separated by \r\n
      encoded = ''.join(encoded.split(RN))
      # decode the message.
      decoded = base64.b64decode(encoded)
      # Check sum of decoded messgae
      if base64.b64decode(crc) != _crc24(decoded):
         raise ChecksumError
      # The signature is followed by the message and the whole thing is encoded
      # The message always starts at 65 because the signature is 65 bytes.
      signature = base64.b64encode(decoded[:65])
      msg = decoded[65:]
   elif name == CLEARSIGN_MSG_TYPE_MARKER:
      # First get rid of the Clearsign marker and everything before it in case
      # the user added extra lines that would confuse the parsing that follows
      # The message is preceded by a blank line (\r\n\r\n) chop that off
      # with the comment and process the rest
      # For Clearsign the message is unencoded since the message could
      # include the \r\n\r\n we only ignore
      # the first and combine the rest.
      msg = r.split(BEGIN_MARKER+CLEARSIGN_MSG_TYPE_MARKER+DASHX5)[1]
      msg = RNRN.join(msg.split(RNRN)[1:])
      msg = msg.split(RN+DASHX5)[0]
      # Only the signature is encoded, use the original r to pull out the
      # encoded signature
      encoded = r.split(BEGIN_MARKER)[2].split(DASHX5)[1].split(
         BITCOIN_SIG_TYPE_MARKER)[0]
      encoded, crc = encoded.split('\n=')
      encoded = ''.join(encoded.split('\n'))
      signature = ''.join(encoded.split('\r'))
      crc = crc.strip()
      if base64.b64decode(crc) != _crc24(base64.b64decode(signature)):
         raise ChecksumError
   else:
      raise UnknownSigBlockType()
   return signature, msg

def getEncodedBlock(marker, msg, addComment=False):
   lines = [
      BEGIN_MARKER + marker + DASHX5,
   ]
   if addComment:
      lines += [getComment(), '']
   lines += _chunks(base64.b64encode(msg), 64) + [
      '=' + base64.b64encode(_crc24(msg)),
      END_MARKER + marker + DASHX5,
   ]
   return RN.join(lines)

def getComment():
   return 'Comment: Signed by Bitcoin Armory v' + \
      getVersionString(BTCARMORY_VERSION, 3)

def standardizeMessage(msg, sigctx=False):
   lines = msg.split("\n")
   standardized = []
   for l in lines:
      n = l.rstrip()
      if not sigctx and len(n) and n[0] == '-':
         n = '- ' + n
      standardized.append(n)
         
   return RN.join(standardized)

def formatMessageToSign(msg):
   from BinaryPacker import BinaryPacker
   msgPrefix = 'Bitcoin Signed Message:\n'
   bp = BinaryPacker()
   bp.put(VAR_INT,  len(msgPrefix))
   bp.put(BINARY_CHUNK, msgPrefix)
   bp.put(VAR_INT,  len(msg))
   bp.put(BINARY_CHUNK, msg)
   return bp.getBinaryString()


def getMessagePubKey(sbdMsg, sbdSig):

   if sbdSig.getSize() != 65:
      raise RuntimeError("invalid signature size: %s" % sbdSig.getSize())

   fmt = formatMessageToSign(sbdMsg.toBinStr())
   sbdMsgHash = SecureBinaryData(hash256(fmt))
   pubKey = CryptoECDSA().GetPubKeyFromSigAndMsgHash(sbdSig, sbdMsgHash)

   sbdPub = CryptoECDSA().UncompressPoint(pubKey)
   sSig = SecureBinaryData(sbdSig.toBinStr()[1:])
   # sanity check
   sbdFmt = SecureBinaryData(fmt)
   if not CryptoECDSA().VerifyData(sbdFmt, sSig, sbdPub):
      raise RuntimeError("signature doesn't verify")
   return pubKey


def verifySignature(msg, b64sig):
   try:
      sig = base64.b64decode(b64sig)
      pk = getMessagePubKey(SecureBinaryData(msg), SecureBinaryData(sig))
   except Exception as e:
      LOGEXCEPT("exception %s" % e)
      return False
   addr = script_to_addrStr(pubkey_to_p2pk_script(pk.toBinStr()))
   return dict(message=msg,address=addr)


def verifySignedMessage(signedMsg):
   std = standardizeMessage(signedMsg, True)
   b64sig, msg = readSigBlock(std)
   return verifySignature(msg, b64sig)


def isLikelyDataType(theStr, dtype=None):
   """
   This really shouldn't be used on short strings.  Hence
   why it's called "likely" datatype...
   """
   ret = None
   hexCount = sum([1 if c in BASE16CHARS else 0 for c in theStr])
   b58Count = sum([1 if c in BASE58CHARS else 0 for c in theStr])
   canBeHex = hexCount==len(theStr)
   canBeB58 = b58Count==len(theStr)
   if canBeHex:
      ret = DATATYPE.Hex
   elif canBeB58 and not canBeHex:
      ret = DATATYPE.Base58
   else:
      ret = DATATYPE.Binary

   if dtype==None:
      return ret
   else:
      return dtype==ret


def calcWalletID(secret):
   """
   Calculates what would be the walletID given secret is the seed
   """
   from ArmoryKeyPair import ABEK_BIP44Seed
   root = ABEK_BIP44Seed()
   root.initializeFromSeed(SecureBinaryData(secret), fsync=False)
   return root.uniqueIDB58

################################################################################
# Get system details for logging purposes

def _getSystemDetails():
   """Checks memory of a given system"""

   CPU,COR,X64,MEM = range(4)
   sysParam = [None,None,None,None]
   setCPU('Unknown')
   setMachine(platform.machine().lower())
   if isLinux():
      # Get total RAM
      freeStr = subprocess.check_output('free -m', shell=True)
      totalMemory = freeStr.split('\n')[1].split()[1]
      setMemory(int(totalMemory) * 1024)

      # Get CPU name
      cpuinfo = subprocess.check_output(['cat','/proc/cpuinfo'])
      for line in cpuinfo.split('\n'):
         if line.strip().lower().startswith('model name'):
            setCPU(line.split(':')[1].strip())
            break

   elif isWindows():
      import ctypes
      class MEMORYSTATUSEX(ctypes.Structure):
         _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
         ]
         def __init__(self):
            # have to initialize this to the size of MEMORYSTATUSEX
            self.dwLength = ctypes.sizeof(self)
            super(MEMORYSTATUSEX, self).__init__()

      stat = MEMORYSTATUSEX()
      ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
      setMemory(stat.ullTotalPhys/1024.)
      setCPU(platform.processor())
   elif isMac():
      memsizeStr = subprocess.check_output('sysctl hw.memsize', shell=True)
      setMemory(int(memsizeStr.split(": ")[1]) / 1024)
      setCPU(subprocess.check_output(
         'sysctl -n machdep.cpu.brand_string', shell=True))
   else:
      raise OSError("Can't get system specs in: %s" % platform.system())

   setNumCores(multiprocessing.cpu_count())
   if isWindows():
      setX64Flag(platform.machine().lower() == 'amd64')
   else:
      setX64Flag(platform.machine().lower() == 'x86_64')
   setMemory(getMemory() / (1024*1024.))

   def getHddSize(adir):
      if isWindows():
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(adir), \
                                                   None, None, \
                                                   ctypes.pointer(free_bytes))
        return free_bytes.value
      else:
         s = os.statvfs(adir)
         return s.f_bavail * s.f_frsize
   setArmoryHDSpace(getHddSize(getArmoryHomeDir())  / (1024**3))
   setBitcoinHDSpace(getHddSize(getBitcoinHomeDir()) / (1024**3))

def initializeUtils():

   # show some basic information
   if getExecutedScript() == 'ArmoryQt.py':
      print getPrintableArmoryInfo()

   # delete anything from the previous load of the syystem
   _processDeletions()

   # add some console warnings
   _logTestAnnounce()
   _logTor()

   # get some system details
   try:
      _getSystemDetails()
   except Exception as e:
      LOGEXCEPT('Error getting system details: %s' % e)
      LOGERROR('Skipping.')
      setMemory(-1)
      setCPU('Unknown')
      setNumCores(-1)
      setX64Flag(None)
      setMachine(platform.machine().lower())
      setArmoryHDSpace(-1)
      setBitcoinHDSpace(-1)

   # show system details
   LOGINFO(_getArmoryDetailStr())


def initializeArmory():
   from BDM import initializeBDM
   initializeOptions()
   initializeLog()
   initializeBDM()
   initializeUtils()
