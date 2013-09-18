################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
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
from datetime import datetime
from struct import pack, unpack
import hashlib
import locale
import logging
import math
import optparse
import os
import platform
import sys
import time
import traceback

parser = optparse.OptionParser(usage="%prog [options]\n")
parser.add_option("--settings",        dest="settingsPath",default='DEFAULT', type="str",          help="load Armory with a specific settings file")
parser.add_option("--datadir",         dest="datadir",     default='DEFAULT', type="str",          help="Change the directory that Armory calls home")
parser.add_option("--satoshi-datadir", dest="satoshiHome", default='DEFAULT', type='str',          help="The Bitcoin-Qt/bitcoind home directory")
parser.add_option("--satoshi-port",    dest="satoshiPort", default='DEFAULT', type="str",          help="For Bitcoin-Qt instances operating on a non-standard port")
#parser.add_option("--bitcoind-path",   dest="bitcoindPath",default='DEFAULT', type="str",          help="Path to the location of bitcoind on your system")
parser.add_option("--rpcport",         dest="rpcport",     default='DEFAULT', type="str",          help="RPC port for running armoryd.py")
parser.add_option("--testnet",         dest="testnet",     default=False,     action="store_true", help="Use the testnet protocol")
parser.add_option("--offline",         dest="offline",     default=False,     action="store_true", help="Force Armory to run in offline mode")
parser.add_option("--nettimeout",      dest="nettimeout",  default=2,         type="int",          help="Timeout for detecting internet connection at startup")
parser.add_option("--interport",       dest="interport",   default=-1,        type="int",          help="Port for inter-process communication between Armory instances")
parser.add_option("--debug",           dest="doDebug",     default=False,     action="store_true", help="Increase amount of debugging output")
parser.add_option("--nologging",       dest="logDisable",  default=False,     action="store_true", help="Disable all logging")
parser.add_option("--netlog",          dest="netlog",      default=False,     action="store_true", help="Log networking messages sent and received by Armory")
parser.add_option("--logfile",         dest="logFile",     default='DEFAULT', type='str',          help="Specify a non-default location to send logging information")
parser.add_option("--mtdebug",         dest="mtdebug",     default=False,     action="store_true", help="Log multi-threaded call sequences")
parser.add_option("--skip-online-check", dest="forceOnline", default=False,   action="store_true", help="Go into online mode, even if internet connection isn't detected")
parser.add_option("--skip-version-check", dest="skipVerCheck", default=False, action="store_true", help="Do not contact bitcoinarmory.com to check for new versions")
parser.add_option("--keypool",         dest="keypool",     default=100, type="int",                help="Default number of addresses to lookahead in Armory wallets")
parser.add_option("--port", dest="port", default=None, type="int", help="Unit Test Argument - Do not consume")
parser.add_option("--verbosity", dest="verbosity", default=None, type="int", help="Unit Test Argument - Do not consume")
parser.add_option("--coverage_output_dir", dest="coverageOutputDir", default=None, type="str", help="Unit Test Argument - Do not consume")
parser.add_option("--coverage_include", dest="coverageInclude", default=None, type="str", help="Unit Test Argument - Do not consume")
parser.add_option("--rebuild",         dest="rebuild",     default=False,     action="store_true", help="Rebuild blockchain database and rescan")
parser.add_option("--rescan",          dest="rescan",      default=False,     action="store_true", help="Rescan existing blockchain DB")


class FiniteFieldError(Exception): pass
class BadAddressError(Exception): pass
class KeyDataError(Exception): pass
class InvalidHashError(Exception): pass
class CompressedKeyError(Exception): pass
class NegativeValueError(Exception): pass
class TooMuchPrecisionError(Exception): pass
class BadURIError(Exception): pass

#########  INITIALIZE LOGGING UTILITIES  ##########
#
# Setup logging to write INFO+ to file, and WARNING+ to console
# In debug mode, will write DEBUG+ to file and INFO+ to console
#
# Want to get the line in which an error was triggered, but by wrapping
# the logger function (as I will below), the displayed "file:linenum" 
# references the logger function, not the function that called it.
# So I use traceback to find the file and line number two up in the 
# stack trace, and return that to be displayed instead of default 
# [Is this a hack?  Yes and no.  I see no other way to do this]
def getCallerLine():
   stkTwoUp = traceback.extract_stack()[-3]
   filename,method = stkTwoUp[0], stkTwoUp[1]
   return '%s:%d' % (os.path.basename(filename),method)

(CLI_OPTIONS, CLI_ARGS) = parser.parse_args()

# Use CLI args to determine testnet or not
USE_TESTNET = CLI_OPTIONS.testnet

# Set default port for inter-process communication
if CLI_OPTIONS.interport < 0:
   CLI_OPTIONS.interport = 8223 + (1 if USE_TESTNET else 0)

# Get the host operating system
opsys = platform.system()
OS_WINDOWS = 'win32'  in opsys.lower() or 'windows' in opsys.lower()
OS_LINUX   = 'nix'    in opsys.lower() or 'nux'     in opsys.lower()
OS_MACOSX  = 'darwin' in opsys.lower() or 'osx'     in opsys.lower()

# Change the settings file to use
#BITCOIND_PATH = None
#if not CLI_OPTIONS.bitcoindPath.lower()=='default':
   #BITCOIND_PATH = CLI_OPTIONS.bitcoindPath

# Figure out the default directories for Satoshi client, and BicoinArmory
OS_NAME          = ''
OS_VARIANT       = ''
USER_HOME_DIR    = ''
BTC_HOME_DIR     = ''
ARMORY_HOME_DIR  = ''
SUBDIR = 'testnet3' if USE_TESTNET else ''
if OS_WINDOWS:
   OS_NAME         = 'Windows'
   OS_VARIANT      = platform.win32_ver()
   USER_HOME_DIR   = os.getenv('APPDATA')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, 'Bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, 'Armory', SUBDIR)
elif OS_LINUX:
   OS_NAME         = 'Linux'
   OS_VARIANT      = platform.linux_distribution()
   USER_HOME_DIR   = os.getenv('HOME')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, '.bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, '.armory', SUBDIR)
elif OS_MACOSX:
   platform.mac_ver()
   OS_NAME         = 'MacOSX'
   OS_VARIANT      = platform.mac_ver()
   USER_HOME_DIR   = os.path.expanduser('~/Library/Application Support')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, 'Bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, 'Armory', SUBDIR)
else:
   print '***Unknown operating system!'
   print '***Cannot determine default directory locations'

# Change the settings file to use
if CLI_OPTIONS.settingsPath.lower()=='default':
   CLI_OPTIONS.settingsPath = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt')

# Change the log file to use
if CLI_OPTIONS.logFile.lower()=='default':
   if sys.argv[0] in ['ArmoryQt.py', 'ArmoryQt.exe', 'Armory.exe']:
      CLI_OPTIONS.logFile = os.path.join(ARMORY_HOME_DIR, 'armorylog.txt')
   else:
      basename = os.path.basename(sys.argv[0])
      CLI_OPTIONS.logFile = os.path.join(ARMORY_HOME_DIR, '%s.log.txt' % basename)

SETTINGS_PATH   = CLI_OPTIONS.settingsPath
ARMORY_LOG_FILE = CLI_OPTIONS.logFile


DEFAULT_CONSOLE_LOGTHRESH = logging.WARNING
DEFAULT_FILE_LOGTHRESH    = logging.INFO

DEFAULT_PPRINT_LOGLEVEL   = logging.DEBUG
DEFAULT_RAWDATA_LOGLEVEL  = logging.DEBUG

################################################################################
# When there's an error in the logging function, it's impossible to find!
# These wrappers will print the full stack so that it's possible to find 
# which line triggered the error
def LOGDEBUG(msg, *a):
   try:
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = getCallerLine() + ' - '
      logging.debug(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

def LOGINFO(msg, *a):
   try:
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = getCallerLine() + ' - '
      logging.info(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGWARN(msg, *a):
   try:
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = getCallerLine() + ' - '
      logging.warn(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGERROR(msg, *a):
   try:
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = getCallerLine() + ' - '
      logging.error(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGCRIT(msg, *a):
   try:
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = getCallerLine() + ' - '
      logging.critical(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGEXCEPT(msg, *a):
   try:
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = getCallerLine() + ' - '
      logging.exception(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

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
    

def coin2strNZ(nSatoshi):
   """ Right-justified, minimum zeros, but with padding for alignment"""
   return coin2str(nSatoshi, 8, True, 0)

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
# Load the C++ utilites here
#
#    The SWIG/C++ block utilities give us access to the blockchain, fast ECDSA
#    operations, and general encryption/secure-binary containers
################################################################################
try:
   import CppBlockUtils as Cpp
   from CppBlockUtils import CryptoECDSA, SecureBinaryData
   LOGINFO('C++ block utilities loaded successfully')
except:
   LOGCRIT('C++ block utilities not available.')
   LOGCRIT('   Make sure that you have the SWIG-compiled modules')
   LOGCRIT('   in the current directory (or added to the PATH)')
   LOGCRIT('   Specifically, you need:')
   LOGCRIT('       CppBlockUtils.py     and')
   if OS_LINUX or OS_MACOSX:
      LOGCRIT('       _CppBlockUtils.so')
   elif OS_WINDOWS:
      LOGCRIT('       _CppBlockUtils.pyd')
   else:
      LOGCRIT('\n\n... UNKNOWN operating system')
   raise


################################################################################
# We need to have some methods for casting ASCII<->Unicode<->Preferred
DEFAULT_ENCODING = 'utf-8'

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
      LOGERROR('toUnicode() not been defined for input: %s', str(type(theStr)))


def toPreferred(theStr):
   return toUnicode(theStr).encode(locale.getpreferredencoding())


def lenBytes(theStr, theEncoding=DEFAULT_ENCODING):
   return len(toBytes(theStr, theEncoding))


rootLogger = logging.getLogger('')
if CLI_OPTIONS.doDebug or CLI_OPTIONS.netlog or CLI_OPTIONS.mtdebug:
   # Drop it all one level: console will see INFO, file will see DEBUG
   DEFAULT_CONSOLE_LOGTHRESH  -= 10
   DEFAULT_FILE_LOGTHRESH     -= 10


def chopLogFile(filename, size):
   if not os.path.exists(filename):
      print 'Log file doesn\'t exist [yet]'
      return

   logfile = open(filename, 'r')
   allLines = logfile.readlines()
   logfile.close()

   nBytes,nLines = 0,0;
   for line in allLines[::-1]:
      nBytes += len(line)
      nLines += 1
      if nBytes>size:
         break

   logfile = open(filename, 'w')
   for line in allLines[-nLines:]:
      logfile.write(line)
   logfile.close()



# Cut down the log file to just the most recent 1 MB
chopLogFile(ARMORY_LOG_FILE, 1024*1024)


# Now set loglevels
DateFormat = '%Y-%m-%d %H:%M'
logging.getLogger('').setLevel(logging.DEBUG)
fileFormatter  = logging.Formatter('%(asctime)s (%(levelname)s) -- %(message)s', \
                                     datefmt=DateFormat)
fileHandler = logging.FileHandler(ARMORY_LOG_FILE)
fileHandler.setLevel(DEFAULT_FILE_LOGTHRESH)
fileHandler.setFormatter(fileFormatter)
logging.getLogger('').addHandler(fileHandler)

consoleFormatter = logging.Formatter('(%(levelname)s) %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(DEFAULT_CONSOLE_LOGTHRESH)
consoleHandler.setFormatter( consoleFormatter )
logging.getLogger('').addHandler(consoleHandler)

      

class stringAggregator(object):
   def __init__(self):
      self.theStr = ''
   def getStr(self):
      return self.theStr
   def write(self, theStr):
      self.theStr += theStr


# A method to redirect pprint() calls to the log file
# Need a way to take a pprint-able object, and redirect its output to file
# Do this by swapping out sys.stdout temporarily, execute theObj.pprint()
# then set sys.stdout back to the original.  
def LOGPPRINT(theObj, loglevel=DEFAULT_PPRINT_LOGLEVEL):
   sys.stdout = stringAggregator()
   theObj.pprint()
   printedStr = sys.stdout.getStr()
   sys.stdout = sys.__stdout__
   stkOneUp = traceback.extract_stack()[-2]
   filename,method = stkOneUp[0], stkOneUp[1]
   methodStr  = '(PPRINT from %s:%d)\n' % (filename,method)
   logging.log(loglevel, methodStr + printedStr)
   
# For super-debug mode, we'll write out raw data
def LOGRAWDATA(rawStr, loglevel=DEFAULT_RAWDATA_LOGLEVEL):
   dtype = isLikelyDataType(rawStr)
   stkOneUp = traceback.extract_stack()[-2]
   filename,method = stkOneUp[0], stkOneUp[1]
   methodStr  = '(PPRINT from %s:%d)\n' % (filename,method)
   pstr = rawStr[:]
   if dtype==DATATYPE.Binary:
      pstr = binary_to_hex(rawStr)
      pstr = prettyHex(pstr, indent='  ', withAddr=False)
   elif dtype==DATATYPE.Hex:
      pstr = prettyHex(pstr, indent='  ', withAddr=False)
   else:
      pstr = '   ' + '\n   '.join(pstr.split('\n'))

   logging.log(loglevel, methodStr + pstr)


# This is a sweet trick for create enum-like dictionaries. 
# Either automatically numbers (*args), or name-val pairs (**kwargs)
#http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
   enums = dict(zip(sequential, range(len(sequential))), **named)
   return type('Enum', (), enums)

DATATYPE = enum("Binary", 'Base58', 'Hex')
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

cpplogfile = None
if CLI_OPTIONS.logDisable:
   print 'Logging is disabled'
   rootLogger.disabled = True


# Some useful constants to be used throughout everything
BASE58CHARS  = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
BASE16CHARS  = '0123 4567 89ab cdef'.replace(' ','')
LITTLEENDIAN  = '<';
BIGENDIAN     = '>';
NETWORKENDIAN = '!';
ONE_BTC       = long(100000000)
CENT          = long(1000000)
UNINITIALIZED = None
UNKNOWN       = -2
MIN_TX_FEE    = 50000
MIN_RELAY_TX_FEE = 10000
MT_WAIT_TIMEOUT_SEC = 10;

UINT8_MAX  = 2**8-1
UINT16_MAX = 2**16-1
UINT32_MAX = 2**32-1
UINT64_MAX = 2**64-1

RightNow = time.time
SECOND   = 1
MINUTE   = 60
HOUR     = 3600
DAY      = 24*HOUR
WEEK     = 7*DAY
MONTH    = 30*DAY
YEAR     = 365*DAY

KILOBYTE = 1024.0
MEGABYTE = 1024*KILOBYTE
GIGABYTE = 1024*MEGABYTE
TERABYTE = 1024*GIGABYTE
PETABYTE = 1024*TERABYTE

# Set the default-default 
DEFAULT_DATE_FORMAT = '%Y-%b-%d %I:%M%p'
FORMAT_SYMBOLS = [ \
   ['%y', 'year, two digit (00-99)'], \
   ['%Y', 'year, four digit'], \
   ['%b', 'month name (abbrev)'], \
   ['%B', 'month name (full)'], \
   ['%m', 'month number (01-12)'], \
   ['%d', 'day of month (01-31)'], \
   ['%H', 'hour 24h (00-23)'], \
   ['%I', 'hour 12h (01-12)'], \
   ['%M', 'minute (00-59)'], \
   ['%p', 'morning/night (am,pm)'], \
   ['%a', 'day of week (abbrev)'], \
   ['%A', 'day of week (full)'], \
   ['%%', 'percent symbol'] ]


# Some time methods (RightNow() return local unix timestamp)
RightNow = time.time
def RightNowUTC():
   return time.mktime(time.gmtime(RightNow()))



# Define all the hashing functions we're going to need.  We don't actually
# use any of the first three directly (sha1, sha256, ripemd160), we only
# use hash256 and hash160 which use the first three to create the ONLY hash
# operations we ever do in the bitcoin network
# UPDATE:  mini-private-key format requires vanilla sha256... 
def sha1(bits):
   return hashlib.new('sha1', bits).digest()
def sha256(bits):
   return hashlib.new('sha256', bits).digest()
def sha512(bits):
   return hashlib.new('sha512', bits).digest()
def ripemd160(bits):
   # It turns out that not all python has ripemd160...?
   #return hashlib.new('ripemd160', bits).digest()
   return Cpp.BtcUtils().ripemd160_SWIG(bits)
def hash256(s):
   """ Double-SHA256 """
   return sha256(sha256(s))
def hash160(s):
   """ RIPEMD160( SHA256( binaryStr ) ) """
   return Cpp.BtcUtils().getHash160_SWIG(s)


def HMAC(key, msg, hashfunc=sha512):
   """ This is intended to be simple, not fast.  For speed, use HDWalletCrypto() """
   key = (sha512(key) if len(key)>64 else key)
   key = key + ('\x00'*(64-len(key)) if len(key)<64 else '')
   okey = ''.join([chr(ord('\x5c')^ord(c)) for c in key])
   ikey = ''.join([chr(ord('\x36')^ord(c)) for c in key])
   return hashfunc( okey + hashfunc(ikey + msg) )

HMAC256 = lambda key,msg: HMAC(key,msg,sha256)
HMAC512 = lambda key,msg: HMAC(key,msg,sha512)


################################################################################
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



def pprintDiff(str1, str2, indent=''):
   if not len(str1)==len(str2):
      print 'pprintDiff: Strings are different length!'
      return

   byteDiff = []
   for i in range(len(str1)):
      if str1[i]==str2[i]:
         byteDiff.append('-')
      else:
         byteDiff.append('X')

   pprintHex(''.join(byteDiff), indent=indent)




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
   hstr = h[:]  # copies data, no references
   if endIn==LITTLEENDIAN:
      hstr = hex_switchEndian(hstr)
   return( int(hstr, 16) )


##### HEXSTR/BINARYSTR #####
def hex_to_binary(h, endIn=LITTLEENDIAN, endOut=LITTLEENDIAN):
   """
   Converts hexadecimal to binary (in a python string).  Endianness is
   only switched if (endIn != endOut)
   """
   bout = h[:]  # copies data, no references
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



EmptyHash = hex_to_binary('00'*32)


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
      n += BASE58CHARS.index(ch)

   binOut = ''
   while n>0:
      d,m = divmod(n,256)
      binOut = chr(m) + binOut
      n = d
   return '\x00'*padding + binOut



##### MAIN NETWORK IS DEFAULT #####
if not USE_TESTNET:
   # TODO:  The testnet genesis tx hash can't be the same...?
   BITCOIN_PORT = 8333
   BITCOIN_RPC_PORT = 8332
   ARMORY_RPC_PORT = 8225
   MAGIC_BYTES = '\xf9\xbe\xb4\xd9'
   GENESIS_BLOCK_HASH_HEX  = '6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000'
   GENESIS_BLOCK_HASH      = 'o\xe2\x8c\n\xb6\xf1\xb3r\xc1\xa6\xa2F\xaec\xf7O\x93\x1e\x83e\xe1Z\x08\x9ch\xd6\x19\x00\x00\x00\x00\x00'
   GENESIS_TX_HASH_HEX     = '3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a'
   GENESIS_TX_HASH         = ';\xa3\xed\xfdz{\x12\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3\x88\x8aQ2:\x9f\xb8\xaaK\x1e^J'
   ADDRBYTE = '\x00'
   P2SHBYTE = '\x05'
   PRIVKEYBYTE = '\x80'
else:
   BITCOIN_PORT = 18333
   BITCOIN_RPC_PORT = 18332
   ARMORY_RPC_PORT     = 18225
   MAGIC_BYTES  = '\x0b\x11\x09\x07'
   GENESIS_BLOCK_HASH_HEX  = '43497fd7f826957108f4a30fd9cec3aeba79972084e90ead01ea330900000000'
   GENESIS_BLOCK_HASH      = 'CI\x7f\xd7\xf8&\x95q\x08\xf4\xa3\x0f\xd9\xce\xc3\xae\xbay\x97 \x84\xe9\x0e\xad\x01\xea3\t\x00\x00\x00\x00'
   GENESIS_TX_HASH_HEX     = '3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a'
   GENESIS_TX_HASH         = ';\xa3\xed\xfdz{\x12\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3\x88\x8aQ2:\x9f\xb8\xaaK\x1e^J'
   ADDRBYTE = '\x6f'
   P2SHBYTE = '\xc4'
   PRIVKEYBYTE = '\xef'

if not CLI_OPTIONS.satoshiPort == 'DEFAULT':
   try:
      BITCOIN_PORT = int(CLI_OPTIONS.satoshiPort)
   except:
      raise TypeError, 'Invalid port for Bitcoin-Qt, using ' + str(BITCOIN_PORT)


if not CLI_OPTIONS.rpcport == 'DEFAULT':
   try:
      ARMORY_RPC_PORT = int(CLI_OPTIONS.rpcport)
   except:
      raise TypeError, 'Invalid RPC port for armoryd ' + str(ARMORY_RPC_PORT)


BLOCKCHAINS = {}
BLOCKCHAINS['\xf9\xbe\xb4\xd9'] = "Main Network"
BLOCKCHAINS['\xfa\xbf\xb5\xda'] = "Old Test Network"
BLOCKCHAINS['\x0b\x11\x09\x07'] = "Test Network (testnet3)"

NETWORKS = {}
NETWORKS['\x00'] = "Main Network"
NETWORKS['\x6f'] = "Test Network"
NETWORKS['\x34'] = "Namecoin Network"






################################################################################
def hash160_to_addrStr(binStr, isP2SH=False):
   """
   Converts the 20-byte pubKeyHash to 25-byte binary Bitcoin address
   which includes the network byte (prefix) and 4-byte checksum (suffix)
   """
   addr21 = (P2SHBYTE if isP2SH else ADDRBYTE) + binStr
   addr25 = addr21 + hash256(addr21)[:4]
   return binary_to_base58(addr25);

################################################################################
def addrStr_is_p2sh(b58Str):
   binStr = base58_to_binary(b58Str)
   if not len(binStr)==25:
      return False
   return (binStr[0] == P2SHBYTE)

################################################################################
def addrStr_to_hash160(b58Str):
   return base58_to_binary(b58Str)[1:-4]


###### Typing-friendly Base16 #####
#  Implements "hexadecimal" encoding but using only easy-to-type
#  characters in the alphabet.  Hex usually includes the digits 0-9
#  which can be slow to type, even for good typists.  On the other
#  hand, by changing the alphabet to common, easily distinguishable,
#  lowercase characters, typing such strings will become dramatically
#  faster.  Additionally, some default encodings of QRCodes do not
#  preserve the capitalization of the letters, meaning that Base58
#  is not a feasible options
NORMALCHARS  = '0123 4567 89ab cdef'.replace(' ','')
EASY16CHARS  = 'asdf ghjk wert uion'.replace(' ','')
hex_to_base16_map = {}
base16_to_hex_map = {}
for n,b in zip(NORMALCHARS,EASY16CHARS):
   hex_to_base16_map[n] = b
   base16_to_hex_map[b] = n

def binary_to_easyType16(binstr):
   return ''.join([hex_to_base16_map[c] for c in binary_to_hex(binstr)])

def easyType16_to_binary(b16str):
   return hex_to_binary(''.join([base16_to_hex_map[c] for c in b16str]))


def makeSixteenBytesEasy(b16):
   if not len(b16)==16:
      raise ValueError, 'Must supply 16-byte input'
   chk2 = computeChecksum(b16, nBytes=2)
   et18 = binary_to_easyType16(b16 + chk2) 
   return ' '.join([et18[i*4:(i+1)*4] for i in range(9)])

def readSixteenEasyBytes(et18):
   b18 = easyType16_to_binary(et18.strip().replace(' ',''))
   b16 = b18[:16]
   chk = b18[ 16:]
   b16new = verifyChecksum(b16, chk)
   if len(b16new)==0:
      return ('','Error_2+')
   elif not b16new==b16:
      return (b16new,'Fixed_1')
   else:
      return (b16new,None)

##### FLOAT/BTC #####
# https://en.bitcoin.it/wiki/Proper_Money_Handling_(JSON-RPC)
def ubtc_to_floatStr(n):
   return '%d.%08d' % divmod (n, ONE_BTC)
def floatStr_to_ubtc(s):
   return long(round(float(s) * ONE_BTC))
def float_to_btc (f):
   return long (round(f * ONE_BTC))



##### And a few useful utilities #####
def unixTimeToFormatStr(unixTime, formatStr=DEFAULT_DATE_FORMAT):
   """
   Converts a unix time (like those found in block headers) to a
   pleasant, human-readable format
   """
   dtobj = datetime.fromtimestamp(unixTime)
   dtstr = u'' + dtobj.strftime(formatStr).decode('utf-8')
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
   else:
      strPieces = [floatSec/MONTH, 'month']

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


##### HEXSTR/VARINT #####
def packVarInt(n):
   """ Writes 1,3,5 or 9 bytes depending on the size of n """
   if   n < 0xfd:  return [chr(n), 1]
   elif n < 1<<16: return ['\xfd'+pack('<H',n), 3]
   elif n < 1<<32: return ['\xfe'+pack('<I',n), 5]
   else:           return ['\xff'+pack('<Q',n), 9]

def unpackVarInt(hvi):
   """ Returns a pair: the integer value and number of bytes read """
   code = unpack('<B', hvi[0])[0]
   if   code  < 0xfd: return [code, 1]
   elif code == 0xfd: return [unpack('<H',hvi[1:3])[0], 3]
   elif code == 0xfe: return [unpack('<I',hvi[1:5])[0], 5]
   elif code == 0xff: return [unpack('<Q',hvi[1:9])[0], 9]
   else: assert(False)




def fixChecksumError(binaryStr, chksum, hashFunc=hash256):
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

def computeChecksum(binaryStr, nBytes=4, hashFunc=hash256):
   return hashFunc(binaryStr)[:nBytes]


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
   However, for PyBtcWallet serialization, if I determine that it is a chksum
   error and simply return the original string, then PyBtcWallet will correct
   the checksum in the file, next time it reserializes the data. 
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
      fixStr = fixChecksumError(bin1, chksum, hashFunc)
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


# TODO:  I don't actually know how to do this, yet...
def difficulty_to_binaryBits(i):
   pass

# The following params are for the Bitcoin elliptic curves (secp256k1)
SECP256K1_MOD   = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
SECP256K1_B     = 0x0000000000000000000000000000000000000000000000000000000000000007L
SECP256K1_A     = 0x0000000000000000000000000000000000000000000000000000000000000000L
SECP256K1_GX    = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
SECP256K1_GY    = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L

################################################################################
################################################################################
# START FINITE FIELD OPERATIONS


class FiniteField(object):
   """
   Create a simple, prime-order FiniteField.  Because this is used only
   to encode data of fixed width, I enforce prime-order by hardcoding 
   primes, and you just pick the data width (in bytes).  If your desired
   data width is not here,  simply find a prime number very close to 2^N,
   and add it to the PRIMES map below.

   This will be used for Shamir's Secret Sharing scheme.  Encode your 
   data as the coeffient of finite-field polynomial, and store points
   on that polynomial.  The order of the polynomial determines how
   many points are needed to recover the original secret.
   """

   # bytes: primeclosetomaxval
   PRIMES = {   1:  2**8-5,  # mainly for testing
                2:  2**16-39,
                4:  2**32-5,
                8:  2**64-59,
               16:  2**128-797,
               20:  2**160-543,
               24:  2**192-333,
               32:  2**256-357,
               48:  2**384-317,
               64:  2**512-569,
               96:  2**768-825,
              128:  2**1024-105,
              192:  2**1536-3453,
              256:  2**2048-1157  }

   def __init__(self, nbytes):
      if not self.PRIMES.has_key(nbytes): 
         LOGERROR('No primes available for size=%d bytes', nbytes)
         self.prime = None
         raise FiniteFieldError
      self.prime = self.PRIMES[nbytes]


   def add(self,a,b):
      return (a+b) % self.prime
   
   def subtract(self,a,b):
      return (a-b) % self.prime
   
   def mult(self,a,b):
      return (a*b) % self.prime
   
   def power(self,a,b):
      result = 1
      while(b>0):
         b,x = divmod(b,2)
         result = (result * (a if x else 1)) % self.prime
         a = a*a % self.prime
      return result
   
   def powinv(self,a):
      """ USE ONLY PRIME MODULUS """
      return self.power(a,self.prime-2)
   
   def divide(self,a,b):
      """ USE ONLY PRIME MODULUS """
      baddinv = self.powinv(b)
      return self.mult(a,baddinv)
   
   
   def mtrxrmrowcol(self,mtrx,r,c):
      if not len(mtrx) == len(mtrx[0]):
         LOGERROR('Must be a square matrix!')
         return []
   
      sz = len(mtrx)
      return [[mtrx[i][j] for j in range(sz) if not j==c] for i in range(sz) if not i==r]
      
   
   ################################################################################
   def mtrxdet(self,mtrx):
      if len(mtrx)==1:
         return mtrx[0][0]
   
      if not len(mtrx) == len(mtrx[0]):
         LOGERROR('Must be a square matrix!')
         return -1
   
      result = 0;
      for i in range(len(mtrx)):
         mult     = mtrx[0][i] * (-1 if i%2==1 else 1)
         subdet   = self.mtrxdet(self.mtrxrmrowcol(mtrx,0,i))
         result   = self.add(result, self.mult(mult,subdet))
      return result
     
   ################################################################################
   def mtrxmultvect(self,mtrx, vect):
      M,N = len(mtrx), len(mtrx[0])
      if not len(mtrx[0])==len(vect):
         LOGERROR('Mtrx and vect are incompatible: %dx%d, %dx1', M, N, len(vect))
      return [ sum([self.mult(mtrx[i][j],vect[j]) for j in range(N)])%self.prime for i in range(M) ]
   
   ################################################################################
   def mtrxmult(self,m1, m2):
      M1,N1 = len(m1), len(m1[0])
      M2,N2 = len(m2), len(m2[0])
      if not N1==M2:
         LOGERROR('Mtrx and vect are incompatible: %dx%d, %dx%d', M1,N1, M2,N2)
      inner = lambda i,j: sum([self.mult(m1[i][k],m2[k][j]) for k in range(N1)])
      return [ [inner(i,j)%self.prime for j in range(N1)] for i in range(M1) ]
   
   ################################################################################
   def mtrxadjoint(self,mtrx):
      sz = len(mtrx)
      inner = lambda i,j: self.mtrxdet(self.mtrxrmrowcol(mtrx,i,j))
      return [[((-1 if (i+j)%2==1 else 1)*inner(j,i))%self.prime for j in range(sz)] for i in range(sz)]
      
   ################################################################################
   def mtrxinv(self,mtrx):
      det = self.mtrxdet(mtrx)
      adj = self.mtrxadjoint(mtrx)
      sz = len(mtrx)
      return [[self.divide(adj[i][j],det) for j in range(sz)] for i in range(sz)]


################################################################################
def SplitSecret(secret,needed, pieces, nbytes=None):
   if nbytes==None:
      nbytes = len(secret)

   ff = FiniteField(nbytes)
   fragments = []

   # Convert secret to an integer
   a = binary_to_int(SecureBinaryData(secret).toBinStr(),BIGENDIAN)
   if not a<ff.prime:
      LOGERROR('Secret must be less than %s', int_to_hex(ff.prime,endOut=BIGENDIAN))
      LOGERROR('             You entered %s', int_to_hex(a,endOut=BIGENDIAN))
      raise FiniteFieldError

   if not pieces>=needed:
      LOGERROR('You must create more pieces than needed to reconstruct!')
      raise FiniteFieldError


   if needed==1 or needed>8:
      LOGERROR('Can split secrets into parts *requiring* at most 8 fragments')
      LOGERROR('You can break it into as many optional fragments as you want')
      return fragments


   lasthmac = secret[:]
   othernum = []
   for i in range(pieces+needed-1):
      lasthmac = HMAC512(lasthmac, 'splitsecrets')[:nbytes]
      othernum.append(lasthmac)

   othernum = [binary_to_int(n) for n in othernum]
   if needed==2:
      b = othernum[0]
      poly = lambda x:  ff.add(ff.mult(a,x), b)
      for i in range(pieces):
         x = othernum[i+1]
         fragments.append( [x, poly(x)] )

   elif needed==3:
      def poly(x):
         b = othernum[0]
         c = othernum[1]
         x2  = ff.power(x,2)
         ax2 = ff.mult(a,x2)
         bx  = ff.mult(b,x)
         return ff.add(ff.add(ax2,bx),c) 

      for i in range(pieces):
         x = othernum[i+2]
         fragments.append( [x, poly(x)] )

   else:
      def poly(x):
         polyout = ff.mult(a, ff.power(x,needed-1))
         for i,e in enumerate(range(needed-2,-1,-1)):
            term = ff.mult(othernum[i], ff.power(x,e))
            polyout = ff.add(polyout, term)
         return polyout
         
      for i in range(pieces):
         x = othernum[i+2]
         fragments.append( [x, poly(x)] )


   a = None
   fragments = [ [int_to_binary(p, nbytes, BIGENDIAN) for p in frag] for frag in fragments]
   return fragments


################################################################################
def ReconstructSecret(fragments, needed, nbytes):

   ff = FiniteField(nbytes)
   if needed==2:
      x1,y1 = [binary_to_int(f, BIGENDIAN) for f in fragments[0]]
      x2,y2 = [binary_to_int(f, BIGENDIAN) for f in fragments[1]]

      m = [[x1,1],[x2,1]]
      v = [y1,y2]

      minv = ff.mtrxinv(m)
      a,b = ff.mtrxmultvect(minv,v)
      return int_to_binary(a, nbytes, BIGENDIAN)
   
   elif needed==3:
      x1,y1 = [binary_to_int(f, BIGENDIAN) for f in fragments[0]]
      x2,y2 = [binary_to_int(f, BIGENDIAN) for f in fragments[1]]
      x3,y3 = [binary_to_int(f, BIGENDIAN) for f in fragments[2]]

      sq = lambda x: ff.power(x,2)
      m = [  [sq(x1), x1 ,1], \
             [sq(x2), x2, 1], \
             [sq(x3), x3, 1] ]
      v = [y1,y2,y3]

      minv = ff.mtrxinv(m)
      a,b,c = ff.mtrxmultvect(minv,v)
      return int_to_binary(a, nbytes, BIGENDIAN)
   else:
      pairs = fragments[:needed]
      m = []
      v = []
      for x,y in pairs:
         x = binary_to_int(x, BIGENDIAN)
         y = binary_to_int(y, BIGENDIAN)
         m.append([])
         for i,e in enumerate(range(needed-1,-1,-1)):
            m[-1].append( ff.power(x,e) )
         v.append(y)

      minv = ff.mtrxinv(m)
      outvect = ff.mtrxmultvect(minv,v)
      return int_to_binary(outvect[0], nbytes, BIGENDIAN)
         
   


# END FINITE FIELD OPERATIONS
################################################################################
################################################################################


# We can identify an address string by its first byte upon conversion
# back to binary.  Return -1 if checksum doesn't match
def checkAddrType(addrBin):
   """ Gets the network byte of the address.  Returns -1 if chksum fails """
   first21, chk4 = addrBin[:-4], addrBin[-4:]
   chkBytes = hash256(first21)
   if chkBytes[:4] == chk4:
      return addrBin[0]
   else:
      return -1

# Check validity of a BTC address in its binary form, as would
# be found inside a pkScript.  Usually about 24 bytes
def checkAddrBinValid(addrBin, netbyte=ADDRBYTE):
   """
   Checks whether this address is valid for the given network
   (set at the top of pybtcengine.py)
   """
   return checkAddrType(addrBin) == netbyte

# Check validity of a BTC address in Base58 form
def checkAddrStrValid(addrStr):
   """ Check that a Base58 address-string is valid on this network """
   return checkAddrBinValid(base58_to_binary(addrStr))


def convertKeyDataToAddress(PRIVATE_KEY=None, PUBLIC_KEY=None):
   if not PRIVATE_KEY and not PUBLIC_KEY:
      raise BadAddressError, 'No key data supplied for conversion'
   elif PRIVATE_KEY:
      if isinstance(PRIVATE_KEY, str):
         PRIVATE_KEY = SecureBinaryData(PRIVATE_KEY)

      if not PRIVATE_KEY.getSize()==32:
         raise BadAddressError, 'Invalid private key format!'
      else:
         PUBLIC_KEY = CryptoECDSA().ComputePublicKey(PRIVATE_KEY)

   if isinstance(PUBLIC_KEY,str):
      PUBLIC_KEY = SecureBinaryData(PUBLIC_KEY)
   return PUBLIC_KEY.getHash160()



################################################################################
def decodeMiniPrivateKey(keyStr):
   """
   Converts a 22, 26 or 30-character Base58 mini private key into a 
   32-byte binary private key.  
   """
   if not len(keyStr) in (22,26,30):
      return ''

   keyQ = keyStr + '?'
   theHash = sha256(keyQ)
   
   if binary_to_hex(theHash[0]) == '01':
      raise KeyDataError, 'PBKDF2-based mini private keys not supported!'
   elif binary_to_hex(theHash[0]) != '00':
      raise KeyDataError, 'Invalid mini private key... double check the entry'
   
   return sha256(keyStr)
   

################################################################################
def parsePrivateKeyData(theStr):
      hexChars = '01234567890abcdef'
      b58Chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

      hexCount = sum([1 if c in hexChars else 0 for c in theStr.lower()])
      b58Count = sum([1 if c in b58Chars else 0 for c in theStr])
      canBeHex = hexCount==len(theStr)
      canBeB58 = b58Count==len(theStr)

      binEntry = ''
      keyType = ''
      isMini = False
      if canBeB58 and not canBeHex:
         if len(theStr) in (22, 30):
            # Mini-private key format!
            try:
               binEntry = decodeMiniPrivateKey(theStr)
            except KeyDataError:
               raise BadAddressError, 'Invalid mini-private key string'
            keyType = 'Mini Private Key Format'
            isMini = True
         elif len(theStr) in range(48,53):
            binEntry = base58_to_binary(theStr)
            keyType = 'Plain Base58'
         else:
            raise BadAddressError, 'Unrecognized key data'
      elif canBeHex:  
         binEntry = hex_to_binary(theStr)
         keyType = 'Plain Hex'
      else:
         raise BadAddressError, 'Unrecognized key data'


      if len(binEntry)==36 or (len(binEntry)==37 and binEntry[0]==PRIVKEYBYTE):
         if len(binEntry)==36:
            keydata = binEntry[:32 ]
            chk     = binEntry[ 32:]
            binEntry = verifyChecksum(keydata, chk)
            if not isMini: 
               keyType = 'Raw %s with checksum' % keyType.split(' ')[1]
         else:
            # Assume leading 0x80 byte, and 4 byte checksum
            keydata = binEntry[ :1+32 ]
            chk     = binEntry[  1+32:]
            binEntry = verifyChecksum(keydata, chk)
            binEntry = binEntry[1:]
            if not isMini: 
               keyType = 'Standard %s key with checksum' % keyType.split(' ')[1]

         if binEntry=='':
            raise InvalidHashError, 'Private Key checksum failed!'
      elif len(binEntry) in (33, 37) and binEntry[-1]=='\x01':
         raise CompressedKeyError, 'Compressed Public keys not supported!'
      return binEntry, keyType
   


################################################################################
def encodePrivKeyBase58(privKeyBin):
   bin33 = PRIVKEYBYTE + privKeyBin
   chk = computeChecksum(bin33)
   return binary_to_base58(bin33 + chk)



URI_VERSION_STR = '1.0'

################################################################################
def parseBitcoinURI(theStr):
   """ Takes a URI string, returns the pieces of it, in a dictionary """

   # Start by splitting it into pieces on any separator
   seplist = ':;?&'
   for c in seplist:
      theStr = theStr.replace(c,' ')
   parts = theStr.split()

   # Now start walking through the parts and get the info out of it
   if not parts[0] == 'bitcoin':
      return {}

   uriData = {}
   
   try:
      uriData['address'] = parts[1]
      for p in parts[2:]:
         if not '=' in p:
            raise BadURIError, 'Unrecognized URI field: "%s"'%p
            
         # All fields must be "key=value" making it pretty easy to parse
         key, value = p.split('=')
   
         # A few
         if key.lower()=='amount':
            uriData['amount'] = str2coin(value)
         elif key.lower() in ('label','message'):
            uriData[key] = uriPercentToReserved(value)
         else:
            uriData[key] = value
   except:
      return {}
   
   return uriData


################################################################################
def uriReservedToPercent(theStr):
   """ 
   Convert from a regular string to a percent-encoded string
   """
   #Must replace '%' first, to avoid recursive (and incorrect) replacement!
   reserved = "%!*'();:@&=+$,/?#[] "

   for c in reserved:
      theStr = theStr.replace(c, '%%%s' % int_to_hex(ord(c)))
   return theStr


################################################################################
def uriPercentToReserved(theStr):
   """ 
   This replacement direction is much easier!
   Convert from a percent-encoded string to a 
   """
   
   parts = theStr.split('%')
   if len(parts)>1:
      for p in parts[1:]:
         parts[0] += chr( hex_to_int(p[:2]) ) + p[2:]
   return parts[0][:]
   

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
      uriStr += 'label=%s' % uriReservedToPercent(msg)

   return uriStr


