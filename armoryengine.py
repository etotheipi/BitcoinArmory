################################################################################
#
# Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory
# Author:     Alan Reiner
# Orig Date:  20 November, 2011
# Descr:      This file serves as an engine for python-based Bitcoin software.
#             I forked this from my own project -- PyBtcEngine -- because I
#             I needed to start including/rewriting code to use CppBlockUtils
#             but did not want to break the pure-python-ness of PyBtcEngine.
#             If you are interested in in a pure-python set of bitcoin utils
#             please go checkout the PyBtcEngine github project.
#
#             Of course, the biggest advatage here is that you have access to
#             the blockchain through BlockObj/BlockObjRef/BlockUtils, as found
#             in the CppForSWIG directory.  This is available in PyBtcEngine,
#             but I had to split out the modules, and I didn't have a good way
#             to maintain the pure-python module while also implementing all
#             the great SWIG-imported C++ utilities I built.
#
#             This module replaces the ECDSA operations, with faster ones
#             implemented in C++ from Crypto++.  This also enables the ability
#             to use SecureBinaryData objects for moving around private keys,
#             though I'm not entirely clear if python-based memory management
#             is going to properly clean up after itself, even with a page-
#             locked, self-destructing data container.
#
#
################################################################################


# Version Numbers 
BTCARMORY_VERSION    = (0, 84, 0, 0)  # (Major, Minor, Minor++, even-more-minor)
PYBTCWALLET_VERSION  = (1, 35, 0, 0)  # (Major, Minor, Minor++, even-more-minor)

ARMORY_DONATION_ADDR = '1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv'

   

import copy
import hashlib
import random
import time
import os
import string
import sys
import shutil
import math
import logging
import logging.handlers
import ast
import traceback
import threading
from struct import pack, unpack
from datetime import datetime


from sys import argv

import optparse
parser = optparse.OptionParser(usage="%prog [options]\n")
#parser.add_option("--host", dest="host", default="127.0.0.1",
                  #help="IP/hostname to connect to (default: %default)")
#parser.add_option("--port", dest="port", default="8333", type="int",
                  #help="port to connect to (default: %default)")
parser.add_option("--settings", dest="settingsPath", default='DEFAULT', type="str",
                  help="load Armory with a specific settings file")
parser.add_option("--datadir", dest="datadir", default='DEFAULT', type="str",
                  help="Change the directory that Armory calls home")
parser.add_option("--satoshi-datadir", dest="satoshiHome", default='DEFAULT', type='str', 
                  help="The Bitcoin-Qt/bitcoind home directory")
parser.add_option("--satoshi-port", dest="satoshiPort", default='DEFAULT', type="str",
                  help="For Bitcoin-Qt instances operating on a non-standard port")
parser.add_option("--testnet", dest="testnet", action="store_true", default=False,
                  help="Use the testnet protocol")
parser.add_option("--offline", dest="offline", action="store_true", default=False,
                  help="Force Armory to run in offline mode")
parser.add_option("--nettimeout", dest="nettimeout", default=2, type="int",
                  help="Timeout for detecting internet connection at startup")
parser.add_option("--interport", dest="interport", default=-1, type="int",
                  help="Port for inter-process communication between Armory instances")
parser.add_option("--debug", dest="doDebug", action="store_true", default=False, 
                  help="Increase amount of debugging output")
parser.add_option("--nologging", dest="logDisable", action="store_true", default=False,
                  help="Disable all logging")
#parser.add_option("--logcpp", dest="logcpp", action="store_true", default=False,
                  #help="Log C++/SWIG console output by redirecting *all* stdout to log file")
parser.add_option("--netlog", dest="netlog", action="store_true", default=False,
                  help="Log networking messages sent and received by Armory")
parser.add_option("--force-online", dest="forceOnline", action="store_true", default=False,
                  help="Go into online mode, even if internet connection isn't detected")
parser.add_option("--no-threading", dest="noThreading", action="store_true", default=False,
                  help="Force use of the single-threaded (blocking) BlockDataManger.")


(CLI_OPTIONS, CLI_ARGS) = parser.parse_args()


# Use CLI args to determine testnet or not
USE_TESTNET = CLI_OPTIONS.testnet
   

# Set default port for inter-process communication
if CLI_OPTIONS.interport < 0:
   CLI_OPTIONS.interport = 8223 + (1 if USE_TESTNET else 0)




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

print '********************************************************************************'
print 'Loading Armory Engine:'
print '   Armory Version:      ', getVersionString(BTCARMORY_VERSION)
print '   PyBtcWallet  Version:', getVersionString(PYBTCWALLET_VERSION)

# Get the host operating system
import platform
opsys = platform.system()
OS_WINDOWS = 'win32'  in opsys.lower() or 'windows' in opsys.lower()
OS_LINUX   = 'nix'    in opsys.lower() or 'nux'     in opsys.lower()
OS_MACOSX  = 'darwin' in opsys.lower() or 'osx'     in opsys.lower()

# Figure out the default directories for Satoshi client, and BicoinArmory
OS_NAME          = ''
USER_HOME_DIR    = ''
BTC_HOME_DIR     = ''
ARMORY_HOME_DIR  = ''
SUBDIR = 'testnet' if USE_TESTNET else ''
if OS_WINDOWS:
   OS_NAME         = 'Windows'
   USER_HOME_DIR   = os.getenv('APPDATA')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, 'Bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, 'Armory', SUBDIR)
elif OS_LINUX:
   OS_NAME         = 'Linux'
   USER_HOME_DIR   = os.getenv('HOME')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, '.bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, '.armory', SUBDIR)
elif OS_MACOSX:
   OS_NAME         = 'Mac/OSX'
   USER_HOME_DIR   = os.path.expanduser('~/Library/Application Support')
   BTC_HOME_DIR    = os.path.join(USER_HOME_DIR, 'Bitcoin', SUBDIR)
   ARMORY_HOME_DIR = os.path.join(USER_HOME_DIR, 'Armory', SUBDIR)
else:
   print '***Unknown operating system!'
   print '***Cannot determine default directory locations'


# Allow user to override default bitcoin-qt/bitcoind home directory
if not CLI_OPTIONS.satoshiHome.lower()=='default':
   if not os.path.exists(CLI_OPTIONS.satoshiHome):
      print 'Directory "%s" does not exist!  Using default!' % CLI_OPTIONS.satoshiHome
   else:
      BTC_HOME_DIR = CLI_OPTIONS.satoshiHome


# Allow user to override default Armory home directory
if not CLI_OPTIONS.datadir.lower()=='default':
   if not os.path.exists(CLI_OPTIONS.datadir):
      print 'Directory "%s" does not exist!  Using default!' % CLI_OPTIONS.datadir
   else:
      ARMORY_HOME_DIR = CLI_OPTIONS.datadir

# Change the settings file to use
if CLI_OPTIONS.settingsPath.lower()=='default':
   CLI_OPTIONS.settingsPath = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt')



SETTINGS_PATH = CLI_OPTIONS.settingsPath
ARMORY_LOG_FILE     = os.path.join(ARMORY_HOME_DIR, 'armorylog.txt')



print 'Detected Operating system:', OS_NAME
print '   User home-directory   :', USER_HOME_DIR
print '   Satoshi BTC directory :', BTC_HOME_DIR
print '   Armory home dir       :', ARMORY_HOME_DIR

if ARMORY_HOME_DIR and not os.path.exists(ARMORY_HOME_DIR):
   os.makedirs(ARMORY_HOME_DIR)



class UnserializeError(Exception): pass
class BadAddressError(Exception): pass
class VerifyScriptError(Exception): pass
class FileExistsError(Exception): pass
class ECDSA_Error(Exception): pass
class PackerError(Exception): pass
class UnpackerError(Exception): pass
class UnitializedBlockDataError(Exception): pass
class WalletLockError(Exception): pass
class SignatureError(Exception): pass
class KeyDataError(Exception): pass
class ChecksumError(Exception): pass
class WalletAddressError(Exception): pass
class PassphraseError(Exception): pass
class EncryptionError(Exception): pass
class InterruptTestError(Exception): pass
class NetworkIDError(Exception): pass
class WalletExistsError(Exception): pass
class ConnectionError(Exception): pass
class BlockchainUnavailableError(Exception): pass
class InvalidHashError(Exception): pass
class BadInputError(Exception): pass
class BadURIError(Exception): pass
class CompressedKeyError(Exception): pass





##### MAIN NETWORK IS DEFAULT #####
if not USE_TESTNET:
   # TODO:  The testnet genesis tx hash can't be the same...?
   BITCOIN_PORT = 8333
   MAGIC_BYTES = '\xf9\xbe\xb4\xd9'
   GENESIS_BLOCK_HASH_HEX  = '6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000'
   GENESIS_BLOCK_HASH      = 'o\xe2\x8c\n\xb6\xf1\xb3r\xc1\xa6\xa2F\xaec\xf7O\x93\x1e\x83e\xe1Z\x08\x9ch\xd6\x19\x00\x00\x00\x00\x00'
   GENESIS_TX_HASH_HEX     = '3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a'
   GENESIS_TX_HASH         = ';\xa3\xed\xfdz{\x12\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3\x88\x8aQ2:\x9f\xb8\xaaK\x1e^J'
   ADDRBYTE = '\x00'
else:
   BITCOIN_PORT = 18333
   MAGIC_BYTES  = '\xfa\xbf\xb5\xda'
   GENESIS_BLOCK_HASH_HEX  = '08b067b31dc139ee8e7a76a4f2cfcca477c4c06e1ef89f4ae308951907000000'
   GENESIS_BLOCK_HASH      = '\x08\xb0g\xb3\x1d\xc19\xee\x8ezv\xa4\xf2\xcf\xcc\xa4w\xc4\xc0n\x1e\xf8\x9fJ\xe3\x08\x95\x19\x07\x00\x00\x00'
   GENESIS_TX_HASH_HEX     = '3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a'
   GENESIS_TX_HASH         = ';\xa3\xed\xfdz{\x12\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3\x88\x8aQ2:\x9f\xb8\xaaK\x1e^J'
   ADDRBYTE = '\x6f'

if not CLI_OPTIONS.satoshiPort == 'DEFAULT':
   try:
      BITCOIN_PORT = int(CLI_OPTIONS.satoshiPort)
   except:
      raise TypeError, 'Invalid port for Bitcoin-Qt, using ' + str(BITCOIN_PORT)


BLOCKCHAINS = {}
BLOCKCHAINS['\xf9\xbe\xb4\xd9'] = "Main Network"
BLOCKCHAINS['\xfa\xbf\xb5\xda'] = "Test Network"

NETWORKS = {}
NETWORKS['\x00'] = "Main Network"
NETWORKS['\x6f'] = "Test Network"
NETWORKS['\x34'] = "Namecoin Network"



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
   
# When there's an error in the logging function, it's impossible to find!
# These wrappers will print the full stack so that it's possible to find 
# which line triggered the error
def LOGDEBUG(msg, *a):
   try:
      logstr = msg % a
      callerStr = getCallerLine() + ' - '
      logging.debug(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

def LOGINFO(msg, *a):
   try:
      logstr = msg % a
      callerStr = getCallerLine() + ' - '
      logging.info(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGWARN(msg, *a):
   try:
      logstr = msg % a
      callerStr = getCallerLine() + ' - '
      logging.warn(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGERROR(msg, *a):
   try:
      logstr = msg % a
      callerStr = getCallerLine() + ' - '
      logging.error(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGCRIT(msg, *a):
   try:
      logstr = msg % a
      callerStr = getCallerLine() + ' - '
      logging.critical(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise
def LOGEXCEPT(msg, *a):
   try:
      logstr = msg % a
      callerStr = getCallerLine() + ' - '
      logging.exception(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise



DEFAULT_CONSOLE_LOGTHRESH = logging.WARNING
DEFAULT_FILE_LOGTHRESH    = logging.INFO

DEFAULT_PPRINT_LOGLEVEL   = logging.DEBUG
DEFAULT_RAWDATA_LOGLEVEL  = logging.DEBUG

rootLogger = logging.getLogger('')
if CLI_OPTIONS.doDebug or CLI_OPTIONS.netlog:
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



# Cut down the log file to just the most recent 100 kB
chopLogFile(ARMORY_LOG_FILE, 100*1024)


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


cpplogfile = None
if CLI_OPTIONS.logDisable:
   print 'Logging is disabled'
   rootLogger.disabled = True

# For now, ditch the C++-console-catching.  Logging python is enough
# My attempt at C++ logging too was becoming a hardcore hack...
"""
elif CLI_OPTIONS.logcpp:
   # In order to catch C++ output, we have to redirect ALL stdout
   # (which means that console writes by python, too)
   cpplogfile = open(ARMORY_LOG_FILE_CPP, 'r')
   allLines = cpplogfile.readlines()
   cpplogfile.close()
   # Chop off the beginning of the file
   nBytes,nLines = 0,0;
   for line in allLines[::-1]:
      nBytes += len(line)
      nLines += 1
      if nBytes>100*1024:
         break
   cpplogfile = open(ARMORY_LOG_FILE_CPP, 'w')
   print 'nlines:', nLines
   for line in allLines[-nLines:]:
      print line,
      cpplogfile.write(line)
   cpplogfile.close()
   cpplogfile = open(ARMORY_LOG_FILE_CPP, 'a')
   raw_input()
   os.dup2(cpplogfile.fileno(), sys.stdout.fileno())
   raw_input()
   os.dup2(cpplogfile.fileno(), sys.stderr.fileno())
"""
   

def logexcept_override(type, value, tback):
   import traceback
   import logging
   strList = traceback.format_exception(type,value,tback)
   logging.error(''.join([s for s in strList]))
   # then call the default handler
   sys.__excepthook__(type, value, tback) 

sys.excepthook = logexcept_override


LOGINFO('')
LOGINFO('')
LOGINFO('')
LOGINFO('************************************************************')
LOGINFO('Invoked: ' + ' '.join(argv))
LOGINFO('************************************************************')
LOGINFO('Loading Armory Engine:')
LOGINFO('   Armory Version        : ' + getVersionString(BTCARMORY_VERSION))
LOGINFO('   PyBtcWallet  Version  : ' + getVersionString(PYBTCWALLET_VERSION))
LOGINFO('Detected Operating system: ' + OS_NAME)
LOGINFO('   User home-directory   : ' + USER_HOME_DIR)
LOGINFO('   Satoshi BTC directory : ' + BTC_HOME_DIR)
LOGINFO('   Armory home dir       : ' + ARMORY_HOME_DIR)
LOGINFO('')
LOGINFO('Network Name: ' + NETWORKS[ADDRBYTE])
LOGINFO('Satoshi Port: %d', BITCOIN_PORT)
LOGINFO('Named options/arguments to armoryengine.py:')
for key,val in ast.literal_eval(str(CLI_OPTIONS)).iteritems():
   LOGINFO('    %-16s: %s', key,val)
LOGINFO('Other arguments:')
for val in CLI_ARGS:
   LOGINFO('    %s', val)
LOGINFO('************************************************************')





def coin2str(nSatoshi, ndec=8, rJust=False, maxZeros=8):
   """
   Converts a raw value (1e-8 BTC) into a formatted string for display
   
   ndec, guarantees that we get get a least N decimal places in our result

   maxZeros means we will replace zeros with spaces up to M decimal places
   in order to declutter the amount field

   """

   nBtc = float(nSatoshi) / float(ONE_BTC)
   s = '0.0'
   if   ndec==8:  s = '%0.8f' % (nBtc,)
   elif ndec==7:  s = '%0.7f' % (nBtc,)
   elif ndec==6:  s = '%0.6f' % (nBtc,)
   elif ndec==5:  s = '%0.5f' % (nBtc,)
   elif ndec==4:  s = '%0.4f' % (nBtc,)
   elif ndec==3:  s = '%0.3f' % (nBtc,)
   elif ndec==2:  s = '%0.2f' % (nBtc,)
   elif ndec==1:  s = '%0.1f' % (nBtc,)
   elif ndec==0:  s = '%0.0f' % (nBtc,)

   s = s.rjust(18, ' ')


   if maxZeros < ndec:
      maxChop = ndec - maxZeros
      nChop = min(len(s) - len(str(s.strip('0'))), maxChop)
      if nChop>0:
         s  = s[:-nChop] + nChop*' '

   if not rJust:
      s.strip(' ')

   s = s.replace('. ','  ')

   return s
    

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


# This is a sweet trick for create enum-like dictionaries. 
# Either automatically numbers (*args), or name-val pairs (**kwargs)
#http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def str2coin(coinStr):
   if not '.' in coinStr:
      return int(coinStr)*ONE_BTC
   else:
      lhs,rhs = coinStr.split('.')
      rhs = rhs[:8]
      return int(lhs)*ONE_BTC + int(rhs.ljust(8,'0'))


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



################################################################################
# Load the C++ utilites here
#
#    The SWIG/C++ block utilities give us access to the blockchain, fast ECDSA
#    operations, and general encryption/secure-binary containers
################################################################################
try:
   import CppBlockUtils as Cpp
   from CppBlockUtils import KdfRomix, CryptoECDSA, CryptoAES, SecureBinaryData
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
# Might as well create the BDM right here -- there will only ever be one, anyway
# NOTE: Moved this to the end, after the BDMThreadManager class, so that if the 
#       option is selected, TheBDM can reference the asynchronous version.
#TheBDM = Cpp.BlockDataManager().getBDM()



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


def getCurrTimeAndBlock():
   time0 = long(RightNowUTC())
   if TheBDM.isInitialized():
      return (time0, TheBDM.getTopBlockHeader().getBlockHeight())
   else:
      return (time0, UINT32_MAX)
   


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


   




################################################################################
def hash160_to_addrStr(binStr):
   """
   Converts the 20-byte pubKeyHash to 25-byte binary Bitcoin address
   which includes the network byte (prefix) and 4-byte checksum (suffix)
   """
   addr21 = ADDRBYTE + binStr
   addr25 = addr21 + hash256(addr21)[:4]
   return binary_to_base58(addr25);

################################################################################
def addrStr_to_hash160(binStr):
   return base58_to_binary(binStr)[1:-4]





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



################################################################################
def BDM_LoadBlockchainFile(blkdir=None, wltList=None):
   """
   Looks for blkXXXX.dat files.  If they are found, it is indexed into RAM
   and then all blockchain data can be accessed through the BDM object. 
   Access to any information in the blockchain can be found via
   the bdm object.

   NOTE:  DO NOT USE THIS for the multi-threaded BDM
   """

   
   if blkdir==None:
      blkdir = BTC_HOME_DIR

   if not os.path.exists(blkdir):
      raise FileExistsError, ('Directory does not exist: %s' % blkdir)

   TheBDM.SetBtcNetworkParams( GENESIS_BLOCK_HASH, GENESIS_TX_HASH, MAGIC_BYTES)

   # Register wallets so that they can be included in the initial scan
   if wltList:
      for wlt in wltList:
         TheBDM.registerWallet(wlt.cppWallet, False)  # isWltNew=False

   return TheBDM.parseEntireBlockchain(blkdir)


################################################################################
################################################################################
#  Classes for reading and writing large binary objects
################################################################################
################################################################################
UINT8, UINT16, UINT32, UINT64, INT8, INT16, INT32, INT64, VAR_INT, VAR_STR, FLOAT, BINARY_CHUNK = range(12)

# Seed this object with binary data, then read in its pieces sequentially
class BinaryUnpacker(object):
   """
   Class for helping unpack binary streams of data.  Typical usage is
      >> bup     = BinaryUnpacker(myBinaryData)
      >> int32   = bup.get(UINT32)
      >> int64   = bup.get(VAR_INT)
      >> bytes10 = bup.get(BINARY_CHUNK, 10)
      >> ...etc...
   """
   def __init__(self, binaryStr):
      self.binaryStr = binaryStr
      self.pos = 0

   def getSize(self): return len(self.binaryStr)
   def getRemainingSize(self): return len(self.binaryStr) - self.pos
   def getBinaryString(self): return self.binaryStr
   def getRemainingString(self): return self.binaryStr[self.pos:]
   def append(self, binaryStr): self.binaryStr += binaryStr
   def advance(self, bytesToAdvance): self.pos += bytesToAdvance
   def rewind(self, bytesToRewind): self.pos -= bytesToRewind
   def resetPosition(self, toPos=0): self.pos = toPos
   def getPosition(self): return self.pos

   def get(self, varType, sz=0, endianness=LITTLEENDIAN):
      """
      First argument is the data-type:  UINT32, VAR_INT, etc.
      If BINARY_CHUNK, need to supply a number of bytes to read, as well
      """
      def sizeCheck(sz):
         if self.getRemainingSize()<sz:
            raise UnpackerError

      E = endianness
      pos = self.pos
      if varType == UINT32:
         sizeCheck(4)
         value = unpack(E+'I', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == UINT64:
         sizeCheck(8)
         value = unpack(E+'Q', self.binaryStr[pos:pos+8])[0]
         self.advance(8)
         return value
      elif varType == UINT8:
         sizeCheck(1)
         value = unpack(E+'B', self.binaryStr[pos:pos+1])[0]
         self.advance(1)
         return value
      elif varType == UINT16:
         sizeCheck(2)
         value = unpack(E+'H', self.binaryStr[pos:pos+2])[0]
         self.advance(2)
         return value
      elif varType == INT32:
         sizeCheck(4)
         value = unpack(E+'i', self.binaryStr[pos:pos+4])[0]
         self.advance(4)
         return value
      elif varType == INT64:
         sizeCheck(8)
         value = unpack(E+'q', self.binaryStr[pos:pos+8])[0]
         self.advance(8)
         return value
      elif varType == INT8:
         sizeCheck(1)
         value = unpack(E+'b', self.binaryStr[pos:pos+1])[0]
         self.advance(1)
         return value
      elif varType == INT16:
         sizeCheck(2)
         value = unpack(E+'h', self.binaryStr[pos:pos+2])[0]
         self.advance(2)
         return value
      elif varType == VAR_INT:
         sizeCheck(1)
         [value, nBytes] = unpackVarInt(self.binaryStr[pos:pos+9])
         self.advance(nBytes)
         return value
      elif varType == VAR_STR:
         sizeCheck(1)
         [value, nBytes] = unpackVarInt(self.binaryStr[pos:pos+9])
         binOut = self.binaryStr[pos+nBytes:pos+nBytes+value]
         self.advance(nBytes+value)
         return binOut
      elif varType == FLOAT:
         sizeCheck(4)
         value = unpack(E+'f', self.binaryStr[pos:pos+4])
         self.advance(4)
         return value
      elif varType == BINARY_CHUNK:
         sizeCheck(sz)
         binOut = self.binaryStr[pos:pos+sz]
         self.advance(sz)
         return binOut

      LOGERROR('Var Type not recognized!  VarType = %d', varType)
      raise UnpackerError, "Var type not recognized!  VarType="+str(varType)



# Start a buffer for concatenating various blocks of binary data
class BinaryPacker(object):
   """
   Class for helping load binary data into a stream.  Typical usage is
      >> binpack = BinaryPacker()
      >> bup.put(UINT32, 12)
      >> bup.put(VAR_INT, 78)
      >> bup.put(BINARY_CHUNK, '\x9f'*10)
      >> ...etc...
      >> result = bup.getBinaryString()
   """
   def __init__(self):
      self.binaryConcat = []

   def getSize(self):
      return sum([len(a) for a in self.binaryConcat])

   def getBinaryString(self):
      return ''.join(self.binaryConcat)

   def __str__(self):
      return self.getBinaryString()


   def put(self, varType, theData, width=None, endianness=LITTLEENDIAN):
      """
      Need to supply the argument type you are put'ing into the stream.
      Values of BINARY_CHUNK will automatically detect the size as necessary

      Use width=X to include padding of BINARY_CHUNKs w/ 0x00 bytes
      """
      E = endianness
      if   varType == UINT8:
         self.binaryConcat += int_to_binary(theData, 1, endianness)
      elif varType == UINT16:
         self.binaryConcat += int_to_binary(theData, 2, endianness)
      elif varType == UINT32:
         self.binaryConcat += int_to_binary(theData, 4, endianness)
      elif varType == UINT64:
         self.binaryConcat += int_to_binary(theData, 8, endianness)
      elif varType == INT8:
         self.binaryConcat += pack(E+'b', theData)
      elif varType == INT16:
         self.binaryConcat += pack(E+'h', theData)
      elif varType == INT32:
         self.binaryConcat += pack(E+'i', theData)
      elif varType == INT64:
         self.binaryConcat += pack(E+'q', theData)
      elif varType == VAR_INT:
         self.binaryConcat += packVarInt(theData)[0]
      elif varType == VAR_STR:
         self.binaryConcat += packVarInt(len(theData))[0]
         self.binaryConcat += theData
      elif varType == FLOAT:
         self.binaryConcat += pack(E+'f', theData)
      elif varType == BINARY_CHUNK:
         if width==None:
            self.binaryConcat += theData
         else:
            if len(theData)>width:
               raise PackerError, 'Too much data to fit into fixed width field'
            self.binaryConcat += theData.ljust(width, '\x00')
      else:
         raise PackerError, "Var type not recognized!  VarType="+str(varType)

################################################################################

# The following params are common to ALL bitcoin elliptic curves (secp256k1)
#_p  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
#_r  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
#_b  = 0x0000000000000000000000000000000000000000000000000000000000000007L
#_a  = 0x0000000000000000000000000000000000000000000000000000000000000000L
#_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
#_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L


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


def convertKeyDataToAddress(privKey=None, pubKey=None):
   if not privKey and not pubKey:
      raise BadAddressError, 'No key data supplied for conversion'
   elif privKey:
      if isinstance(privKey, str):
         privKey = SecureBinaryData(privKey)

      if not privKey.getSize()==32:
         raise BadAddressError, 'Invalid private key format!'
      else:
         pubKey = CryptoECDSA().ComputePublicKey(privKey)

   if isinstance(pubKey,str):
      pubKey = SecureBinaryData(pubKey)
   return pubKey.getHash160()



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

      hexCount = sum([1 if c in hexChars else 0 for c in theStr])
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
               raise BadInputError, 'Invalid mini-private key string'
            keyType = 'Mini Private Key Format'
            isMini = True
         elif len(theStr) in range(48,53):
            binEntry = base58_to_binary(theStr)
            keyType = 'Plain Base58'
         else:
            raise BadInputError, 'Unrecognized key data'
      elif canBeHex:  
         binEntry = hex_to_binary(theStr)
         keyType = 'Plain Hex'
      else:
         raise BadInputError, 'Unrecognized key data'


      if len(binEntry)==36 or (len(binEntry)==37 and binEntry[0]=='\x80'):
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



################################################################################
class PyBtcAddress(object):
   """
   PyBtcAddress --

   This class encapsulated EVERY kind of address object:
      -- Plaintext private-key-bearing addresses
      -- Encrypted private key addresses, with AES locking and unlocking
      -- Watching-only public-key addresses
      -- Address-only storage, representing someone else's key
      -- Deterministic address generation from previous addresses
      -- Serialization and unserialization of key data under all conditions
      -- Checksums on all serialized fields to protect against HDD byte errors

      For deterministic wallets, new addresses will be created from a chaincode
      and the previous address.  What is implemented here is a special kind of
      deterministic calculation that actually allows the user to securely
      generate new addresses even if they don't have the private key.  This
      method uses Diffie-Hellman shared-secret calculations to produce the new
      keys, and has the same level of security as all other ECDSA operations.
      There's a lot of fantastic benefits to doing this:

         (1) If all addresses in wallet are chained, then you only need to backup
             your wallet ONCE -- when you first create it.  Print it out, put it
             in a safety-deposit box, or tattoo the generator key to the inside
             of your eyelid:  it will never change.

         (2) You can keep your private keys on an offline machine, and keep a
             watching-only wallet online.  You will be able to generate new
             keys/addresses, and verify incoming transactions, without ever
             requiring your private key to touch the internet.

         (3) If your friend has the chaincode and your first public key, they
             too can generate new addresses for you -- allowing them to send
             you money multiple times, with different addresses, without ever
             needing to specifically request the addresses.
             (the downside to this is if the chaincode is compromised, all
             chained addresses become de-anonymized -- but is only a loss of
             privacy, not security)

      However, we do require some fairly complicated logic, due to the fact
      that a user with a full, private-key-bearing wallet, may try to generate
      a new key/address without supplying a passphrase.  If this happens, the
      wallet logic gets very complicated -- we don't want to reject the request
      to generate a new address, but we can't compute the private key until the
      next time the user unlocks their wallet.  Thus, we have to save off the
      data they will need to create the key, to be applied on next unlock.
   """
   #############################################################################
   def __init__(self):
      """
      We use SecureBinaryData objects to store pub, priv and IV objects,
      because that is what is required by the C++ code.  See EncryptionUtils.h
      to see that available methods.
      """
      self.addrStr20             = ''
      self.binPublicKey65        = SecureBinaryData()  # 0x04 X(BE) Y(BE)
      self.binPrivKey32_Encr     = SecureBinaryData()  # BIG-ENDIAN
      self.binPrivKey32_Plain    = SecureBinaryData()
      self.binInitVect16         = SecureBinaryData()
      self.isLocked              = False
      self.useEncryption         = False
      self.isInitialized         = False
      self.keyChanged            = False   # ...since last key encryption
      self.walletByteLoc         = -1
      self.chaincode             = SecureBinaryData()
      self.chainIndex            = 0

      # Information to be used by C++ to know where to search for transactions
      # in the blockchain (disabled in favor of a better search method)
      self.timeRange = [2**32-1, 0]
      self.blkRange  = [2**32-1, 0]

      # This feels like a hack, but it's the only way I can think to handle
      # the case of generating new, chained addresses, even without the
      # private key currently in memory.  i.e. - If we can't unlock the priv
      # key when creating a new chained priv key, we will simply extend the
      # public key, and store the last-known chain info, so that it can be
      # generated the next time the address is unlocked
      self.createPrivKeyNextUnlock             = False
      self.createPrivKeyNextUnlock_IVandKey    = [None, None] # (IV,Key)
      self.createPrivKeyNextUnlock_ChainDepth  = -1

   #############################################################################
   def isInitialized(self):
      """ Keep track of whether this address has been initialized """
      return self.isInitialized

   #############################################################################
   def hasPrivKey(self):
      """
      We have a private key if either the plaintext, or ciphertext private-key
      fields are non-empty.  We also consider ourselves to "have" the private
      key if this address was chained from a key that has the private key, even
      if we haven't computed it yet (due to not having unlocked the private key
      before creating the new address).
      """
      return (self.binPrivKey32_Encr.getSize()  != 0 or \
              self.binPrivKey32_Plain.getSize() != 0 or \
              self.createPrivKeyNextUnlock)

   #############################################################################
   def hasPubKey(self):
      return (self.binPublicKey65.getSize() != 0)

   #############################################################################
   def getAddrStr(self, netbyte=ADDRBYTE):
      chksum = hash256(netbyte + self.addrStr20)[:4]
      return binary_to_base58(netbyte + self.addrStr20 + chksum)

   #############################################################################
   def getAddr160(self):
      if len(self.addrStr20)!=20:
         raise KeyDataError, 'PyBtcAddress does not have an address string!'
      return self.addrStr20

   #############################################################################
   def touch(self, unixTime=None, blkNum=None):
      """
      Just like "touching" a file, this makes sure that the firstSeen and
      lastSeen fields for this address are updated to include "now"

      If we include only a block number, we will fill in the timestamp with
      the unix-time for that block (if the BlockDataManager is availabled)
      """
      if self.blkRange[0]==0:
         self.blkRange[0]=2**32-1
      if self.timeRange[0]==0:
         self.timeRange[0]=2**32-1

      if blkNum==None:
         if TheBDM.isInitialized():
            topBlk = TheBDM.getTopBlockHeader().getBlockHeight()
            self.blkRange[0] = long(min(self.blkRange[0], topBlk))
            self.blkRange[1] = long(max(self.blkRange[1], topBlk))
      else:
         self.blkRange[0]  = long(min(self.blkRange[0], blkNum))
         self.blkRange[1]  = long(max(self.blkRange[1], blkNum))

         if unixTime==None and TheBDM.isInitialized():
            unixTime = TheBDM.getHeaderByHeight(blkNum).getTimestamp()

      if unixTime==None:
         unixTime = RightNow()

      self.timeRange[0] = long(min(self.timeRange[0], unixTime))
      self.timeRange[1] = long(max(self.timeRange[1], unixTime))



   #############################################################################
   def copy(self):
      newAddr = PyBtcAddress().unserialize(self.serialize())
      newAddr.binPrivKey32_Plain = self.binPrivKey32_Plain.copy()
      newAddr.binPrivKey32_Encr  = self.binPrivKey32_Encr.copy()
      newAddr.binPublicKey65     = self.binPublicKey65.copy()
      newAddr.binInitVect16      = self.binInitVect16.copy()
      newAddr.isLocked           = self.isLocked
      newAddr.useEncryption      = self.useEncryption
      newAddr.isInitialized      = self.isInitialized
      newAddr.keyChanged         = self.keyChanged
      newAddr.walletByteLoc      = self.walletByteLoc
      newAddr.chaincode          = self.chaincode
      newAddr.chainIndex         = self.chainIndex
      return newAddr



   #############################################################################
   def getTimeRange(self):
      return self.timeRange

   #############################################################################
   def getBlockRange(self):
      return self.blkRange

   #############################################################################
   def serializePublicKey(self):
      """Converts the SecureBinaryData public key to a 65-byte python string"""
      return self.binPublicKey65.toBinStr()

   #############################################################################
   def serializeEncryptedPrivateKey(self):
      """Converts SecureBinaryData encrypted private key to python string"""
      return self.binPrivKey32_Encr.toBinStr()

   #############################################################################
   # NOTE:  This method should rarely be used, unless we are only printing it
   #        to the screen.  Actually, it will be used for unencrypted wallets
   def serializePlainPrivateKey(self):
      return self.binPrivKey32_Plain.toBinStr()

   def serializeInitVector(self):
      return self.binInitVect16.toBinStr()


   #############################################################################
   def verifyEncryptionKey(self, secureKdfOutput):
      """
      Determine if this data is the decryption key for this encrypted address
      """
      if not self.useEncryption or not self.hasPrivKey():
         return False

      if self.useEncryption and not secureKdfOutput:
         LOGERROR('No encryption key supplied to verifyEncryption!')
         return False


      decryptedKey = CryptoAES().DecryptCFB( self.binPrivKey32_Encr, \
                                             SecureBinaryData(secureKdfOutput), \
                                             self.binInitVect16)
      verified = False

      if not self.isLocked:
         if decryptedKey==self.binPrivKey32_Plain:
            verified = True
      else:
         computedPubKey = CryptoECDSA().ComputePublicKey(decryptedKey)
         if self.hasPubKey():
            verified = (self.binPublicKey65==computedPubKey)
         else:
            self.binPublicKey65 = computedPubKey
            verified = (computedPubKey.getHash160()==self.addrStr20)

      decryptedKey.destroy()
      return verified



   #############################################################################
   def setInitializationVector(self, IV16=None, random=False, force=False):
      """
      Either set the IV through input arg, or explicitly call random=True
      Returns the IV -- which is especially important if it is randomly gen

      This method is mainly for PREVENTING you from changing an existing IV
      without meaning to.  Losing the IV for encrypted data is almost as bad
      as losing the encryption key.  Caller must use force=True in order to
      override this warning -- otherwise this method will abort.
      """
      if self.binInitVect16.getSize()==16:
         if self.isLocked:
            LOGERROR('Address already locked with different IV.')
            LOGERROR('Changing IV may cause loss of keydata.')
         else:
            LOGERROR('Address already contains an initialization')
            LOGERROR('vector.  If you change IV without updating')
            LOGERROR('the encrypted storage, you may permanently')
            LOGERROR('lose the encrypted data')

         if not force:
            LOGERROR('If you really want to do this, re-execute this call with force=True')
            return ''

      if IV16:
         self.binInitVect16 = SecureBinaryData(IV16)
      elif random==True:
         self.binInitVect16 = SecureBinaryData().GenerateRandom(16)
      else:
         raise KeyDataError, 'setInitVector: set IV data, or random=True'
      return self.binInitVect16

   #############################################################################
   def enableKeyEncryption(self, IV16=None, generateIVIfNecessary=False):
      """
      setIV method will raise error is we don't specify any args, but it is
      acceptable HERE to not specify any args just to enable encryption
      """
      self.useEncryption = True
      if IV16:
         self.setInitializationVector(IV16)
      elif generateIVIfNecessary and self.binInitVect16.getSize()<16:
         self.setInitializationVector(random=True)
   

   #############################################################################
   def isKeyEncryptionEnabled(self):
      return self.useEncryption


   #############################################################################
   def createFromEncryptedKeyData(self, addr20, encrPrivKey32, IV16, \
                                                     chkSum=None, pubKey=None):
      # We expect both private key and IV to the right size
      assert(encrPrivKey32.getSize()==32)
      assert(IV16.getSize()==16)
      self.__init__()
      self.addrStr20     = addr20
      self.binPrivKey32_Encr = SecureBinaryData(encrPrivKey32)
      self.setInitializationVector(IV16)
      self.isLocked      = True
      self.useEncryption = True
      self.isInitialized = True
      if chkSum and not self.binPrivKey32_Encr.getHash256().startswith(chkSum):
         raise ChecksumError, "Checksum doesn't match encrypted priv key data!"
      if pubKey:
         self.binPublicKey65 = SecureBinaryData(pubKey)
         if not self.binPublicKey65.getHash160()==self.addrStr20:
            raise KeyDataError, "Public key does not match supplied address"

      return self


   #############################################################################
   def createFromPlainKeyData(self, plainPrivKey, addr160=None, willBeEncr=False, \
                                    generateIVIfNecessary=False, IV16=None, \
                                    chksum=None, publicKey65=None, \
                                    skipCheck=False, skipPubCompute=False):

      assert(plainPrivKey.getSize()==32)

      if not addr160:
         addr160 = convertKeyDataToAddress(privKey=plainPrivKey)

      self.__init__()
      self.addrStr20 = addr160
      self.isInitialized = True
      self.binPrivKey32_Plain = SecureBinaryData(plainPrivKey)
      self.isLocked = False

      if willBeEncr:
         self.enableKeyEncryption(IV16, generateIVIfNecessary)
      elif IV16:
         self.binInitVect16 = IV16

      if chksum and not verifyChecksum(self.binPrivKey32_Plain.toBinStr(), chksum):
         raise ChecksumError, "Checksum doesn't match plaintext priv key!"
      if publicKey65:
         self.binPublicKey65 = SecureBinaryData(publicKey65)
         if not self.binPublicKey65.getHash160()==self.addrStr20:
            raise KeyDataError, "Public key does not match supplied address"
         if not skipCheck:
            if not CryptoECDSA().CheckPubPrivKeyMatch(self.binPrivKey32_Plain,\
                                                      self.binPublicKey65):
               raise KeyDataError, 'Supplied pub and priv key do not match!'
      elif not skipPubCompute:
         # No public key supplied, but we do want to calculate it
         self.binPublicKey65 = CryptoECDSA().ComputePublicKey(plainPrivKey)

      return self

   #############################################################################
   def createFromPublicKeyData(self, publicKey65, chksum=None):

      assert(publicKey65.getSize()==65)
      self.__init__()
      self.addrStr20 = publicKey65.getHash160()
      self.binPublicKey65 = publicKey65
      self.isInitialized = True
      self.isLocked = False
      self.useEncryption = False

      if chksum and not verifyChecksum(self.binPublicKey65.toBinStr(), chksum):
         raise ChecksumError, "Checksum doesn't match supplied public key!"

      return self


   #############################################################################
   def lock(self, secureKdfOutput=None, generateIVIfNecessary=False):
      # We don't want to destroy the private key if it's not supposed to be
      # encrypted.  Similarly, if we haven't actually saved the encrypted
      # version, let's not lock it
      newIV = False
      if not self.useEncryption or not self.hasPrivKey():
         # This isn't supposed to be encrypted, or there's no privkey to encrypt
         return
      else:
         if self.binPrivKey32_Encr.getSize()==32 and not self.keyChanged:
            # Addr should be encrypted, and we already have encrypted priv key
            self.binPrivKey32_Plain.destroy()
            self.isLocked = True
         else:
            # Addr should be encrypted, but haven't computed encrypted value yet
            if secureKdfOutput!=None:
               # We have an encryption key, use it
               if self.binInitVect16.getSize() < 16:
                  if not generateIVIfNecessary:
                     raise KeyDataError, 'No Initialization Vector available'
                  else:
                     self.binInitVect16 = SecureBinaryData().GenerateRandom(16)
                     newIV = True

               # Finally execute the encryption
               self.binPrivKey32_Encr = CryptoAES().EncryptCFB( \
                                                self.binPrivKey32_Plain, \
                                                SecureBinaryData(secureKdfOutput), \
                                                self.binInitVect16)
               # Destroy the unencrypted key, reset the keyChanged flag
               self.binPrivKey32_Plain.destroy()
               self.isLocked = True
               self.keyChanged = False
            else:
               # Can't encrypt the addr because we don't have encryption key
               raise WalletLockError, ("\n\tTrying to destroy plaintext key, but no"
                                       "\n\tencrypted key data is available, and no"
                                       "\n\tencryption key provided to encrypt it.")


      # In case we changed the IV, we should let the caller know this
      return self.binInitVect16 if newIV else SecureBinaryData()


   #############################################################################
   def unlock(self, secureKdfOutput, skipCheck=False):
      """
      This method knows nothing about a key-derivation function.  It simply
      takes in an AES key and applies it to decrypt the data.  However, it's
      best if that AES key is actually derived from "heavy" key-derivation
      function.
      """
      if not self.useEncryption or not self.isLocked:
         # Bail out if the wallet is unencrypted, or already unlocked
         self.isLocked = False
         return


      if self.createPrivKeyNextUnlock:
         # This is SPECIFICALLY for the case that we didn't have the encr key
         # available when we tried to extend our deterministic wallet, and
         # generated a new address anyway
         self.binPrivKey32_Plain = CryptoAES().DecryptCFB( \
                                     self.createPrivKeyNextUnlock_IVandKey[1], \
                                     SecureBinaryData(secureKdfOutput), \
                                     self.createPrivKeyNextUnlock_IVandKey[0])

         for i in range(self.createPrivKeyNextUnlock_ChainDepth):
            self.binPrivKey32_Plain = CryptoECDSA().ComputeChainedPrivateKey( \
                                         self.binPrivKey32_Plain, \
                                         self.chaincode)


         # IV should have already been randomly generated, before
         self.isLocked = False
         self.createPrivKeyNextUnlock            = False
         self.createPrivKeyNextUnlock_IVandKey   = []
         self.createPrivKeyNextUnlock_ChainDepth = 0

         # Lock/Unlock to make sure encrypted private key is filled
         self.lock(secureKdfOutput,generateIVIfNecessary=True)
         self.unlock(secureKdfOutput)

      else:

         if not self.binPrivKey32_Encr.getSize()==32:
            raise WalletLockError, 'No encrypted private key to decrypt!'

         if not self.binInitVect16.getSize()==16:
            raise WalletLockError, 'Initialization Vect (IV) is missing!'

         self.binPrivKey32_Plain = CryptoAES().DecryptCFB( \
                                        self.binPrivKey32_Encr, \
                                        secureKdfOutput, \
                                        self.binInitVect16)

      self.isLocked = False

      if not skipCheck:
         if not self.hasPubKey():
            self.binPublicKey65 = CryptoECDSA().ComputePublicKey(\
                                                      self.binPrivKey32_Plain)
         else:
            # We should usually check that keys match, but may choose to skip
            # if we have a lot of keys to load
            if not CryptoECDSA().CheckPubPrivKeyMatch(self.binPrivKey32_Plain, \
                                            self.binPublicKey65):
               raise KeyDataError, "Stored public key does not match priv key!"


   #############################################################################
   def changeEncryptionKey(self, secureOldKey, secureNewKey):
      """
      We will use None to specify "no encryption", either for old or new.  Of
      course we throw an error is old key is "None" but the address is actually
      encrypted.
      """
      if not self.hasPrivKey():
         raise KeyDataError, 'No private key available to re-encrypt'

      if not secureOldKey and self.useEncryption and self.isLocked:
         raise WalletLockError, 'Need old encryption key to unlock private keys'

      wasLocked = self.isLocked

      # Decrypt the original key
      if self.isLocked:
         self.unlock(secureOldKey, skipCheck=False)

      # Keep the old IV if we are changing the key.  IV reuse is perfectly
      # fine for a new key, and might save us from disaster if we otherwise
      # generated a new one and then forgot to take note of it.
      self.keyChanged = True
      if not secureNewKey:
         # If we chose not to re-encrypt, make sure we clear the encryption
         self.binInitVect16     = SecureBinaryData()
         self.binPrivKey32_Encr = SecureBinaryData()
         self.isLocked          = False
         self.useEncryption     = False
      else:
         # Re-encrypt with new key (using same IV)
         self.useEncryption = True
         self.lock(secureNewKey)  # do this to make sure privKey_Encr filled
         if wasLocked:
            self.isLocked = True
         else:
            self.unlock(secureNewKey)
            self.isLocked = False




   #############################################################################
   # This is more of a static method
   def checkPubPrivKeyMatch(self, securePriv, securePub):
      CryptoECDSA().CheckPubPrivKeyMatch(securePriv, securePub)



   #############################################################################
   def generateDERSignature(self, binMsg, secureKdfOutput=None):
      """
      This generates a DER signature for this address using the private key.
      Obviously, if we don't have the private key, we throw an error.  Or if
      the wallet is locked and no encryption key was provided.

      If an encryption key IS provided, then we unlock the address just long
      enough to sign the message and then re-lock it
      """
      if not self.hasPrivKey():
         raise KeyDataError, 'Cannot sign for address without private key!'

      if self.isLocked:
         if secureKdfOutput==None:
            raise WalletLockError, "Cannot sign Tx when private key is locked!"
         else:
            # Wallet is locked but we have a decryption key
            self.unlock(secureKdfOutput, skipCheck=False)

      try:
         secureMsg = SecureBinaryData(binMsg)
         sig = CryptoECDSA().SignData(secureMsg, self.binPrivKey32_Plain)
         sigstr = sig.toBinStr()
         # We add an extra 0 byte to the beginning of each value to guarantee
         # that they are interpretted as unsigned integers.  Not always necessary
         # but it doesn't hurt to always do it.
         rBin   = '\x00' + sigstr[:32 ]
         sBin   = '\x00' + sigstr[ 32:]
         rSize  = int_to_binary(len(rBin))
         sSize  = int_to_binary(len(sBin))
         rsSize = int_to_binary(len(rBin) + len(sBin) + 4)
         sigScr = '\x30' + rsSize + \
                  '\x02' + rSize + rBin + \
                  '\x02' + sSize + sBin
         return sigScr
      except:
         LOGERROR('Failed signature generation')
      finally:
         # Always re-lock/cleanup after unlocking, even after an exception.
         # If locking triggers an error too, we will just skip it.
         try:
            if secureKdfOutput!=None:
               self.lock(secureKdfOutput)
         except:
            pass




   #############################################################################
   def verifyDERSignature(self, binMsgVerify, derSig):
      if not self.hasPubKey():
         raise KeyDataError, 'No public key available for this address!'

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

      secMsg    = SecureBinaryData(binMsgVerify)
      secSig    = SecureBinaryData(r[-32:] + s[-32:])
      secPubKey = SecureBinaryData(self.binPublicKey65)
      return CryptoECDSA().VerifyData(secMsg, secSig, secPubKey)



   #############################################################################
   def createNewRandomAddress(self, secureKdfOutput=None, IV16=None):
      """
      This generates a new private key directly into a secure binary container
      and then encrypts it immediately if encryption is enabled and the AES key
      (from KDF) is available to do so.  This behaves like a static method,
      returning a copy/ref to itself.

      TODO:  There is no way for this method to know whether you wanted the
             key to be encrypted forgot to provide a key
      """
      self.__init__()
      self.binPrivKey32_Plain = CryptoECDSA().GenerateNewPrivateKey()
      self.binPublicKey65 = CryptoECDSA().ComputePublicKey(self.binPrivKey32_Plain)
      self.addrStr20 = self.binPublicKey65.getHash160()
      self.isInitialized = True

      if secureKdfOutput!=None:
         self.binInitVect16 = IV16
         if IV16==None or IV16.getSize()!=16:
            self.binInitVect16 = SecureBinaryData().GenerateRandom(16)
         self.lock(secureKdfOutput)
         self.isLocked      = True
         self.useEncryption = True
      else:
         self.isLocked      = False
         self.useEncryption = False
      return self


   #############################################################################
   def markAsRootAddr(self, chaincode):
      if not chaincode.getSize()==32:
         raise KeyDataError, 'Chaincode must be 32 bytes'
      else:
         self.chainIndex = -1
         self.chaincode  = chaincode


   #############################################################################
   def isAddrChainRoot(self):
      return (self.chainIndex==-1)

   #############################################################################
   def extendAddressChain(self, secureKdfOutput=None, newIV=None):
      """
      We require some fairly complicated logic here, due to the fact that a
      user with a full, private-key-bearing wallet, may try to generate a new
      key/address without supplying a passphrase.  If this happens, the wallet
      logic gets mucked up -- we don't want to reject the request to
      generate a new address, but we can't compute the private key until the
      next time the user unlocks their wallet.  Thus, we have to save off the
      data they will need to create the key, to be applied on next unlock.
      """
      LOGDEBUG('Extending address chain')
      if not self.chaincode.getSize() == 32:
         raise KeyDataError, 'No chaincode has been defined to extend chain'

      newAddr = PyBtcAddress()
      privKeyAvailButNotDecryptable = (self.hasPrivKey() and \
                                       self.isLocked     and \
                                       not secureKdfOutput  )


      if self.hasPrivKey() and not privKeyAvailButNotDecryptable:
         # We are extending a chain using private key data
         wasLocked = self.isLocked
         if self.useEncryption and self.isLocked:
            if not secureKdfOutput:
               raise WalletLockError, 'Cannot create new address without passphrase'
            self.unlock(secureKdfOutput)
         if not newIV:
            newIV = SecureBinaryData().GenerateRandom(16)

         if self.hasPubKey():
            newPriv = CryptoECDSA().ComputeChainedPrivateKey( \
                                    self.binPrivKey32_Plain, \
                                    self.chaincode, \
                                    self.binPublicKey65)
         else:
            newPriv = CryptoECDSA().ComputeChainedPrivateKey( \
                                    self.binPrivKey32_Plain, \
                                    self.chaincode)
         newPub  = CryptoECDSA().ComputePublicKey(newPriv)
         newAddr160 = newPub.getHash160()
         newAddr.createFromPlainKeyData(newPriv, newAddr160, \
                                       IV16=newIV, publicKey65=newPub)

         newAddr.addrStr20 = newPub.getHash160()
         newAddr.useEncryption = self.useEncryption
         newAddr.isInitialized = True
         newAddr.chaincode     = self.chaincode
         newAddr.chainIndex    = self.chainIndex+1

         # We can't get here without a secureKdfOutput (I think)
         if newAddr.useEncryption:
            newAddr.lock(secureKdfOutput)
            if not wasLocked:
               newAddr.unlock(secureKdfOutput)
               self.unlock(secureKdfOutput)
         return newAddr
      else:
         # We are extending the address based solely on its public key
         if not self.hasPubKey():
            raise KeyDataError, 'No public key available to extend chain'
         newAddr.binPublicKey65 = CryptoECDSA().ComputeChainedPublicKey( \
                                    self.binPublicKey65, self.chaincode)
         newAddr.addrStr20 = newAddr.binPublicKey65.getHash160()
         newAddr.useEncryption = self.useEncryption
         newAddr.isInitialized = True
         newAddr.chaincode  = self.chaincode
         newAddr.chainIndex = self.chainIndex+1


         if privKeyAvailButNotDecryptable:
            # *** store what is needed to recover key on next addr unlock ***
            newAddr.isLocked      = True
            newAddr.useEncryption = True
            if not newIV:
               newIV = SecureBinaryData().GenerateRandom(16)
            newAddr.binInitVect16 = newIV
            newAddr.createPrivKeyNextUnlock           = True
            newAddr.createPrivKeyNextUnlock_IVandKey = [None,None]
            if self.createPrivKeyNextUnlock:
               # We are chaining from address also requiring gen on next unlock
               newAddr.createPrivKeyNextUnlock_IVandKey[0] = \
                  self.createPrivKeyNextUnlock_IVandKey[0].copy()
               newAddr.createPrivKeyNextUnlock_IVandKey[1] = \
                  self.createPrivKeyNextUnlock_IVandKey[1].copy()
               newAddr.createPrivKeyNextUnlock_ChainDepth = \
                  self.createPrivKeyNextUnlock_ChainDepth+1
            else:
               # The address from which we are extending has already been generated
               newAddr.createPrivKeyNextUnlock_IVandKey[0] = self.binInitVect16.copy()
               newAddr.createPrivKeyNextUnlock_IVandKey[1] = self.binPrivKey32_Encr.copy()
               newAddr.createPrivKeyNextUnlock_ChainDepth  = 1
         return newAddr


   def serialize(self):
      """
      We define here a binary serialization scheme that will write out ALL
      information needed to completely reconstruct address data from file.
      This method returns a string, but presumably will be used to write addr
      data to file.  The following format is used.

         Address160  (20 bytes) :  The 20-byte hash of the public key
                                   This must always be the first field
         AddressChk  ( 4 bytes) :  Checksum to make sure no error in addr160
         AddrVersion ( 4 bytes) :  Early version don't specify encrypt params
         Flags       ( 8 bytes) :  Addr-specific info, including encrypt params

         ChainCode   (32 bytes) :  For extending deterministic wallets
         ChainChk    ( 4 bytes) :  Checksum for chaincode
         ChainIndex  ( 8 bytes) :  Index in chain if deterministic addresses
         ChainDepth  ( 8 bytes) :  How deep addr is in chain beyond last
                                   computed private key (if base address was
                                   locked when we tried to extend/chain it)

         InitVect    (16 bytes) :  Initialization vector for encryption
         InitVectChk ( 4 bytes) :  Checksum for IV
         PrivKey     (32 bytes) :  Private key data (may be encrypted)
         PrivKeyChk  ( 4 bytes) :  Checksum for private key data

         PublicKey   (65 bytes) :  Public key for this address
         PubKeyChk   ( 4 bytes) :  Checksum for private key data


         FirstTime   ( 8 bytes) :  The first time  addr was seen in blockchain
         LastTime    ( 8 bytes) :  The last  time  addr was seen in blockchain
         FirstBlock  ( 4 bytes) :  The first block addr was seen in blockchain
         LastBlock   ( 4 bytes) :  The last  block addr was seen in blockchain
      """

      serializeWithEncryption = self.useEncryption

      if self.useEncryption and \
         self.binPrivKey32_Encr.getSize()==0 and \
         self.binPrivKey32_Plain.getSize()>0:
         LOGERROR('')
         LOGERROR('***WARNING: you have chosen to serialize a key you hope to be')
         LOGERROR('            encrypted, but have not yet chosen a passphrase for')
         LOGERROR('            it.  The only way to serialize this address is with ')
         LOGERROR('            the plaintext keys.  Please lock this address at')
         LOGERROR('            least once in order to enable encrypted output.')
         serializeWithEncryption = False

      # Before starting, let's construct the flags for this address
      nFlagBytes = 8
      flags = [False]*nFlagBytes*8
      flags[0] = self.hasPrivKey()
      flags[1] = self.hasPubKey()
      flags[2] = serializeWithEncryption
      flags[3] = self.createPrivKeyNextUnlock
      flags = ''.join([('1' if f else '0') for f in flags])

      def raw(a):
         if isinstance(a, str):
            return a
         else:
            return a.toBinStr()

      def chk(a):
         if isinstance(a, str):
            return computeChecksum(a,4)
         else:
            return computeChecksum(a.toBinStr(),4)

      # Use BinaryPacker "width" fields to guaranteee BINARY_CHUNK width.
      # Sure, if we have malformed data we might cut some of it off instead
      # of writing it to the binary stream.  But at least we'll ALWAYS be
      # able to determine where each field is, and will never corrupt the
      # whole wallet so badly we have to go hex-diving to figure out what
      # happened.
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK,   self.addrStr20,                    width=20)
      binOut.put(BINARY_CHUNK,   chk(self.addrStr20),               width= 4)
      binOut.put(UINT32,         getVersionInt(PYBTCWALLET_VERSION))
      binOut.put(UINT64,         bitset_to_int(flags))

      # Write out address-chaining parameters (for deterministic wallets)
      binOut.put(BINARY_CHUNK,   raw(self.chaincode),               width=32)
      binOut.put(BINARY_CHUNK,   chk(self.chaincode),               width= 4)
      binOut.put(INT64,          self.chainIndex)
      binOut.put(INT64,          self.createPrivKeyNextUnlock_ChainDepth)

      # Write out whatever is appropriate for private-key data
      # Binary-unpacker will write all 0x00 bytes if empty values are given
      if serializeWithEncryption:
         if self.createPrivKeyNextUnlock:
            binOut.put(BINARY_CHUNK,   raw(self.createPrivKeyNextUnlock_IVandKey[0]), width=16)
            binOut.put(BINARY_CHUNK,   chk(self.createPrivKeyNextUnlock_IVandKey[0]), width= 4)
            binOut.put(BINARY_CHUNK,   raw(self.createPrivKeyNextUnlock_IVandKey[1]), width=32)
            binOut.put(BINARY_CHUNK,   chk(self.createPrivKeyNextUnlock_IVandKey[1]), width= 4)
         else:
            binOut.put(BINARY_CHUNK,   raw(self.binInitVect16),     width=16)
            binOut.put(BINARY_CHUNK,   chk(self.binInitVect16),     width= 4)
            binOut.put(BINARY_CHUNK,   raw(self.binPrivKey32_Encr), width=32)
            binOut.put(BINARY_CHUNK,   chk(self.binPrivKey32_Encr), width= 4)
      else:
         binOut.put(BINARY_CHUNK,   raw(self.binInitVect16),        width=16)
         binOut.put(BINARY_CHUNK,   chk(self.binInitVect16),        width= 4)
         binOut.put(BINARY_CHUNK,   raw(self.binPrivKey32_Plain),   width=32)
         binOut.put(BINARY_CHUNK,   chk(self.binPrivKey32_Plain),   width= 4)

      binOut.put(BINARY_CHUNK, raw(self.binPublicKey65),            width=65)
      binOut.put(BINARY_CHUNK, chk(self.binPublicKey65),            width= 4)

      binOut.put(UINT64, self.timeRange[0])
      binOut.put(UINT64, self.timeRange[1])
      binOut.put(UINT32, self.blkRange[0])
      binOut.put(UINT32, self.blkRange[1])

      return binOut.getBinaryString()

   #############################################################################
   def scanBlockchainForAddress(self):
      if TheBDM.isInitialized():
         LOGDEBUG('Scanning blockchain for address')
         cppWlt = Cpp.BtcWallet()
         cppWlt.addAddress_1_(self.getAddr160())
         TheBDM.scanBlockchainForTx(cppWlt)
         utxoList = cppWlt.getUnspentTxOutList()
         bal = cppWlt.getBalance()
         return (bal, utxoList)

   #############################################################################
   def unserialize(self, toUnpack):
      """
      We reconstruct the address from a serialized version of it.  See the help
      text for "serialize()" for information on what fields need to
      be included and the binary mapping

      We verify all checksums, correct for one byte errors, and raise exceptions
      for bigger problems that can't be fixed.
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


      # Start with a fresh new address
      self.__init__()

      self.addrStr20 = serializedData.get(BINARY_CHUNK, 20)
      chkAddr20      = serializedData.get(BINARY_CHUNK,  4)

      addrVerInt     = serializedData.get(UINT32)
      flags          = serializedData.get(UINT64)
      self.addrStr20 = verifyChecksum(self.addrStr20, chkAddr20)
      flags = int_to_bitset(flags, widthBytes=8)

      # Interpret the flags
      containsPrivKey              = (flags[0]=='1')
      containsPubKey               = (flags[1]=='1')
      self.useEncryption           = (flags[2]=='1')
      self.createPrivKeyNextUnlock = (flags[3]=='1')

      addrChkError = False
      if len(self.addrStr20)==0:
         addrChkError = True
         if not containsPrivKey and not containsPubKey:
            raise UnserializeError, 'Checksum mismatch in addrStr'



      # Write out address-chaining parameters (for deterministic wallets)
      self.chaincode   = chkzero(serializedData.get(BINARY_CHUNK, 32))
      chkChaincode     =         serializedData.get(BINARY_CHUNK,  4)
      self.chainIndex  =         serializedData.get(INT64)
      depth            =         serializedData.get(INT64)
      self.createPrivKeyNextUnlock_ChainDepth = depth

      # Correct errors, convert to secure container
      self.chaincode = SecureBinaryData(verifyChecksum(self.chaincode, chkChaincode))


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
            raise UnserializeError, 'Checksum mismatch in PrivateKey '+\
                                    '('+hash160_to_addrStr(self.addrStr20)+')'

         if self.useEncryption:
            if iv.getSize()==0:
               raise UnserializeError, 'Checksum mismatch in IV ' +\
                                    '('+hash160_to_addrStr(self.addrStr20)+')'
            if self.createPrivKeyNextUnlock:
               self.createPrivKeyNextUnlock_IVandKey[0] = iv.copy()
               self.createPrivKeyNextUnlock_IVandKey[1] = privKey.copy()
            else:
               self.binInitVect16     = iv.copy()
               self.binPrivKey32_Encr = privKey.copy()
         else:
            self.binInitVect16      = iv.copy()
            self.binPrivKey32_Plain = privKey.copy()

      pubKey = chkzero(serializedData.get(BINARY_CHUNK, 65))
      chkPub =         serializedData.get(BINARY_CHUNK, 4)
      pubKey = SecureBinaryData(verifyChecksum(pubKey, chkPub))

      if containsPubKey:
         if not pubKey.getSize()==65:
            if self.binPrivKey32_Plain.getSize()==32:
               pubKey = CryptoAES().ComputePublicKey(self.binPrivKey32_Plain)
            else:
               raise UnserializeError, 'Checksum mismatch in PublicKey ' +\
                                       '('+hash160_to_addrStr(self.addrStr20)+')'

      self.binPublicKey65 = pubKey

      if addrChkError:
         self.addrStr20 = self.binPublicKey65.getHash160()

      self.timeRange[0] = serializedData.get(UINT64)
      self.timeRange[1] = serializedData.get(UINT64)
      self.blkRange[0]  = serializedData.get(UINT32)
      self.blkRange[1]  = serializedData.get(UINT32)

      self.isInitialized = True
      return self

   #############################################################################
   # The following methods are the SIMPLE address operations that can be used
   # to juggle address data without worrying at all about encryption details.
   # The addresses created here can later be endowed with encryption.
   #############################################################################
   def createFromPrivateKey(self, privKey, pubKey=None, skipCheck=False):
      """
      Creates address from a user-supplied random INTEGER.
      This method DOES perform elliptic-curve operations
      """
      if isinstance(privKey, str) and len(privKey)==32:
         self.binPrivKey32_Plain = SecureBinaryData(privKey)
      elif isinstance(privKey, int) or isinstance(privKey, long):
         binPriv = int_to_binary(privKey, widthBytes=32, endOut=BIGENDIAN)
         self.binPrivKey32_Plain = SecureBinaryData(binPriv)
      else:
         raise KeyDataError, 'Unknown private key format'

      if pubKey==None:
         self.binPublicKey65 = CryptoECDSA().ComputePublicKey(self.binPrivKey32_Plain)
      else:
         self.binPublicKey65 = SecureBinaryData(pubKey)

      if not skipCheck:
         assert(CryptoECDSA().CheckPubPrivKeyMatch( \
                                             self.binPrivKey32_Plain, \
                                             self.binPublicKey65))

      self.addrStr20 = self.binPublicKey65.getHash160()

      self.isInitialized = True
      return self

   def createFromPublicKey(self, pubkey):
      """
      Creates address from a user-supplied ECDSA public key.

      The key can be supplied as an (x,y) pair of integers, an EC_Point
      as defined in the lisecdsa class, or as a 65-byte binary string
      (the 64 public key bytes with a 0x04 prefix byte)

      This method will fail if the supplied pair of points is not
      on the secp256k1 curve.
      """
      if isinstance(pubkey, tuple) and len(pubkey)==2:
         # We are given public-key (x,y) pair
         binXBE = int_to_binary(pubkey[0], widthBytes=32, endOut=BIGENDIAN)
         binYBE = int_to_binary(pubkey[1], widthBytes=32, endOut=BIGENDIAN)
         self.binPublicKey65 = SecureBinaryData('\x04' + binXBE + binYBE)
         if not CryptoECDSA().VerifyPublicKeyValid(self.binPublicKey65):
            raise KeyDataError, 'Supplied public key is not on secp256k1 curve'
      elif isinstance(pubkey, str) and len(pubkey)==65:
         self.binPublicKey65 = SecureBinaryData(pubkey)
         if not CryptoECDSA().VerifyPublicKeyValid(self.binPublicKey65):
            raise KeyDataError, 'Supplied public key is not on secp256k1 curve'
      else:
         raise KeyDataError, 'Unknown public key format!'

      # TODO: I should do a test to see which is faster:
      #           1) Compute the hash directly like this
      #           2) Get the string, hash it in python
      self.addrStr20 = self.binPublicKey65.getHash160()
      self.isInitialized = True
      return self


   def createFromPublicKeyHash160(self, pubkeyHash160, netbyte=ADDRBYTE):
      """
      Creates an address from just the 20-byte binary hash of a public key.

      In binary form without a chksum, there is no protection against byte
      errors, since there's no way to distinguish an invalid address from
      a valid one (they both look like random data).

      If you are creating an address using 20 bytes you obtained in an
      unreliable manner (such as manually typing them in), you should
      double-check the input before sending money using the address created
      here -- the tx will appear valid and be accepted by the network,
      but will be permanently tied up in the network
      """
      self.__init__()
      self.addrStr20 = pubkeyHash160
      self.isInitialized = True
      return self

   def createFromAddrStr(self, addrStr):
      """
      Creates an address from a Base58 address string.  Since the address
      string includes a checksum, this method will fail if there was any
      errors entering/copying the address
      """
      self.__init__()
      self.addrStr = addrStr
      if not self.checkAddressValid():
         raise BadAddressError, 'Invalid address string: '+addrStr
      self.isInitialized = True
      return self

   def calculateAddrStr(self, netbyte=ADDRBYTE):
      """
      Forces a recalculation of the address string from the public key
      """
      if not self.hasPubKey():
         raise KeyDataError, 'Cannot compute address without PublicKey'
      keyHash = self.binPublicKey65.getHash160()
      chksum  = hash256(netbyte + keyHash)[:4]
      return  binary_to_base58(netbyte + keyHash + chksum)



   def checkAddressValid(self):
      return checkAddrStrValid(self.addrStr);


   def pprint(self, withPrivKey=True, indent=''):
      def pp(x, nchar=1000):
         if x.getSize()==0:
            return '--'*32
         else:
            return x.toHexStr()[:nchar]
      print indent + 'BTC Address      :', self.getAddrStr()
      print indent + 'Hash160[BE]      :', binary_to_hex(self.getAddr160())
      print indent + 'Wallet Location  :', self.walletByteLoc
      print indent + 'Chained Address  :', self.chainIndex >= -1
      print indent + 'Have (priv,pub)  : (%s,%s)' % \
                     (str(self.hasPrivKey()), str(self.hasPubKey()))
      print indent + 'First/Last Time  : (%s,%s)' % \
                     (str(self.timeRange[0]), str(self.timeRange[1]))
      print indent + 'First/Last Block : (%s,%s)' % \
                     (str(self.blkRange[0]), str(self.blkRange[1]))
      if self.hasPubKey():
         print indent + 'PubKeyX(BE)      :', \
                        binary_to_hex(self.binPublicKey65.toBinStr()[1:33 ])
         print indent + 'PubKeyY(BE)      :', \
                        binary_to_hex(self.binPublicKey65.toBinStr()[  33:])
      print indent + 'Encryption parameters:'
      print indent + '   UseEncryption :', self.useEncryption
      print indent + '   IsLocked      :', self.isLocked
      print indent + '   KeyChanged    :', self.keyChanged
      print indent + '   ChainIndex    :', self.chainIndex
      print indent + '   Chaincode     :', pp(self.chaincode)
      print indent + '   InitVector    :', pp(self.binInitVect16)
      if withPrivKey and self.hasPrivKey():
         print indent + 'PrivKeyPlain(BE) :', pp(self.binPrivKey32_Plain)
         print indent + 'PrivKeyCiphr(BE) :', pp(self.binPrivKey32_Encr)
      else:
         print indent + 'PrivKeyPlain(BE) :', pp(SecureBinaryData())
         print indent + 'PrivKeyCiphr(BE) :', pp(SecureBinaryData())
      if self.createPrivKeyNextUnlock:
         print indent + '           ***** :', 'PrivKeys available on next unlock'



################################################################################
# Identify all the codes/strings that are needed for dealing with scripts
################################################################################

# Start list of OP codes
OP_0 = 0
OP_FALSE = 0
OP_PUSHDATA1 = 76
OP_PUSHDATA2 = 77
OP_PUSHDATA4 = 78
OP_1NEGATE = 79
OP_1 = 81
OP_TRUE = 81
OP_2 = 82
OP_3 = 83
OP_4 = 84
OP_5 = 85
OP_6 = 86
OP_7 = 87
OP_8 = 88
OP_9 = 89
OP_10 = 90
OP_11 = 91
OP_12 = 92
OP_13 = 93
OP_14 = 94
OP_15 = 95
OP_16 = 96
OP_NOP = 97
OP_IF = 99
OP_NOTIF = 100
OP_ELSE = 103
OP_ENDIF = 104
OP_VERIFY = 105
OP_RETURN = 106
OP_TOALTSTACK = 107
OP_FROMALTSTACK = 108
OP_IFDUP = 115
OP_DEPTH = 116
OP_DROP = 117
OP_DUP = 118
OP_NIP = 119
OP_OVER = 120
OP_PICK = 121
OP_ROLL = 122
OP_ROT = 123
OP_SWAP = 124
OP_TUCK = 125
OP_2DROP = 109
OP_2DUP = 110
OP_3DUP = 111
OP_2OVER = 112
OP_2ROT = 113
OP_2SWAP = 114
OP_CAT = 126
OP_SUBSTR = 127
OP_LEFT = 128
OP_RIGHT = 129
OP_SIZE = 130
OP_INVERT = 131
OP_AND = 132
OP_OR = 133
OP_XOR = 134
OP_EQUAL = 135
OP_EQUALVERIFY = 136
OP_1ADD = 139
OP_1SUB = 140
OP_2MUL = 141
OP_2DIV = 142
OP_NEGATE = 143
OP_ABS = 144
OP_NOT = 145
OP_0NOTEQUAL = 146
OP_ADD = 147
OP_SUB = 148
OP_MUL = 149
OP_DIV = 150
OP_MOD = 151
OP_LSHIFT = 152
OP_RSHIFT = 153
OP_BOOLAND = 154
OP_BOOLOR = 155
OP_NUMEQUAL = 156
OP_NUMEQUALVERIFY = 157
OP_NUMNOTEQUAL = 158
OP_LESSTHAN = 159
OP_GREATERTHAN = 160
OP_LESSTHANOREQUAL = 161
OP_GREATERTHANOREQUAL = 162
OP_MIN = 163
OP_MAX = 164
OP_WITHIN = 165
OP_RIPEMD160 = 166
OP_SHA1 = 167
OP_SHA256 = 168
OP_HASH160 = 169
OP_HASH256 = 170
OP_CODESEPARATOR = 171
OP_CHECKSIG = 172
OP_CHECKSIGVERIFY = 173
OP_CHECKMULTISIG = 174
OP_CHECKMULTISIGVERIFY = 175

opnames = ['']*256
opnames[0] =   'OP_0'
for i in range(1,76):
   opnames[i] ='OP_PUSHDATA'
opnames[76] =	'OP_PUSHDATA1'
opnames[77] =	'OP_PUSHDATA2'
opnames[78] =	'OP_PUSHDATA4'
opnames[79] =	'OP_1NEGATE'
opnames[81] =  'OP_1'
opnames[81] =	'OP_TRUE'
for i in range(1,17):
   opnames[80+i] = 'OP_' + str(i)
opnames[97] =	'OP_NOP'
opnames[99] =	'OP_IF'
opnames[100] =	'OP_NOTIF'
opnames[103] = 'OP_ELSE'
opnames[104] = 'OP_ENDIF'
opnames[105] =	'OP_VERIFY'
opnames[106] = 'OP_RETURN'
opnames[107] =	'OP_TOALTSTACK'
opnames[108] =	'OP_FROMALTSTACK'
opnames[115] =	'OP_IFDUP'
opnames[116] =	'OP_DEPTH'
opnames[117] =	'OP_DROP'
opnames[118] =	'OP_DUP'
opnames[119] =	'OP_NIP'
opnames[120] =	'OP_OVER'
opnames[121] =	'OP_PICK'
opnames[122] =	'OP_ROLL'
opnames[123] =	'OP_ROT'
opnames[124] =	'OP_SWAP'
opnames[125] =	'OP_TUCK'
opnames[109] =	'OP_2DROP'
opnames[110] =	'OP_2DUP'
opnames[111] =	'OP_3DUP'
opnames[112] =	'OP_2OVER'
opnames[113] =	'OP_2ROT'
opnames[114] =	'OP_2SWAP'
opnames[126] =	'OP_CAT'
opnames[127] = 'OP_SUBSTR'
opnames[128] =	'OP_LEFT'
opnames[129] =	'OP_RIGHT'
opnames[130] =	'OP_SIZE'
opnames[131] =	'OP_INVERT'
opnames[132] =	'OP_AND'
opnames[133] =	'OP_OR'
opnames[134] = 'OP_XOR'
opnames[135] = 'OP_EQUAL'
opnames[136] =	'OP_EQUALVERIFY'
opnames[139] =	'OP_1ADD'
opnames[140] =	'OP_1SUB'
opnames[141] =	'OP_2MUL'
opnames[142] =	'OP_2DIV'
opnames[143] =	'OP_NEGATE'
opnames[144] =	'OP_ABS'
opnames[145] =	'OP_NOT'
opnames[146] =	'OP_0NOTEQUAL'
opnames[147] =	'OP_ADD'
opnames[148] =	'OP_SUB'
opnames[149] =	'OP_MUL'
opnames[150] =	'OP_DIV'
opnames[151] =	'OP_MOD'
opnames[152] =	'OP_LSHIFT'
opnames[153] =	'OP_RSHIFT'
opnames[154] =	'OP_BOOLAND'
opnames[155] =	'OP_BOOLOR'
opnames[156] =	'OP_NUMEQUAL'
opnames[157] =	'OP_NUMEQUALVERIFY'
opnames[158] =	'OP_NUMNOTEQUAL'
opnames[159] =	'OP_LESSTHAN'
opnames[160] =	'OP_GREATERTHAN'
opnames[161] =	'OP_LESSTHANOREQUAL'
opnames[162] = 'OP_GREATERTHANOREQUAL'
opnames[163] =	'OP_MIN'
opnames[164] =	'OP_MAX'
opnames[165] = 'OP_WITHIN'
opnames[166] =	'OP_RIPEMD160'
opnames[167] =	'OP_SHA1'
opnames[168] =	'OP_SHA256'
opnames[169] =	'OP_HASH160'
opnames[170] =	'OP_HASH256'
opnames[171] =	'OP_CODESEPARATOR'
opnames[172] =	'OP_CHECKSIG'
opnames[173] =	'OP_CHECKSIGVERIFY'
opnames[174] =	'OP_CHECKMULTISIG'
opnames[175] =	'OP_CHECKMULTISIGVERIFY'


opCodeLookup = {}
opCodeLookup['OP_FALSE'] = 0
opCodeLookup['OP_PUSHDATA1'] =	76
opCodeLookup['OP_PUSHDATA2'] =	77
opCodeLookup['OP_PUSHDATA4'] =	78
opCodeLookup['OP_1NEGATE'] =	79
opCodeLookup['OP_1'] =  81
for i in range(1,17):
   opCodeLookup['OP_'+str(i)] =  80+i
opCodeLookup['OP_TRUE'] =	81
opCodeLookup['OP_NOP'] =	97
opCodeLookup['OP_IF'] =	99
opCodeLookup['OP_NOTIF'] =	100
opCodeLookup['OP_ELSE'] = 103
opCodeLookup['OP_ENDIF'] = 104
opCodeLookup['OP_VERIFY'] =	105
opCodeLookup['OP_RETURN'] = 106
opCodeLookup['OP_TOALTSTACK'] =	107
opCodeLookup['OP_FROMALTSTACK'] =	108
opCodeLookup['OP_IFDUP'] =	115
opCodeLookup['OP_DEPTH'] =	116
opCodeLookup['OP_DROP'] =	117
opCodeLookup['OP_DUP'] =	118
opCodeLookup['OP_NIP'] =	119
opCodeLookup['OP_OVER'] =	120
opCodeLookup['OP_PICK'] =	121
opCodeLookup['OP_ROLL'] =	122
opCodeLookup['OP_ROT'] =	123
opCodeLookup['OP_SWAP'] =	124
opCodeLookup['OP_TUCK'] =	125
opCodeLookup['OP_2DROP'] =	109
opCodeLookup['OP_2DUP'] =	110
opCodeLookup['OP_3DUP'] =	111
opCodeLookup['OP_2OVER'] =	112
opCodeLookup['OP_2ROT'] =	113
opCodeLookup['OP_2SWAP'] =	114
opCodeLookup['OP_CAT'] =	126
opCodeLookup['OP_SUBSTR'] = 127
opCodeLookup['OP_LEFT'] =	128
opCodeLookup['OP_RIGHT'] =	129
opCodeLookup['OP_SIZE'] =	130
opCodeLookup['OP_INVERT'] =	131
opCodeLookup['OP_AND'] =	132
opCodeLookup['OP_OR'] =	133
opCodeLookup['OP_XOR'] = 134
opCodeLookup['OP_EQUAL'] = 135
opCodeLookup['OP_EQUALVERIFY'] =	136
opCodeLookup['OP_1ADD'] =	139
opCodeLookup['OP_1SUB'] =	140
opCodeLookup['OP_2MUL'] =	141
opCodeLookup['OP_2DIV'] =	142
opCodeLookup['OP_NEGATE'] =	143
opCodeLookup['OP_ABS'] =	144
opCodeLookup['OP_NOT'] =	145
opCodeLookup['OP_0NOTEQUAL'] =	146
opCodeLookup['OP_ADD'] =	147
opCodeLookup['OP_SUB'] =	148
opCodeLookup['OP_MUL'] =	149
opCodeLookup['OP_DIV'] =	150
opCodeLookup['OP_MOD'] =	151
opCodeLookup['OP_LSHIFT'] =	152
opCodeLookup['OP_RSHIFT'] =	153
opCodeLookup['OP_BOOLAND'] =	154
opCodeLookup['OP_BOOLOR'] =	155
opCodeLookup['OP_NUMEQUAL'] =	156
opCodeLookup['OP_NUMEQUALVERIFY'] =	157
opCodeLookup['OP_NUMNOTEQUAL'] =	158
opCodeLookup['OP_LESSTHAN'] =	159
opCodeLookup['OP_GREATERTHAN'] =	160
opCodeLookup['OP_LESSTHANOREQUAL'] =	161
opCodeLookup['OP_GREATERTHANOREQUAL'] = 162
opCodeLookup['OP_MIN'] =	163
opCodeLookup['OP_MAX'] =	164
opCodeLookup['OP_WITHIN'] = 165
opCodeLookup['OP_RIPEMD160'] =	166
opCodeLookup['OP_SHA1'] =	167
opCodeLookup['OP_SHA256'] =	168
opCodeLookup['OP_HASH160'] =	169
opCodeLookup['OP_HASH256'] =	170
opCodeLookup['OP_CODESEPARATOR'] =	171
opCodeLookup['OP_CHECKSIG'] =	172
opCodeLookup['OP_CHECKSIGVERIFY'] =	173
opCodeLookup['OP_CHECKMULTISIG'] =	174
opCodeLookup['OP_CHECKMULTISIGVERIFY'] =	175
#Word Opcode	Description
#OP_PUBKEYHASH = 253	Represents a public key hashed with OP_HASH160.
#OP_PUBKEY = 254	Represents a public key compatible with OP_CHECKSIG.
#OP_INVALIDOPCODE = 255	Matches any opcode that is not yet assigned.
#[edit] Reserved words
#Any opcode not assigned is also reserved. Using an unassigned opcode makes the transaction invalid.
#Word	Opcode	When used...
#OP_RESERVED = 80	Transaction is invalid
#OP_VER = 98	Transaction is invalid
#OP_VERIF = 101	Transaction is invalid
#OP_VERNOTIF = 102	Transaction is invalid
#OP_RESERVED1 = 137	Transaction is invalid
#OP_RESERVED2 = 138	Transaction is invalid
#OP_NOP1 = OP_NOP10	176-185	The word is ignored.


def getOpCode(name):
   return int_to_binary(opCodeLookup[name], widthBytes=1)


TXIN_SCRIPT_STANDARD = 0
TXIN_SCRIPT_COINBASE = 1
TXIN_SCRIPT_SPENDCB  = 2
TXIN_SCRIPT_UNSIGNED = 3
TXIN_SCRIPT_UNKNOWN  = 4

TXOUT_SCRIPT_STANDARD = 0
TXOUT_SCRIPT_COINBASE = 1
TXOUT_SCRIPT_MULTISIG = 2
TXOUT_SCRIPT_OP_EVAL  = 3
TXOUT_SCRIPT_UNKNOWN  = 4

MULTISIG_1of1     = (1,1)
MULTISIG_1of2     = (1,2)
MULTISIG_2oF2     = (2,2)
MULTISIG_1oF3     = (1,3)
MULTISIG_2oF3     = (2,3)
MULTISIG_3oF3     = (3,3)
MULTISIG_UNKNOWN  = (0,0)

TXOUT_TYPE_NAMES = { TXOUT_SCRIPT_STANDARD: 'Standard', \
                     TXOUT_SCRIPT_COINBASE: 'Coinbase', \
                     TXOUT_SCRIPT_MULTISIG: 'Multi-Signature', \
                     TXOUT_SCRIPT_UNKNOWN:  '<Unrecognized>', \
                     TXOUT_SCRIPT_OP_EVAL:  'OP-EVAL' }
TXIN_TYPE_NAMES = {  TXIN_SCRIPT_STANDARD:  'Standard', \
                     TXIN_SCRIPT_COINBASE:  'Coinbase', \
                     TXIN_SCRIPT_SPENDCB:   'Spend-CB', \
                     TXIN_SCRIPT_UNSIGNED:  'Unsigned', \
                     TXIN_SCRIPT_UNKNOWN:   '<Unrecognized>'}

################################################################################
def getTxOutMultiSigInfo(binScript):
   """
   Gets the Multi-Sig tx type, as well as all the address-160 strings of
   the keys that are needed to satisfy this transaction.  This currently
   only identifies M-of-N transaction types, returning unknown otherwise.

   However, the address list it returns should be valid regardless of
   whether the type was unknown:  we assume all 20-byte chunks of data
   are public key hashes, and 65-byte chunks are public keys.

   NOTE:  Because the address list is always valid, there is no reason
          not to use this method to extract addresses from ANY scripts,
          not just multi-sig...
   """
   addr160List = []
   pub65List   = []
   bup = BinaryUnpacker(binScript)
   opcodes = []
   while bup.getRemainingSize() > 0:
      nextByte = bup.get(UINT8)
      binChunk = ''
      if 0 < nextByte < 76:
         nBytes = nextByte
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA1:
         nBytes = scriptUnpacker.get(UINT8)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA2:
         nBytes = scriptUnpacker.get(UINT16)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      elif nextByte == OP_PUSHDATA4:
         nBytes = scriptUnpacker.get(UINT32)
         binChunk = bup.get(BINARY_CHUNK, nBytes)
      else:
         opcodes.append(nextByte)
         

      if len(binChunk) == 20:
         addr160List.append(binChunk)
         pub65List.append('')
         opcodes.append('<Addr20>')
      elif len(binChunk) == 65:
         addr160List.append(convertKeyDataToAddress(pubKey=binChunk))
         pub65List.append(binChunk)
         opcodes.append('<PubKey65>')


   mstype = MULTISIG_UNKNOWN
   #print 'Transaction:',
   #for op in opcodes:
      #print op,

   # First assume that this is an M-of-N script
   try:
      isCMS = opcodes[-1]==getOpCode('OP_CHECKMULTISIG')
      M = int(opcodes[ 0])
      N = int(opcodes[-2])
      keys  = opcodes[1:-2]
      nPub = sum([(1 if p=='PubKey65' else 0) for p in keys])
      if 0<M<3 and 0<N<=3 and N==nPub:
         # We have a legit M-of-N script, figure out which one
         if M==1 and N==1: return MULTISIG_1of1, addr160List, pub65List
         if M==1 and N==2: return MULTISIG_1of2, addr160List, pub65List
         if M==2 and N==2: return MULTISIG_2oF2, addr160List, pub65List
         if M==1 and N==3: return MULTISIG_1oF3, addr160List, pub65List
         if M==2 and N==3: return MULTISIG_2oF3, addr160List, pub65List
         if M==3 and N==3: return MULTISIG_3oF3, addr160List, pub65List
   except:
      pass

      
   # Next try A-or-(B-and-C) transaction (not implemented yet
   # I'm not sure how these transactions will look
   try:
      pass
   except:
      pass

   return MULTISIG_UNKNOWN, addr160List, pub65List


################################################################################
def getTxOutScriptType(binScript):
   if binScript[:2] == hex_to_binary('4104'):
      is65B = len(binScript) == 67
      lastByteMatch = binScript[-1] == getOpCode('OP_CHECKSIG')
      if (is65B and lastByteMatch):
         return TXOUT_SCRIPT_COINBASE
   else:
      is1 = binScript[ 0] == getOpCode('OP_DUP')
      is2 = binScript[ 1] == getOpCode('OP_HASH160')
      is3 = binScript[-2] == getOpCode('OP_EQUALVERIFY')
      is4 = binScript[-1] == getOpCode('OP_CHECKSIG')
      if (is1 and is2 and is3 and is4):
         return TXOUT_SCRIPT_STANDARD

   # If we got here, let's check if it's a standard Multi-sig type
   mstype = getTxOutMultiSigInfo(binScript)[0]
   if mstype!=MULTISIG_UNKNOWN:
      return TXOUT_SCRIPT_MULTISIG

   return TXOUT_SCRIPT_UNKNOWN

################################################################################
def TxOutScriptExtractAddrStr(binScript):
   return hash160_to_addrStr(TxOutScriptExtractAddr160(binScript))

################################################################################
def TxOutScriptExtractAddr160(binScript):
   txoutType = getTxOutScriptType(binScript)
   if txoutType == TXOUT_SCRIPT_UNKNOWN:
      return '<Non-standard TxOut script>'

   if txoutType == TXOUT_SCRIPT_COINBASE:
      return convertKeyDataToAddress(pubKey=binScript[1:66])
   elif txoutType == TXOUT_SCRIPT_STANDARD:
      return binScript[3:23]
   elif txoutType == TXOUT_SCRIPT_MULTISIG:
      # Returns a list of addresses
      return getTxOutMultiSigInfo(binScript)[1]


################################################################################
def getTxInScriptType(txinObj):
   """
   NOTE: this method takes a TXIN object, not just the script itself.  This
         is because this method needs to see the OutPoint to distinguish an
         UNKNOWN TxIn from a coinbase-TxIn
   """
   binScript = txinObj.binScript
   if len(binScript)==0:
      return TXIN_SCRIPT_UNSIGNED
   if txinObj.outpoint.txHash == EmptyHash:
      return TXIN_SCRIPT_COINBASE

   b0,b1,b2,b3,b4 = binScript[:5]
   if not (b1=='\x30' and b3=='\x02'):
      return TXIN_SCRIPT_UNKNOWN

   SigSize = binary_to_int(b2) + 3
   PubkeySize = 66  # 0x4104[Pubx][Puby]

   if len(binScript)==SigSize:
      return TXIN_SCRIPT_SPENDCB
   elif len(binScript)==(SigSize + PubkeySize + 1):
      return TXIN_SCRIPT_STANDARD

   return TXIN_SCRIPT_UNKNOWN


################################################################################
def TxInScriptExtractKeyAddr(txinObj):
   scrType = getTxInScriptType(txinObj)
   if scrType == TXIN_SCRIPT_STANDARD:
      pubKeyBin = txinObj.binScript[-65:]
      newAddr = PyBtcAddress().createFromPublicKey(pubKeyBin)
      return (newAddr.calculateAddrStr(), newAddr.binPublicKey65.toBinStr()) # LITTLE_ENDIAN
   elif scrType == TXIN_SCRIPT_COINBASE:
      return ('[COINBASE-NO-ADDR: %s]'%binary_to_hex(txinObj.binScript), '[COINBASE-NO-PUBKEY]')
      #return ('[COINBASE-NO-ADDR]', '[COINBASE-NO-PUBKEY]')
   elif scrType == TXIN_SCRIPT_SPENDCB:
      return ('[SPENDCOINBASE]', '[SPENDCOINBASE]')
   else:
      return ('[UNKNOWN-TXIN]', '[UNKNOWN-TXIN]')


################################################################################
def TxInScriptExtractAddr160IfAvail(txinObj):
   if getTxInScriptType(txinObj) == TXIN_SCRIPT_STANDARD:
      pubKeyBin = txinObj.binScript[-65:]
      return hash160(pubKeyBin)
   else:
      return ''



# Finally done with all the base conversion functions and ECDSA code
# Now define the classes for the objects that will use this


################################################################################
#  Transaction Classes
################################################################################

indent = ' '*3

#####
class PyOutPoint(object):
   #def __init__(self, txHash, txOutIndex):
      #self.txHash = txHash
      #self.txOutIndex     = outIndex

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         opData = toUnpack
      else:
         opData = BinaryUnpacker( toUnpack )

      if opData.getRemainingSize() < 36: raise UnserializeError
      self.txHash = opData.get(BINARY_CHUNK, 32)
      self.txOutIndex = opData.get(UINT32)
      return self

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.txHash)
      binOut.put(UINT32, self.txOutIndex)
      return binOut.getBinaryString()


   def copy(self):
      return PyOutPoint().unserialize(self.serialize())


   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'OutPoint:'
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.txHash, endian), \
                  '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'TxOutIndex:', self.txOutIndex


#####
class PyTxIn(object):
   def __init__(self):
      self.outpoint   = UNINITIALIZED
      self.binScript  = UNINITIALIZED
      self.intSeq     = 2**32-1
      self.isCoinbase = UNKNOWN

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txInData = toUnpack
      else:
         txInData = BinaryUnpacker( toUnpack )

      self.outpoint  = PyOutPoint().unserialize( txInData.get(BINARY_CHUNK, 36) )
      scriptSize     = txInData.get(VAR_INT)
      if txInData.getRemainingSize() < scriptSize+4: raise UnserializeError
      self.binScript = txInData.get(BINARY_CHUNK, scriptSize)
      self.intSeq    = txInData.get(UINT32)
      return self

   def getScript(self):
      return self.binScript

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.outpoint.serialize() )
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      binOut.put(UINT32, self.intSeq)
      return binOut.getBinaryString()

   def copy(self):
      return PyTxIn().unserialize(self.serialize())


   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'PyTxIn:'
      print indstr + indent + 'PrevTxHash:', \
                  binary_to_hex(self.outpoint.txHash, endian), \
                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'TxOutIndex:', self.outpoint.txOutIndex
      source = TxInScriptExtractKeyAddr(self)[0]
      print indstr + indent + 'Script:    ', \
                  '('+binary_to_hex(self.binScript)[:64]+')'
      inAddr160 = TxInScriptExtractAddr160IfAvail(self)
      if len(inAddr160)>0:
         print indstr + indent + 'Sender:    ', hash160_to_addrStr(inAddr160)
      print indstr + indent + 'Seq:       ', self.intSeq


#####
class PyTxOut(object):
   def __init__(self):
      self.value     = UNINITIALIZED
      self.binScript = UNINITIALIZED

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txOutData = toUnpack
      else:
         txOutData = BinaryUnpacker( toUnpack )

      self.value       = txOutData.get(UINT64)
      scriptSize       = txOutData.get(VAR_INT)
      if txOutData.getRemainingSize() < scriptSize: raise UnserializeError
      self.binScript = txOutData.get(BINARY_CHUNK, scriptSize)
      return self

   def getValue(self):
      return self.value

   def getScript(self):
      return self.binScript

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT64, self.value)
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      return binOut.getBinaryString()

   def copy(self):
      return PyTxOut().unserialize(self.serialize())

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'TxOut:'
      print indstr + indent + 'Value:   ', self.value, '(', float(self.value) / ONE_BTC, ')'
      txoutType = getTxOutScriptType(self.binScript)
      if txoutType == TXOUT_SCRIPT_COINBASE:
         print indstr + indent + 'Script:   PubKey(%s) OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript),)
      elif txoutType == TXOUT_SCRIPT_STANDARD:
         print indstr + indent + 'Script:   OP_DUP OP_HASH (%s) OP_EQUAL OP_CHECKSIG' % \
                              (TxOutScriptExtractAddrStr(self.binScript),)
      else:
         print indstr + indent + 'Script:   <Non-standard script!>'

#####
class PyTx(object):
   def __init__(self):
      self.version    = UNINITIALIZED
      self.inputs     = UNINITIALIZED
      self.outputs    = UNINITIALIZED
      self.lockTime   = 0
      self.thisHash   = UNINITIALIZED
      self.isSigned   = False

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT32, self.version)
      binOut.put(VAR_INT, len(self.inputs))
      for txin in self.inputs:
         binOut.put(BINARY_CHUNK, txin.serialize())
      binOut.put(VAR_INT, len(self.outputs))
      for txout in self.outputs:
         binOut.put(BINARY_CHUNK, txout.serialize())
      binOut.put(UINT32, self.lockTime)
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txData = toUnpack
      else:
         txData = BinaryUnpacker( toUnpack )

      startPos = txData.getPosition()
      self.inputs     = []
      self.outputs    = []
      self.version    = txData.get(UINT32)
      numInputs  = txData.get(VAR_INT)
      for i in xrange(numInputs):
         self.inputs.append( PyTxIn().unserialize(txData) )
      numOutputs = txData.get(VAR_INT)
      for i in xrange(numOutputs):
         self.outputs.append( PyTxOut().unserialize(txData) )
      self.lockTime   = txData.get(UINT32)
      endPos = txData.getPosition()
      self.nBytes = endPos - startPos
      self.thisHash = hash256(self.serialize())
      return self

   def copy(self):
      return PyTx().unserialize(self.serialize())

   def getHash(self):
      return hash256(self.serialize())

   def getHashHex(self, endianness=LITTLEENDIAN):
      return binary_to_hex(self.getHash(), endOut=endianness)


   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'Transaction:'
      print indstr + indent + 'TxHash:   ', self.getHashHex(endian), \
                                    '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'Version:  ', self.version
      print indstr + indent + 'nInputs:  ', len(self.inputs)
      print indstr + indent + 'nOutputs: ', len(self.outputs)
      print indstr + indent + 'LockTime: ', self.lockTime
      print indstr + indent + 'Inputs: '
      for inp in self.inputs:
         inp.pprint(nIndent+2, endian=endian)
      print indstr + indent + 'Outputs: '
      for out in self.outputs:
         out.pprint(nIndent+2, endian=endian)



   #def pprintShort(self, nIndent=0, endian=BIGENDIAN):
      #print '\nTransaction: %s' % self.getHashHex()


   def pprintHex(self, nIndent=0):
      bu = BinaryUnpacker(self.serialize())
      theSer = self.serialize()
      print binary_to_hex(bu.get(BINARY_CHUNK, 4))
      nTxin = bu.get(VAR_INT)
      print 'VAR_INT(%d)' % nTxin
      for i in range(nTxin):
         print binary_to_hex(bu.get(BINARY_CHUNK,32))
         print binary_to_hex(bu.get(BINARY_CHUNK,4))
         scriptSz = bu.get(VAR_INT)
         print 'VAR_IN(%d)' % scriptSz
         print binary_to_hex(bu.get(BINARY_CHUNK,scriptSz))
         print binary_to_hex(bu.get(BINARY_CHUNK,4))
      nTxout = bu.get(VAR_INT)
      print 'VAR_INT(%d)' % nTxout
      for i in range(nTxout):
         print binary_to_hex(bu.get(BINARY_CHUNK,8))
         scriptSz = bu.get(VAR_INT)
         print binary_to_hex(bu.get(BINARY_CHUNK,scriptSz))
      print binary_to_hex(bu.get(BINARY_CHUNK, 4))




################################################################################
#  Block Information
################################################################################


class PyBlockHeader(object):
   def __init__(self):
      self.version      = 1
      self.prevBlkHash  = ''
      self.merkleRoot   = UNINITIALIZED
      self.timestamp    = UNINITIALIZED
      self.diffBits     = UNINITIALIZED
      self.nonce        = UNINITIALIZED
      # Use these fields for storage of block information, but are not otherwise
      # part of the serialized data structure
      self.theHash      = ''
      self.numTx        = UNINITIALIZED
      self.blkHeight    = UNINITIALIZED
      self.fileByteLoc  = UNINITIALIZED
      self.nextBlkHash  = UNINITIALIZED
      self.intDifficult = UNINITIALIZED
      self.sumDifficult = UNINITIALIZED
      self.isMainChain  = False
      self.isOrphan     = True

   def serialize(self):
      if self.version == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
      binOut = BinaryPacker()
      binOut.put(UINT32, self.version)
      binOut.put(BINARY_CHUNK, self.prevBlkHash)
      binOut.put(BINARY_CHUNK, self.merkleRoot)
      binOut.put(UINT32, self.timestamp)
      binOut.put(BINARY_CHUNK, self.diffBits)
      binOut.put(UINT32, self.nonce)
      return binOut.getBinaryString()


   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack
      else:
         blkData = BinaryUnpacker( toUnpack )

      self.version     = blkData.get(UINT32)
      self.prevBlkHash = blkData.get(BINARY_CHUNK, 32)
      self.merkleRoot  = blkData.get(BINARY_CHUNK, 32)
      self.timestamp   = blkData.get(UINT32)
      self.diffBits    = blkData.get(BINARY_CHUNK, 4)
      self.nonce       = blkData.get(UINT32)
      self.theHash     = hash256(self.serialize())
      return self

   def copy(self):
      return PyBlockHeader().unserialize(self.serialize())

   def getHash(self, endian=LITTLEENDIAN):
      if self.version == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
      if len(self.theHash) < 32:
         self.theHash = hash256(self.serialize())
      outHash = self.theHash
      if endian==BIGENDIAN:
         outHash = binary_switchEndian(outHash)
      return outHash

   def getHashHex(self, endian=LITTLEENDIAN):
      if self.version == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
      if len(self.theHash) < 32:
         self.theHash = hash256(self.serialize())
      return binary_to_hex(self.theHash, endian)

   def getDifficulty(self):
      if self.diffBits == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockHeader object not initialized!'
      self.intDifficult = binaryBits_to_difficulty(self.diffBits)
      return self.intDifficult

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'BlockHeader:'
      print indstr + indent + 'Version:   ', self.version
      print indstr + indent + 'ThisHash:  ', binary_to_hex( self.theHash, endOut=endian), \
                                                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'PrevBlock: ', binary_to_hex(self.prevBlkHash, endOut=endian), \
                                                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'MerkRoot:  ', binary_to_hex(self.merkleRoot, endOut=endian), \
                                                      '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'Timestamp: ', self.timestamp
      fltDiff = binaryBits_to_difficulty(self.diffBits)
      print indstr + indent + 'Difficulty:', fltDiff, '('+binary_to_hex(self.diffBits)+')'
      print indstr + indent + 'Nonce:     ', self.nonce
      if not self.blkHeight==UNINITIALIZED:
         print indstr + indent + 'BlkHeight: ', self.blkHeight
      if not self.blkHeight==UNINITIALIZED:
         print indstr + indent + 'BlkFileLoc:', self.fileByteLoc
      if not self.nextBlkHash==UNINITIALIZED:
         #print indstr + indent + 'NextBlock: ', binary_to_hex(self.nextBlkHash)
         print indstr + indent + 'NextBlock: ', self.nextBlkHash
      if not self.numTx==UNINITIALIZED:
         print indstr + indent + 'NumTx:     ', self.numTx
      if not self.intDifficult==UNINITIALIZED:
         print indstr + indent + 'Difficulty:', self.intDifficult
      if not self.sumDifficult==UNINITIALIZED:
         print indstr + indent + 'DiffSum:   ', self.sumDifficult


################################################################################
################################################################################
class PyBlockData(object):
   def __init__(self, txList=[]):
      self.txList     = txList
      self.numTx      = len(txList)
      self.merkleTree = []
      self.merkleRoot = UNINITIALIZED


   def serialize(self):
      if self.numTx == UNINITIALIZED:
         raise UnitializedBlockDataError, 'PyBlockData object not initialized!'
      binOut = BinaryPacker()
      binOut.put(VAR_INT, self.numTx)
      for tx in self.txList:
         binOut.put(BINARY_CHUNK, tx.serialize())
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack
      else:
         blkData = BinaryUnpacker( toUnpack )

      self.txList = []
      self.numTx  = blkData.get(VAR_INT)
      for i in xrange(self.numTx):
         self.txList.append( PyTx().unserialize(blkData) )
      self.merkleTree = []
      self.merkleRoot = ''
      return self


   def getTxHashList(self):
      if( self.numTx == UNINITIALIZED ):
         self.getMerkleRoot()
      return self.merkleTree[:self.numTx]


   def getMerkleRoot(self):
      assert( not self.numTx == UNINITIALIZED )
      if len(self.merkleTree)==0 and not self.numTx==0:
         #Create the merkle tree
         self.merkleTree = [hash256(tx.serialize()) for tx in self.txList]
         sz = len(self.merkleTree)
         while sz > 1:
            hashes = self.merkleTree[-sz:]
            mod2 = sz%2
            for i in range(sz/2):
               self.merkleTree.append( hash256(hashes[2*i] + hashes[2*i+1]) )
            if mod2==1:
               self.merkleTree.append( hash256(hashes[-1] + hashes[-1]) )
            sz = (sz+1) / 2
      self.merkleRoot = self.merkleTree[-1]
      return self.merkleRoot

   def printMerkleTree(self, reverseHash=False, indent=''):
      print indent + 'Printing Merkle Tree:'
      if reverseHash:
         print indent + '(hashes will be reversed, like shown on BlockExplorer.com)'
      root = self.getMerkleRoot()
      print indent + 'Merkle Root:', binary_to_hex(root)
      for h in self.merkleTree:
         phash = binary_to_hex(h) if not reverseHash else binary_to_hex(h, endOut=BIGENDIAN)
         print indent + '\t' + phash


   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'BlockData:'
      print indstr + indent + 'MerkleRoot:  ', binary_to_hex(self.getMerkleRoot(), endian), \
                                               '(BE)' if endian==BIGENDIAN else '(LE)'
      print indstr + indent + 'NumTx:       ', self.numTx
      for tx in self.txList:
         tx.pprint(nIndent+1, endian=endian)


################################################################################
################################################################################
class PyBlock(object):
   def __init__(self, prevHeader=None, txlist=[]):
      self.blockHeader = PyBlockHeader()
      self.blockData   = PyBlockData()
      if prevHeader:
         self.setPrevHeader(prevHeader)
      if txlist:
         self.setTxList(txlist)

   def serialize(self):
      assert( not self.blockHeader == UNINITIALIZED )
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.blockHeader.serialize())
      binOut.put(BINARY_CHUNK, self.blockData.serialize())
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack
      else:
         blkData = BinaryUnpacker( toUnpack )

      self.txList = []
      self.blockHeader = PyBlockHeader().unserialize(blkData)
      self.blockData   = PyBlockData().unserialize(blkData)
      return self

   def getNumTx(self):
      return len(self.blockData.txList)

   def getSize(self):
      return len(self.serialize())

   # Not sure how useful these manual block-construction methods
   # are.  For now, I just need something with non-ridiculous vals
   def setPrevHeader(self, prevHeader, copyAttr=True):
      self.blockHeader.prevBlkHash = prevHeader.theHash
      self.blockHeader.nonce       = 0
      if copyAttr:
         self.blockHeader.version     = prevHeader.version
         self.blockHeader.timestamp   = prevHeader.timestamp+600
         self.blockHeader.diffBits    = prevHeader.diffBits

   def setTxList(self, txlist):
      self.blockData = PyBlockData(txlist)
      if not self.blockHeader == UNINITIALIZED:
         self.blockHeader.merkleRoot = self.blockData.getMerkleRoot()

   def tx(self, idx):
      return self.blockData.txList[idx]

   def pprint(self, nIndent=0, endian=BIGENDIAN):
      indstr = indent*nIndent
      print indstr + 'Block:'
      self.blockHeader.pprint(nIndent+1, endian=endian)
      self.blockData.pprint(nIndent+1, endian=endian)






################################################################################
#
# SCRIPTING!
#
################################################################################


def convertScriptToOpStrings(binScript):
   opList = []

   i = 0;
   sz = len(binScript)
   error = False;
   while i < sz:
      nextOp = ord(binScript[i]);
      if nextOp == 0:
         opList.append("0")
         i+=1
      elif nextOp < 76:
         opList.append("[PUSHDATA -- " + str(nextOp) + " BYTES:]")
         binObj = binScript[i+1:i+1+nextOp]
         opList.append(binary_to_hex(binObj))
         i += nextOp+1
      elif nextOp == 76:
         nb = binary_to_int(binScript[i+1:i+2])
         if i+1+1+nb > sz:
            error = True;
            break
         binObj = binScript[i+2:i+2+nb]
         opList.append("[OP_PUSHDATA1 -- " + str(nb) + " BYTES:]");
         opList.append(binary_to_hex(binObj))
         i += nb+2
      elif nextOp == 77:
         nb = binScript[i+1:i+3];
         if i+1+2+nb > sz:
            error = True;
            break
         nbprint = min(nb,256)
         binObj = binScript[i+3,i+3+nbprint]
         opList.append("[OP_PUSHDATA2 -- " + str(nb) + " BYTES:]");
         opList.append(binary_to_hex(binObj) + '...')
         i += nb+3
      elif nextOp == 78:
         nb = binScript[i+1:i+5];
         if i+1+4+nb > sz:
            error = True;
            break
         nbprint = min(nb,256)
         binObj = binScript[i+5,i+5+nbprint]
         opList.append("[OP_PUSHDATA4 -- " + str(nb) + " BYTES:]");
         opList.append(binary_to_hex(binObj) + '...')
         i += nb+5
      else:
         opList.append(opnames[nextOp]);
         i += 1

   if error:
      opList.append("ERROR PROCESSING SCRIPT");

   return opList;


def pprintScript(binScript, nIndent=0):
   indstr = indent*nIndent
   print indstr + 'Script:'
   opList = convertScriptToOpStrings(binScript)
   for op in opList:
      print indstr + indent + op



TX_INVALID = 0
OP_NOT_IMPLEMENTED = 1
OP_DISABLED = 2
SCRIPT_STACK_SIZE_ERROR = 3
SCRIPT_ERROR = 4
SCRIPT_NO_ERROR = 5


class PyScriptProcessor(object):
   """
   Use this class to evaluate a script.  This method is more complicated
   than some might expect, due to the fact that any OP_CHECKSIG or
   OP_CHECKMULTISIG code requires the full transaction of the TxIn script
   and also needs the TxOut script being spent.  Since nearly every useful
   script will have one of these operations, this class/method assumes
   that all that data will be supplied.

   To simply execute a script not requiring any crypto operations:

      scriptIsValid = PyScriptProcessor().executeScript(binScript)
   """

   def __init__(self, txOldData=None, txNew=None, txInIndex=None):
      self.stack   = []
      self.txNew   = None
      self.script1 = None
      self.script2 = None
      if txOldData and txNew and not txInIndex==None:
         self.setTxObjects(txOldData, txNew, txInIndex)


   def setTxObjects(self, txOldData, txNew, txInIndex):
      """
      The minimal amount of data necessary to evaluate a script that
      has an signature check is the TxOut script that is being spent
      and the entire Tx of the TxIn that is spending it.  Thus, we
      must supply at least the txOldScript, and a txNew with its
      TxIn index (so we know which TxIn is spending that TxOut).
      It is acceptable to pass in the full TxOut or the tx of the
      TxOut instead of just the script itself.
      """
      self.txNew = PyTx().unserialize(txNew.serialize())
      self.script1 = str(txNew.inputs[txInIndex].binScript) # copy
      self.txInIndex  = txInIndex
      self.txOutIndex = txNew.inputs[txInIndex].outpoint.txOutIndex
      self.txHash  = txNew.inputs[txInIndex].outpoint.txHash

      if isinstance(txOldData, PyTx):
         if not self.txHash == hash256(txOldData.serialize()):
            LOGERROR('*** Supplied incorrect pair of transactions!')
         self.script2 = str(txOldData.outputs[self.txOutIndex].binScript)
      elif isinstance(txOldData, PyTxOut):
         self.script2 = str(txOldData.binScript)
      elif isinstance(txOldData, str):
         self.script2 = str(txOldData)



   def verifyTransactionValid(self, txOldData=None, txNew=None, txInIndex=-1):
      if txOldData and txNew and txInIndex != -1:
         self.setTxObjects(txOldData, txNew, txInIndex)
      else:
         txOldData = self.script2
         txNew = self.txNew
         txInIndex = self.txInIndex

      if self.script1==None or self.txNew==None:
         raise VerifyScriptError, 'Cannot verify transactions, without setTxObjects call first!'

      # Execute TxIn script first
      self.stack = []
      exitCode1 = self.executeScript(self.script1, self.stack)

      if not exitCode1 == SCRIPT_NO_ERROR:
         raise VerifyScriptError, ('First script failed!  Exit Code: ' + str(exitCode1))

      exitCode2 = self.executeScript(self.script2, self.stack)

      if not exitCode2 == SCRIPT_NO_ERROR:
         raise VerifyScriptError, ('Second script failed!  Exit Code: ' + str(exitCode2))

      return self.stack[-1]==1


   def executeScript(self, binaryScript, stack=[]):
      self.stack = stack
      self.stackAlt  = []
      scriptData = BinaryUnpacker(binaryScript)
      self.lastOpCodeSepPos = None

      while scriptData.getRemainingSize() > 0:
         opcode = scriptData.get(UINT8)
         exitCode = self.executeOpCode(opcode, scriptData, self.stack, self.stackAlt)
         if not exitCode == SCRIPT_NO_ERROR:
            if exitCode==OP_NOT_IMPLEMENTED:
               LOGERROR('***ERROR: OpCodes OP_IF, OP_NOTIF, OP_ELSE, OP_ENDIF,')
               LOGERROR('          have not been implemented, yet.  This script')
               LOGERROR('          could not be evaluated.')
            if exitCode==OP_DISABLED:
               LOGERROR('***ERROR: This script included an op code that has been')
               LOGERROR('          disabled for security reasons.  Script eval')
               LOGERROR('          failed.')
            return exitCode

      return SCRIPT_NO_ERROR


   # Implementing this method exactly as in the client because it looks like
   # there could be some subtleties with how it determines "true"
   def castToBool(self, binData):
      if isinstance(binData, int):
         binData = int_to_binary(binData)

      for i,byte in enumerate(binData):
         if not ord(byte) == 0:
            # This looks like it's assuming LE encoding (?)
            if (i == len(binData)-1) and (byte==0x80):
               return False
            return True
      return False


   def checkSig(self,binSig, binPubKey, txOutScript, txInTx, txInIndex, lastOpCodeSep=None):
      """
      Generic method for checking Bitcoin tx signatures.  This needs to be used for both
      OP_CHECKSIG and OP_CHECKMULTISIG.  Step 1 is to pop signature and public key off
      the stack, which must be done outside this method and passed in through the argument
      list.  The remaining steps do not require access to the stack.
      """

      # 2. Subscript is from latest OP_CODESEPARATOR until end... if DNE, use whole script
      subscript = txOutScript
      if lastOpCodeSep:
         subscript = subscript[lastOpCodeSep:]

      # 3. Signature is deleted from subscript
      #    I'm not sure why this line is necessary - maybe for non-standard scripts?
      lengthInBinary = int_to_binary(len(binSig))
      subscript = subscript.replace( lengthInBinary + binSig, "")

      # 4. Hashtype is popped and stored
      hashtype = binary_to_int(binSig[-1])
      justSig = binSig[:-1]

      if not hashtype == 1:
         LOGERROR('Non-unity hashtypes not implemented yet! (hashtype = %d)', hashtype)
         assert(False)

      # 5. Make a copy of the transaction -- we will be hashing a modified version
      txCopy = PyTx().unserialize( txInTx.serialize() )

      # 6. Remove all OP_CODESEPARATORs
      subscript.replace( int_to_binary(OP_CODESEPARATOR), '')

      # 7. All the TxIn scripts in the copy are blanked (set to empty string)
      for txin in txCopy.inputs:
         txin.binScript = ''

      # 8. Script for the current input in the copy is set to subscript
      txCopy.inputs[txInIndex].binScript = subscript

      # 9. Prepare the signature and public key
      senderAddr = PyBtcAddress().createFromPublicKey(binPubKey)
      binHashCode = int_to_binary(hashtype, widthBytes=4)
      toHash = txCopy.serialize() + binHashCode

      # Hashes are computed as part of CppBlockUtils::CryptoECDSA methods
      ##hashToVerify = hash256(toHash)
      ##hashToVerify = binary_switchEndian(hashToVerify)

      # 10. Apply ECDSA signature verification
      if senderAddr.verifyDERSignature(toHash, justSig):
         return True
      else:
         return False




   def executeOpCode(self, opcode, scriptUnpacker, stack, stackAlt):
      """
      Executes the next OP_CODE given the current state of the stack(s)
      """

      # TODO: Gavin clarified the effects of OP_0, and OP_1-OP_16.
      #       OP_0 puts an empty string onto the stack, which evaluateses to
      #            false and is plugged into HASH160 as ''
      #       OP_X puts a single byte onto the stack, 0x01 to 0x10
      #
      #       I haven't implemented it this way yet, because I'm still missing
      #       some details.  Since this "works" for available scripts, I'm going
      #       to leave it alone for now.

      ##########################################################################
      ##########################################################################
      ### This block produces very nice debugging output for script eval!
      #def pr(s):
         #if isinstance(s,int):
            #return str(s)
         #elif isinstance(s,str):
            #if len(s)>8:
               #return binary_to_hex(s)[:8]
            #else:
               #return binary_to_hex(s)

      #print '  '.join([pr(i) for i in stack])
      #print opnames[opcode][:12].ljust(12,' ') + ':',
      ##########################################################################
      ##########################################################################


      stackSizeAtLeast = lambda n: (len(self.stack) >= n)

      if   opcode == OP_FALSE:
         stack.append(0)
      elif 0 < opcode < 76:
         stack.append(scriptUnpacker.get(BINARY_CHUNK, opcode))
      elif opcode == OP_PUSHDATA1:
         nBytes = scriptUnpacker.get(UINT8)
         stack.append(scriptUnpacker.get(BINARY_CHUNK, nBytes))
      elif opcode == OP_PUSHDATA2:
         nBytes = scriptUnpacker.get(UINT16)
         stack.append(scriptUnpacker.get(BINARY_CHUNK, nBytes))
      elif opcode == OP_PUSHDATA4:
         nBytes = scriptUnpacker.get(UINT32)
         stack.append(scriptUnpacker.get(BINARY_CHUNK, nBytes))
      elif opcode == OP_1NEGATE:
         stack.append(-1)
      elif opcode == OP_TRUE:
         stack.append(1)
      elif 81 < opcode < 97:
         stack.append(opcode-80)
      elif opcode == OP_NOP:
         pass

      # TODO: figure out the conditional op codes...
      elif opcode == OP_IF:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_NOTIF:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_ELSE:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_ENDIF:
         return OP_NOT_IMPLEMENTED

      elif opcode == OP_VERIFY:
         if not self.castToBool(stack.pop()):
            stack.append(0)
            return TX_INVALID
      elif opcode == OP_RETURN:
         return TX_INVALID
      elif opcode == OP_TOALTSTACK:
         stackAlt.append( stack.pop() )
      elif opcode == OP_FROMALTSTACK:
         stack.append( stackAlt.pop() )

      elif opcode == OP_IFDUP:
         # Looks like this method duplicates the top item if it's not zero
         if not stackSizeAtLeast(1): return SCRIPT_STACK_SIZE_ERROR
         if self.castToBool(stack[-1]):
            stack.append(stack[-1]);

      elif opcode == OP_DEPTH:
         stack.append( len(stack) )
      elif opcode == OP_DROP:
         stack.pop()
      elif opcode == OP_DUP:
         stack.append( stack[-1] )
      elif opcode == OP_NIP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         del stack[-2]
      elif opcode == OP_OVER:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         stack.append(stack[-2])
      elif opcode == OP_PICK:
         n = stack.pop()
         if not stackSizeAtLeast(n): return SCRIPT_STACK_SIZE_ERROR
         stack.append(stack[-n])
      elif opcode == OP_ROLL:
         n = stack.pop()
         if not stackSizeAtLeast(n): return SCRIPT_STACK_SIZE_ERROR
         stack.append(stack[-(n+1)])
         del stack[-(n+2)]
      elif opcode == OP_ROT:
         if not stackSizeAtLeast(3): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-3] )
         del stack[-4]
      elif opcode == OP_SWAP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         x2 = stack.pop()
         x1 = stack.pop()
         stack.extend([x2, x1])
      elif opcode == OP_TUCK:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         x2 = stack.pop()
         x1 = stack.pop()
         stack.extend([x2, x1, x2])
      elif opcode == OP_2DROP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         stack.pop()
         stack.pop()
      elif opcode == OP_2DUP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-2] )
         stack.append( stack[-2] )
      elif opcode == OP_3DUP:
         if not stackSizeAtLeast(3): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-3] )
         stack.append( stack[-3] )
         stack.append( stack[-3] )
      elif opcode == OP_2OVER:
         if not stackSizeAtLeast(4): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-4] )
         stack.append( stack[-4] )
      elif opcode == OP_2ROT:
         if not stackSizeAtLeast(6): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-6] )
         stack.append( stack[-6] )
      elif opcode == OP_2SWAP:
         if not stackSizeAtLeast(4): return SCRIPT_STACK_SIZE_ERROR
         x4 = stack.pop()
         x3 = stack.pop()
         x2 = stack.pop()
         x1 = stack.pop()
         stack.extend( [x3, x4, x1, x2] )
      elif opcode == OP_CAT:
         return OP_DISABLED
      elif opcode == OP_SUBSTR:
         return OP_DISABLED
      elif opcode == OP_LEFT:
         return OP_DISABLED
      elif opcode == OP_RIGHT:
         return OP_DISABLED
      elif opcode == OP_SIZE:
         if isinstance(stack[-1], int):
            stack.append(0)
         else:
            stack.append( len(stack[-1]) )
      elif opcode == OP_INVERT:
         return OP_DISABLED
      elif opcode == OP_AND:
         return OP_DISABLED
      elif opcode == OP_OR:
         return OP_DISABLED
      elif opcode == OP_XOR:
         return OP_DISABLED
      elif opcode == OP_EQUAL:
         x1 = stack.pop()
         x2 = stack.pop()
         stack.append( 1 if x1==x2 else 0  )
      elif opcode == OP_EQUALVERIFY:
         x1 = stack.pop()
         x2 = stack.pop()
         if not x1==x2:
            stack.append(0)
            return TX_INVALID


      elif opcode == OP_1ADD:
         stack[-1] += 1
      elif opcode == OP_1SUB:
         stack[-1] -= 1
      elif opcode == OP_2MUL:
         stack[-1] *= 2
         return OP_DISABLED
      elif opcode == OP_2DIV:
         stack[-1] /= 2
         return OP_DISABLED
      elif opcode == OP_NEGATE:
         stack[-1] *= -1
      elif opcode == OP_ABS:
         stack[-1] = abs(stack[-1])
      elif opcode == OP_NOT:
         top = stack.pop()
         if top==0:
            stack.append(1)
         else:
            stack.append(0)
      elif opcode == OP_0NOTEQUAL:
         top = stack.pop()
         if top==0:
            stack.append(0)
         else:
            stack.append(1)
         top = stack.pop()
         if top==0:
            stack.append(1)
         else:
            stack.append(0)
      elif opcode == OP_ADD:
         b = stack.pop()
         a = stack.pop()
         stack.append(a+b)
      elif opcode == OP_SUB:
         b = stack.pop()
         a = stack.pop()
         stack.append(a-b)
      elif opcode == OP_MUL:
         return OP_DISABLED
      elif opcode == OP_DIV:
         return OP_DISABLED
      elif opcode == OP_MOD:
         return OP_DISABLED
      elif opcode == OP_LSHIFT:
         return OP_DISABLED
      elif opcode == OP_RSHIFT:
         return OP_DISABLED
      elif opcode == OP_BOOLAND:
         b = stack.pop()
         a = stack.pop()
         if (not a==0) and (not b==0):
            stack.append(1)
         else:
            stack.append(0)
      elif opcode == OP_BOOLOR:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if (self.castToBool(a) or self.castToBool(b)) else 0 )
      elif opcode == OP_NUMEQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a==b else 0 )
      elif opcode == OP_NUMEQUALVERIFY:
         b = stack.pop()
         a = stack.pop()
         if not a==b:
            stack.append(0)
            return TX_INVALID
      elif opcode == OP_NUMNOTEQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if not a==b else 0 )
      elif opcode == OP_LESSTHAN:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a<b else 0)
      elif opcode == OP_GREATERTHAN:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a>b else 0)
      elif opcode == OP_LESSTHANOREQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a<=b else 0)
      elif opcode == OP_GREATERTHANOREQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a>=b else 0)
      elif opcode == OP_MIN:
         b = stack.pop()
         a = stack.pop()
         stack.append( min(a,b) )
      elif opcode == OP_MAX:
         b = stack.pop()
         a = stack.pop()
         stack.append( max(a,b) )
      elif opcode == OP_WITHIN:
         xmax = stack.pop()
         xmin = stack.pop()
         x    = stack.pop()
         stack.append( 1 if (xmin <= x < xmax) else 0 )

      elif opcode == OP_RIPEMD160:
         bits = stack.pop()
         stack.append( ripemd160(bits) )
      elif opcode == OP_SHA1:
         bits = stack.pop()
         stack.append( sha1(bits) )
      elif opcode == OP_SHA256:
         bits = stack.pop()
         stack.append( sha256(bits) )
      elif opcode == OP_HASH160:
         bits = stack.pop()
         if isinstance(bits, int):
            bits = ''
         stack.append( hash160(bits) )
      elif opcode == OP_HASH256:
         bits = stack.pop()
         if isinstance(bits, int):
            bits = ''
         stack.append( sha256(sha256(bits) ) )
      elif opcode == OP_CODESEPARATOR:
         self.lastOpCodeSepPos = scriptUnpacker.getPosition()
      elif opcode == OP_CHECKSIG or opcode == OP_CHECKSIGVERIFY:

         # 1. Pop key and sig from the stack
         binPubKey = stack.pop()
         binSig    = stack.pop()

         # 2-10. encapsulated in sep method so CheckMultiSig can use it too
         txIsValid = self.checkSig(  binSig, \
                                     binPubKey, \
                                     scriptUnpacker.getBinaryString(), \
                                     self.txNew, \
                                     self.txInIndex, \
                                     self.lastOpCodeSepPos)
         stack.append(1 if txIsValid else 0)
         if opcode==OP_CHECKSIGVERIFY:
            verifyCode = self.executeOpCode(OP_VERIFY)
            if verifyCode == TX_INVALID:
               return TX_INVALID

      elif opcode == OP_CHECKMULTISIG or opcode == OP_CHECKMULTISIGVERIFY:
         # OP_CHECKMULTISIG procedure ported directly from Satoshi client code
         # Location:  bitcoin-0.4.0-linux/src/src/script.cpp:775
         i=1
         if len(stack) < i:
            return TX_INVALID

         nKeys = int(stack[-i])
         if nKeys < 0 or nKeys > 20:
            return TX_INVALID

         i += 1
         iKey = i
         i += nKeys
         if len(stack) < i:
            return TX_INVALID

         nSigs = int(stack[-i])
         if nSigs < 0 or nSigs > nKeys:
            return TX_INVALID

         iSig = i
         i += 1
         i += nSigs
         if len(stack) < i:
            return TX_INVALID

         stack.pop()

         # Apply the ECDSA verification to each of the supplied Sig-Key-pairs
         enoughSigsMatch = True
         while enoughSigsMatch and nSigs > 0:
            binSig = stack[-iSig]
            binKey = stack[-iKey]

            if( self.checkSig(binSig, \
                              binKey, \
                              scriptUnpacker.getBinaryString(), \
                              self.txNew, \
                              self.txInIndex, \
                              self.lastOpCodeSepPos) ):
               iSig  += 1
               nSigs -= 1

            iKey +=1
            nKeys -=1

            if(nSigs > nKeys):
               enoughSigsMatch = False

         # Now pop the things off the stack, we only accessed in-place before
         while i > 1:
            i -= 1
            stack.pop()


         stack.append(1 if enoughSigsMatch else 0)

         if opcode==OP_CHECKMULTISIGVERIFY:
            verifyCode = self.executeOpCode(OP_VERIFY)
            if verifyCode == TX_INVALID:
               return TX_INVALID

      else:
         return SCRIPT_ERROR

      return SCRIPT_NO_ERROR



################################################################################
def getUnspentTxOutsForAddrList(addr160List, utxoType='Sweep', startBlk=-1):
   """
   You have a list of addresses (or just one) and you want to get all the 
   unspent TxOuts for it.  This can either be for computing its balance, or
   for sweeping the address(es).

   This will return a list of pairs of [addr160, utxoObj]
   This isn't the most efficient method for producing the pairs

   NOTE:  At the moment, this only gets STANDARD TxOuts... non-std uses 
          a different BDM call
   """
   if not TheBDM.isInitialized():
      return []
   else:
      if not isinstance(addr160List, (list,tuple)):
         addr160List = [addr160List]
   
      cppWlt = Cpp.BtcWallet()
      for addr in addr160List:
         if isinstance(addr, PyBtcAddress):
            cppWlt.addAddress_1_(addr.getAddr160())
         else:
            cppWlt.addAddress_1_(addr)
   
      
      currBlk = TheBDM.getTopBlockHeader().getBlockHeight()
      TheBDM.scanBlockchainForTx(cppWlt, currBlk+1 if startBlk==-1 else startBlk)

      if utxoType.lower() in ('sweep','unspent','full','all','ultimate'):
         return cppWlt.getFullTxOutList(currBlk)
      elif utxoType.lower() in ('spend','spendable','confirmed'):
         return cppWlt.getSpendableTxOutList(currBlk)
      else:
         raise TypeError, 'Unknown utxoType!'



################################################################################
# NOTE:  This method was actually used to create the Blockchain-reorg unit-
#        test, and hence why coinbase transactions are supported.  However,
#        for normal transactions supported by PyBtcEngine, this support is
#        unnecessary.
#
#        Additionally, this method both creates and signs the tx:  however
#        PyBtcEngine employs TxDistProposals which require the construction
#        and signing to be two separate steps.  This method is not suited
#        for most of the PyBtcEngine CONOPS.
#
#        On the other hand, this method DOES work, and there is no reason
#        not to use it if you already have PyBtcAddress-w-PrivKeys avail
#        and have a list of inputs and outputs as described below.
#
# This method will take an already-selected set of TxOuts, along with
# PyBtcAddress objects containing necessary the private keys
#
#    Src TxOut ~ {PyBtcAddr, PrevTx, PrevTxOutIdx}  --OR--  COINBASE = -1
#    Dst TxOut ~ {PyBtcAddr, value}
#
# Of course, we usually don't have the private keys of the dst addrs...
#
def PyCreateAndSignTx(srcTxOuts, dstAddrsVals):
   newTx = PyTx()
   newTx.version    = 1
   newTx.lockTime   = 0
   newTx.inputs     = []
   newTx.outputs    = []


   numInputs  = len(srcTxOuts)
   numOutputs = len(dstAddrsVals)

   coinbaseTx = False
   if numInputs==1 and srcTxOuts[0] == -1:
      coinbaseTx = True


   #############################
   # Fill in TxOuts first
   for i in range(numOutputs):
      txout       = PyTxOut()
      txout.value = dstAddrsVals[i][1]
      dstAddr     = dstAddrsVals[i][0]
      if(coinbaseTx):
         txout.binScript = ''.join([  '\x41',                      \
                                      dstAddr.binPublicKey65.toBinStr(),  \
                                      getOpCode('OP_CHECKSIG'   )])
      else:
         txout.binScript = ''.join([  getOpCode('OP_DUP'        ), \
                                      getOpCode('OP_HASH160'    ), \
                                      '\x14',                      \
                                      dstAddr.getAddr160(),        \
                                      getOpCode('OP_EQUALVERIFY'), \
                                      getOpCode('OP_CHECKSIG'   )])

      newTx.outputs.append(txout)


   #############################
   # Create temp TxIns with blank scripts
   for i in range(numInputs):
      txin = PyTxIn()
      txin.outpoint = PyOutPoint()
      if(coinbaseTx):
         txin.outpoint.txHash = '\x00'*32
         txin.outpoint.txOutIndex     = binary_to_int('\xff'*4)
      else:
         txin.outpoint.txHash = hash256(srcTxOuts[i][1].serialize())
         txin.outpoint.txOutIndex     = srcTxOuts[i][2]
      txin.binScript = ''
      txin.intSeq = 2**32-1
      newTx.inputs.append(txin)


   #############################
   # Now we apply the ultra-complicated signature procedure
   # We need a copy of the Tx with all the txin scripts blanked out
   txCopySerialized = newTx.serialize()
   for i in range(numInputs):
      if coinbaseTx:
         pass
      else:
         txCopy     = PyTx().unserialize(txCopySerialized)
         srcAddr    = srcTxOuts[i][0]
         txoutIdx   = srcTxOuts[i][2]
         prevTxOut  = srcTxOuts[i][1].outputs[txoutIdx]
         binToSign  = ''

         assert(srcAddr.hasPrivKey())

         # Only implemented one type of hashing:  SIGHASH_ALL
         hashType   = 1  # SIGHASH_ALL
         hashCode1  = int_to_binary(1, widthBytes=1)
         hashCode4  = int_to_binary(1, widthBytes=4)

         # Copy the script of the TxOut we're spending, into the txIn script
         txCopy.inputs[i].binScript = prevTxOut.binScript
         preHashMsg = txCopy.serialize() + hashCode4

         # CppBlockUtils::CryptoECDSA modules do the hashing for us
         ##binToSign = hash256(preHashMsg)
         ##binToSign = binary_switchEndian(binToSign)

         signature = srcAddr.generateDERSignature(preHashMsg)


         # If we are spending a Coinbase-TxOut, only need sig, no pubkey
         # Don't forget to tack on the one-byte hashcode and consider it part of sig
         if len(prevTxOut.binScript) > 30:
            sigLenInBinary = int_to_binary(len(signature) + 1)
            newTx.inputs[i].binScript = sigLenInBinary + signature + hashCode1
         else:
            pubkey = srcAddr.binPublicKey65.toBinStr()
            sigLenInBinary    = int_to_binary(len(signature) + 1)
            pubkeyLenInBinary = int_to_binary(len(pubkey)   )
            newTx.inputs[i].binScript = sigLenInBinary    + signature + hashCode1 + \
                                        pubkeyLenInBinary + pubkey

   #############################
   # Finally, our tx is complete!
   return newTx



################################################################################
################################################################################
#
# SelectCoins algorithms
#
#   The following methods define multiple ways that one could select coins
#   for a given transaction.  However, the "best" solution is extremely
#   dependent on the variety of unspent outputs, and also the preferences
#   of the user.  Things to take into account when selecting coins:
#
#     - Number of inputs:  If we have a lot of inputs in this transaction
#                          from different addresses, then all those addresses
#                          have now been linked together.  We want to use
#                          as few outputs as possible
#
#     - Tx Fess/Size:      The bigger the transaction, in bytes, the more
#                          fee we're going to have to pay to the miners
#
#     - Priority:          Low-priority transactions might require higher
#                          fees and/or take longer to make it into the
#                          blockchain.  Priority is the sum of TxOut
#                          priorities:  (NumConfirm * NumBTC / SizeKB)
#                          We especially want to avoid 0-confirmation txs
#
#     - Output values:     In almost every transaction, we must return
#                          change to ourselves.  This means there will
#                          be two outputs, one to the recipient, one to
#                          us.  We prefer that both outputs be about the
#                          same size, so that it's not clear which is the
#                          recipient, which is the change.  But we don't
#                          want to use too many inputs to do this.
#
#     - Sustainability:    We should pick a strategy that tends to leave our
#                          wallet containing a variety of TxOuts that are
#                          well-suited for future transactions to benefit.
#                          For instance, always favoring the single TxOut
#                          with a value close to the target, will result
#                          in a future wallet full of tiny TxOuts.  This
#                          guarantees that in the future, we're going to
#                          have to do 10+ inputs for a single Tx.
#
#
#   The strategy is to execute a half dozen different types of SelectCoins
#   algorithms, each with a different goal in mind.  Then we examine each
#   of the results and evaluate a "select-score."  Use the one with the
#   best score.  In the future, we could make the scoring algorithm based
#   on user preferences.  We expect that depending on what the availble
#   list looks like, some of these algorithms could produce perfect results,
#   and in other instances *terrible* results.
#
################################################################################
################################################################################

################################################################################
# These would normally be defined by C++ and fed in, but I've recreated
# the C++ class here... it's really just a container, anyway
class PyUnspentTxOut(object):
   def __init__(self, addr='', val=-1, numConf=-1):
      pass
      #self.addr = addr
      #self.val  = long(val*ONE_BTC)
      #self.conf = numConf
      #self.binScript = '\x76\xa9\x14' + self.addr + '\x88\xac'
   def createFromCppUtxo(self, cppUtxo):
      self.addr = cppUtxo.getRecipientAddr()
      self.val  = cppUtxo.getValue()
      self.conf = cppUtxo.getNumConfirm()
      self.binScript = '\x76\xa9\x14' + self.addr + '\x88\xac'
      self.txHash     = cppUtxo.getTxHash()
      self.txOutIndex = cppUtxo.getTxOutIndex()
      return self
   def getTxHash(self):
      return self.txHash
   def getTxOutIndex(self):
      return self.txOutIndex
   def getValue(self):
      return self.val
   def getNumConfirm(self):
      return self.conf
   def getScript(self):
      return self.binScript
   def getRecipientAddr(self):
      return self.addr
   def prettyStr(self, indent=''):
      pstr = [indent]
      pstr.append(binary_to_hex(self.addr[:8]))
      pstr.append(coin2str(self.val))
      pstr.append(str(self.conf).rjust(8,' '))
      return '  '.join(pstr)
   def pprint(self, indent=''):
      print self.prettyStr(indent)


################################################################################
def sumTxOutList(txoutList):
   return sum([u.getValue() for u in txoutList])

################################################################################
# This is really just for viewing a TxOut list -- usually for debugging
def pprintUnspentTxOutList(utxoList, headerLine='Coin Selection: '):
   totalSum = sum([u.getValue() for u in utxoList])
   print headerLine, '(Total = %s BTC)' % coin2str(totalSum)
   print '   ','Owner Address'.ljust(34),
   print '   ','TxOutValue'.rjust(18),
   print '   ','NumConf'.rjust(8),
   print '   ','PriorityFactor'.rjust(16)
   for utxo in utxoList:
      print '   ',hash160_to_addrStr(utxo.getRecipientAddr()).ljust(34),
      print '   ',(coin2str(utxo.getValue()) + ' BTC').rjust(18),
      print '   ',str(utxo.getNumConfirm()).rjust(8),
      print '   ', ('%0.2f' % (utxo.getValue()*utxo.getNumConfirm()/(ONE_BTC*144.))).rjust(16)


################################################################################
# Sorting currently implemented in C++, but we implement a different kind, here
def PySortCoins(unspentTxOutInfo, sortMethod=1):
   """
   Here we define a few different ways to sort a list of unspent TxOut objects.
   Most of them are simple, some are more complex.  In particular, the last
   method (4) tries to be intelligent, by grouping together inputs from the
   same address.

   The goal is not to do the heavy lifting for SelectCoins... we simply need
   a few different ways to sort coins so that the SelectCoins algorithms has
   a variety of different inputs to play with.  Each sorting method is useful
   for some types of unspent-TxOut lists, so as long as we have one good
   sort, the PyEvalCoinSelect method will pick it out.

   As a precaution we send all the zero-confirmation UTXO's to the back
   of the list, so that they will only be used if absolutely necessary.
   """
   zeroConfirm = []

   if sortMethod==0:
      priorityFn = lambda a: a.getValue() * a.getNumConfirm()
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==1:
      priorityFn = lambda a: (a.getValue() * a.getNumConfirm())**(1/3.)
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==2:
      priorityFn = lambda a: (math.log(a.getValue()*a.getNumConfirm()+1)+4)**4
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==3:
      priorityFn = lambda a: a.getValue() if a.getNumConfirm()>0 else 0
      return sorted(unspentTxOutInfo, key=priorityFn, reverse=True)
   if sortMethod==4:
      addrMap = {}
      zeroConfirm = []
      for utxo in unspentTxOutInfo:
         if utxo.getNumConfirm() == 0:
            zeroConfirm.append(utxo)
         else:
            addr = TxOutScriptExtractAddr160(utxo.getScript())
            if not addrMap.has_key(addr):
               addrMap[addr] = [utxo]
            else:
               addrMap[addr].append(utxo)

      priorityUTXO = (lambda a: (a.getNumConfirm()*a.getValue()**0.333))
      for addr,txoutList in addrMap.iteritems():
         txoutList.sort(key=priorityUTXO, reverse=True)

      priorityGrp = lambda a: max([priorityUTXO(utxo) for utxo in a])
      finalSortedList = []
      for utxo in sorted(addrMap.values(), key=priorityGrp, reverse=True):
         finalSortedList.extend(utxo)

      finalSortedList.extend(zeroConfirm)
      return finalSortedList
   if sortMethod in (5, 6, 7):
      utxoSorted = PySortCoins(unspentTxOutInfo, 1)
      # Rotate the top 1,2 or 3 elements to the bottom of the list
      for i in range(sortMethod-4):
         utxoSorted.append(utxoSorted[0])
         del utxoSorted[0]
      return utxoSorted

   # TODO:  Add a semi-random sort method:  it will favor putting high-priority
   #        outputs at the front of the list, but will not be deterministic
   #        This should give us some high-fitness variation compared to sorting
   #        uniformly
   if sortMethod==8:
      utxosNoZC = filter(lambda a: a.getNumConfirm()!=0, unspentTxOutInfo)
      random.shuffle(utxosNoZC)
      utxosNoZC.extend(filter(lambda a: a.getNumConfirm()==0, unspentTxOutInfo))
      return utxosNoZC
   if sortMethod==9:
      utxoSorted = PySortCoins(unspentTxOutInfo, 1)
      sz = len(filter(lambda a: a.getNumConfirm()!=0, utxoSorted))
      # swap 1/3 of the values at random
      topsz = int(min(max(round(sz/3), 5), sz))
      for i in range(topsz):
         pick1 = int(random.uniform(0,topsz))
         pick2 = int(random.uniform(0,sz-topsz))
         utxoSorted[pick1], utxoSorted[pick2] = utxoSorted[pick2], utxoSorted[pick1]
      return utxoSorted




################################################################################
# Now we try half a dozen different selection algorithms
################################################################################



################################################################################
def PySelectCoins_SingleInput_SingleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   This method should usually be called with a small number added to target val
   so that a tx can be constructed that has room for user to add some extra fee
   if necessary.

   However, we must also try calling it with the exact value, in case the user
   is trying to spend exactly their remaining balance.
   """
   target = targetOutVal + minFee
   bestMatchVal  = 2**64
   bestMatchUtxo = None
   for utxo in unspentTxOutInfo:
      if target <= utxo.getValue() < bestMatchVal:
         bestMatchVal = utxo.getValue()
         bestMatchUtxo = utxo

   closeness = bestMatchVal - target
   if 0 < closeness <= CENT:
      # If we're going to have a change output, make sure it's above CENT
      # to avoid a mandatory fee
      try2Val  = 2**64
      try2Utxo = None
      for utxo in unspentTxOutInfo:
         if target+CENT < utxo.getValue() < try2Val:
            try2Val = utxo.getValue()
            try2Val = utxo
      if not try2Utxo==None:
         bestMatchUtxo = try2Utxo


   if bestMatchUtxo==None:
      return []
   else:
      return [bestMatchUtxo]

################################################################################
def PySelectCoins_MultiInput_SingleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   This method should usually be called with a small number added to target val
   so that a tx can be constructed that has room for user to add some extra fee
   if necessary.

   However, we must also try calling it with the exact value, in case the user
   is trying to spend exactly their remaining balance.
   """
   target = targetOutVal + minFee
   outList = []
   sumVal = 0
   for utxo in unspentTxOutInfo:
      sumVal += utxo.getValue()
      outList.append(utxo)
      if sumVal>=target:
         break

   return outList



################################################################################
def PySelectCoins_SingleInput_DoubleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):
   """
   We will look for a single input that is within 30% of the target
   In case the tx value is tiny rel to the fee: the minTarget calc
   may fail to exceed the actual tx size needed, so we add an extra

   We restrain the search to 25%.  If there is no one output in this
   range, then we will return nothing, and the SingleInput_SingleValue
   method might return a usable result
   """
   idealTarget    = 2*targetOutVal + minFee

   # check to make sure we're accumulating enough
   minTarget   = long(0.75 * idealTarget)
   minTarget   = max(minTarget, targetOutVal+minFee)
   maxTarget   = long(1.25 * idealTarget)

   if sum([u.getValue() for u in unspentTxOutInfo]) < minTarget:
      return []

   bestMatch = 2**64-1
   bestUTXO   = None
   for txout in unspentTxOutInfo:
      if minTarget <= txout.getValue() <= maxTarget:
         if abs(txout.getValue()-idealTarget) < bestMatch:
            bestMatch = abs(txout.getValue()-idealTarget)
            bestUTXO = txout

   if bestUTXO==None:
      return []
   else:
      return [bestUTXO]

################################################################################
def PySelectCoins_MultiInput_DoubleValue( \
                                    unspentTxOutInfo, targetOutVal, minFee=0):

   idealTarget = 2.0 * targetOutVal
   minTarget   = long(0.80 * idealTarget)
   minTarget   = max(minTarget, targetOutVal+minFee)
   if sum([u.getValue() for u in unspentTxOutInfo]) < minTarget:
      return []

   outList   = []
   lastDiff  = 2**64-1
   sumVal    = 0
   for utxo in unspentTxOutInfo:
      sumVal += utxo.getValue()
      outList.append(utxo)
      currDiff = abs(sumVal - idealTarget)
      # should switch from decreasing to increasing when best match
      if sumVal>=minTarget and currDiff>lastDiff:
         del outList[-1]
         break
      lastDiff = currDiff

   return outList




################################################################################
def getSelectCoinsScores(utxoSelectList, targetOutVal, minFee):
   """
   Define a metric for scoring the output of SelectCoints.  The output of
   this method is a tuple of scores which identify a few different factors
   of a txOut selection that users might care about in a selectCoins algorithm.

   This method only returns an absolute score, usually between 0 and 1 for
   each factor.  It is up to the person calling this method to decide how
   much "weight" they want to give each one.  You could even use the scores
   as multiplicative factors if you wanted, though they were designed with
   the following equation in mind:   finalScore = sum(WEIGHT[i] * SCORE[i])

   TODO:  I need to recalibrate some of these factors, and modify them to
          represent more directly what the user would be concerned about --
          such as PayFeeFactor, AnonymityFactor, etc.  The information is
          indirectly available with the current set of factors here
   """

   # Need to calculate how much the change will be returned to sender on this tx
   totalIn = sum([utxo.getValue() for utxo in utxoSelectList])
   totalChange = totalIn - (targetOutVal+minFee)

   # Abort if this is an empty list (negative score) or not enough coins
   if len(utxoSelectList)==0 or totalIn<targetOutVal+minFee:
      return -1


   ##################
   # -- Does this selection include any zero-confirmation tx?
   # -- How many addresses are linked together by this tx?
   addrSet = set([])
   noZeroConf = 1
   for utxo in utxoSelectList:
      addrSet.add(TxOutScriptExtractAddr160(utxo.getScript()))
      if utxo.getNumConfirm() == 0:
         noZeroConf = 0
   numAddr = len(addrSet)
   numAddrFactor = 4.0/(numAddr+1)**2  # values in the range (0, 1]



   ##################
   # Evaluate output anonanymity
   # One good measure of anonymity is look at trailiing zeros of the value.
   # If one output is like 50.0, and nother if 27.383291, then it's fairly
   # obvious which one is the change.  Can measure that by seeing that 50.0
   # in satoshis has 9 trailing zeros, where as 27.383291 only has 2
   #
   # If the diff is negative, the wrong answer starts to look like the
   # correct one (about which output is recipient and which is change)
   # We should give "extra credit" for those cases
   def countTrailingZeros(btcVal):
      for i in range(1,20):
         if btcVal % 10**i != 0:
            return i-1
      return 0  # not sure how we'd get here, but let's be safe
   tgtTrailingZeros =  countTrailingZeros(targetOutVal)
   chgTrailingZeros =  countTrailingZeros(totalChange)
   zeroDiff = tgtTrailingZeros - chgTrailingZeros
   outAnonFactor = 0
   if totalChange==0:
      outAnonFactor = 1
   else:
      if zeroDiff==2:
         outAnonFactor = 0.2
      elif zeroDiff==1:
         outAnonFactor = 0.7
      elif zeroDiff<1:
         outAnonFactor = abs(zeroDiff) + 1


   ##################
   # Equal inputs are anonymous-- but no point in doing this if the
   # trailing zeros count is way different -- i.e. does it matter if
   # outputs a and b are close, if a=51.000, and b=47.283?  It's
   # still pretty obvious which one is the change. (so: only execute
   # the following block if outAnonFactor > 0)
   #
   # On the other hand, if we have 1.832 and 10.00, and the 10.000 is the
   # change, we don't really care that they're not close, it's still
   # damned good/deceptive output anonymity  (so: only execute
   # the following block if outAnonFactor <= 1)
   if 0 < outAnonFactor <= 1 and not totalChange==0:
      outValDiff = abs(totalChange - targetOutVal)
      diffPct = (outValDiff / max(totalChange, targetOutVal))
      if diffPct < 0.20:
         outAnonFactor *= 1
      elif diffPct < 0.50:
         outAnonFactor *= 0.7
      elif diffPct < 1.0:
         outAnonFactor *= 0.3
      else:
         outAnonFactor = 0


   ##################
   # Tx size:  we don't have signatures yet, but we assume that each txin is
   #           about 180 Bytes, TxOuts are 35, and 10 other bytes in the Tx
   numBytes  =  10
   numBytes += 180 * len(utxoSelectList)
   numBytes +=  35 * (1 if totalChange==0 else 2)
   txSizeFactor = 0
   numKb = int(numBytes / 1000)
   # Will compute size factor after we see this tx priority and AllowFree
   # results.  If the tx qualifies for free, we don't need to penalize
   # a 3 kB transaction vs one that is 0.5 kB


   ##################
   # Priority:  If our priority is above the 1-btc-after-1-day threshold
   #            then we might be allowed a free tx.  But, if its priority
   #            isn't much above this thresh, it might take a couple blocks
   #            to be included
   dPriority = 0
   anyZeroConfirm = False
   for utxo in utxoSelectList:
      if utxo.getNumConfirm() == 0:
         anyZeroConfirm = True
      else:
         dPriority += utxo.getValue() * utxo.getNumConfirm()

   dPriority = dPriority / numBytes
   priorityThresh = ONE_BTC * 144 / 250
   if dPriority < priorityThresh:
      priorityFactor = 0
   elif dPriority < 10.0*priorityThresh:
      priorityFactor = 0.7
   elif dPriority < 100.0*priorityThresh:
      priorityFactor = 0.9
   else:
      priorityFactor = 1.0


   ##################
   # AllowFree:  If three conditions are met, then the tx can be sent safely
   #             without a tx fee.  Granted, it may not be included in the
   #             current block if the free space is full, but definitely in
   #             the next one
   isFreeAllowed = 0
   haveDustOutputs = (0<totalChange<CENT or targetOutVal<CENT)
   if ((not haveDustOutputs) and \
       dPriority >= priorityThresh and \
       numBytes <= 3500):
      isFreeAllowed = 1


   ##################
   # Finish size-factor calculation -- if free is allowed, kB is irrelevant
   txSizeFactor = 0
   if isFreeAllowed or numKb<1:
      txSizeFactor = 1
   else:
      if numKb < 2:
         txSizeFactor=0.2
      elif numKb<3:
         txSizeFactor=0.1
      elif numKb<4:
         txSizeFactor=0
      else:
         txSizeFactor=-1  #if this is huge, actually subtract score

   return (isFreeAllowed, noZeroConf, priorityFactor, numAddrFactor, txSizeFactor, outAnonFactor)


################################################################################
# We define default preferences for weightings.  Weightings are used to
# determine the "priorities" for ranking various SelectCoins results
# By setting the weights to different orders of magnitude, you are essentially
# defining a sort-order:  order by FactorA, then sub-order by FactorB...
################################################################################
# TODO:  ADJUST WEIGHTING!
IDX_ALLOWFREE   = 0
IDX_NOZEROCONF  = 1
IDX_PRIORITY    = 2
IDX_NUMADDR     = 3
IDX_TXSIZE      = 4
IDX_OUTANONYM   = 5
WEIGHTS = [None]*6
WEIGHTS[IDX_ALLOWFREE]  =  100000
WEIGHTS[IDX_NOZEROCONF] = 1000000  # let's avoid zero-conf if possible
WEIGHTS[IDX_PRIORITY]   =      50
WEIGHTS[IDX_NUMADDR]    =  100000
WEIGHTS[IDX_TXSIZE]     =     100
WEIGHTS[IDX_OUTANONYM]  =      30


################################################################################
def PyEvalCoinSelect(utxoSelectList, targetOutVal, minFee, weights=WEIGHTS):
   """
   Use a specified set of weightings and sub-scores for a unspentTxOut list,
   to assign an absolute "fitness" of this particular selection.  The goal of
   getSelectCoinsScores() is to produce weighting-agnostic subscores -- then
   this method applies the weightings to these scores to get a final answer.

   If list A has a higher score than list B, then it's a better selection for
   that transaction.  If you the two scores don't look right to you, then you
   probably just need to adjust the weightings to your liking.

   These weightings may become user-configurable in the future -- likely as an
   option of coin-selection profiles -- such as "max anonymity", "min fee",
   "balanced", etc).
   """
   scores = getSelectCoinsScores(utxoSelectList, targetOutVal, minFee)
   if scores==-1:
      return -1

   # Combine all the scores
   theScore  = 0
   theScore += weights[IDX_NOZEROCONF] * scores[IDX_NOZEROCONF]
   theScore += weights[IDX_PRIORITY]   * scores[IDX_PRIORITY]
   theScore += weights[IDX_NUMADDR]    * scores[IDX_NUMADDR]
   theScore += weights[IDX_TXSIZE]     * scores[IDX_TXSIZE]
   theScore += weights[IDX_OUTANONYM]  * scores[IDX_OUTANONYM]

   # If we're already paying a fee, why bother including this weight?
   if minFee < 0.0005:
      theScore += weights[IDX_ALLOWFREE]  * scores[IDX_ALLOWFREE]

   return theScore


################################################################################
def PySelectCoins(unspentTxOutInfo, targetOutVal, minFee=0, numRand=10, margin=CENT):
   """
   Intense algorithm for coin selection:  computes about 30 different ways to
   select coins based on the desired target output and the min tx fee.  Then
   ranks the various solutions and picks the best one
   """
   if sum([u.getValue() for u in unspentTxOutInfo]) < targetOutVal:
      return []

   targExact  = targetOutVal
   targMargin = targetOutVal+margin

   selectLists = []

   # Start with the intelligent solutions with different sortings
   for sortMethod in range(8):
      diffSortList = PySortCoins(unspentTxOutInfo, sortMethod)
      selectLists.append(PySelectCoins_SingleInput_SingleValue( diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_MultiInput_SingleValue(  diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_SingleInput_SingleValue( diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_MultiInput_SingleValue(  diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_SingleInput_DoubleValue( diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_MultiInput_DoubleValue(  diffSortList, targExact,  minFee ))
      selectLists.append(PySelectCoins_SingleInput_DoubleValue( diffSortList, targMargin, minFee ))
      selectLists.append(PySelectCoins_MultiInput_DoubleValue(  diffSortList, targMargin, minFee ))

   # Throw in a couple random solutions, maybe we get lucky
   # But first, make a copy before in-place shuffling
   # NOTE:  using list[:] like below, really causes a swig::vector<type> to freak out!
   #utxos = unspentTxOutInfo[:]
   #utxos = list(unspentTxOutInfo)
   for method in range(8,10):
      for i in range(numRand):
         utxos = PySortCoins(unspentTxOutInfo, method)
         selectLists.append(PySelectCoins_MultiInput_SingleValue(utxos, targExact,  minFee))
         selectLists.append(PySelectCoins_MultiInput_DoubleValue(utxos, targExact,  minFee))
         selectLists.append(PySelectCoins_MultiInput_SingleValue(utxos, targMargin, minFee))
         selectLists.append(PySelectCoins_MultiInput_DoubleValue(utxos, targMargin, minFee))

   # Now we define PyEvalCoinSelect as our sorting metric, and find the best solution
   scoreFunc = lambda ulist: PyEvalCoinSelect(ulist, targetOutVal, minFee)
   finalSelection = max(selectLists, key=scoreFunc)
   SCORES = getSelectCoinsScores(finalSelection, targetOutVal, minFee)
   if len(finalSelection)==0:
      return []

   # If we selected a list that has only one or two inputs, and we have
   # other, tiny, unspent outputs from the same addresses, we should
   # throw one or two of them in to help clear them out.  However, we
   # only do so if a plethora of conditions exist:
   #
   # First, we only consider doing this if the tx has <5 inputs already.
   # Also, we skip this process if the current tx doesn't have excessive
   # priority already -- we don't want to risk de-prioritizing a tx for
   # this purpose.
   #
   # Next we sort by LOWEST value, because we really benefit from this most
   # by clearing out tiny outputs.  Along those lines, we don't even do
   # unless it has low priority -- don't want to take a high-priority utxo
   # and convert it to one that will be low-priority to start.
   #
   # Finally, we shouldn't do this if a high score was assigned to output
   # anonymity: this extra output may cause a tx with good output anonymity
   # to no longer possess this property
   IDEAL_NUM_INPUTS = 5
   if len(finalSelection) < IDEAL_NUM_INPUTS and \
          SCORES[IDX_OUTANONYM] == 0:

      alreadyUsedAddr = set( [utxo.getRecipientAddr() for utxo in finalSelection] )
      getPriority = lambda a: a.getValue() * a.getNumConfirm()
      utxoSmallToLarge = sorted(unspentTxOutInfo, key=getPriority)
      
      for other in utxoSmallToLarge:
         
         # Skip it if it is already selected
         if other in finalSelection:
            continue

         # We only consider UTXOs that won't link any new addresses together
         if not other.getRecipientAddr() in alreadyUsedAddr:
            continue
         
         # Avoid zero-conf inputs altogether
         if other.getNumConfirm() == 0:
            continue

         # Don't consider any inputs that are high priority already
         if getPriority(other) > ONE_BTC*144:
            continue

         finalSelection.append(other) 
         if len(finalSelection)>=IDEAL_NUM_INPUTS:
            break

   return finalSelection


def calcMinSuggestedFees(selectCoinsResult, targetOutVal, preSelectedFee):
   """
   Returns two fee options:  one for relay, one for include-in-block.
   In general, relay fees are required to get your block propagated
   (since most nodes are Satoshi clients), but there's no guarantee
   it will be included in a block -- though I'm sure there's plenty
   of miners out there will include your tx for sub-standard fee.
   However, it's virtually guaranteed that a miner will accept a fee
   equal to the second return value from this method.

   We have to supply the fee that was used in the selection algorithm,
   so that we can figure out how much change there will be.  Without
   this information, we might accidentally declare a tx to be freeAllow
   when it actually is not.
   """

   if len(selectCoinsResult)==0:
      return [-1,-1]

   paid = targetOutVal + preSelectedFee
   change = sum([u.getValue() for u in selectCoinsResult]) - paid

   # Calc approx tx size
   numBytes  =  10
   numBytes += 180 * len(selectCoinsResult)
   numBytes +=  35 * (1 if change==0 else 2)
   numKb = int(numBytes / 1000)

   # Compute raw priority of tx
   prioritySum = 0
   for utxo in selectCoinsResult:
      prioritySum += utxo.getValue() * utxo.getNumConfirm()
   prioritySum = prioritySum / numBytes

   # Any tiny/dust outputs?
   haveDustOutputs = (0<change<CENT or targetOutVal<CENT)

   if((not haveDustOutputs) and \
      prioritySum >= ONE_BTC * 144 / 250. and \
      numBytes <= 3600):
      return [0,0]

   # This cannot be a free transaction.
   minFeeMultiplier = (1 + numKb)

   # At the moment this condition never triggers
   if minFeeMultiplier<1.0 and haveDustOutputs:
      minFeeMultiplier = 1.0


   return [minFeeMultiplier * MIN_RELAY_TX_FEE, \
           minFeeMultiplier * MIN_TX_FEE]






################################################################################
################################################################################
# This class can be used for both multi-signature tx collection, as well as
# offline wallet signing (you are collecting signatures for a 1-of-1 tx only
# involving yourself).
class PyTxDistProposal(object):
   """
   PyTxDistProposal is created from a PyTx object, and represents
   an unsigned transaction, that may require the signatures of
   multiple parties before being accepted by the network.

   This technique (https://en.bitcoin.it/wiki/BIP_0010) is that 
   once TxDP is created, the system signing it only needs the 
   ECDSA private keys and nothing else.   This enables the device
   providing the signatures to be extremely lightweight, since it
   doesn't have to store the blockchain.

   For a given TxDP, we will be storing the following structure
   in memory.  Use a 3-input tx as an example, with the first 
   being a 2-of-3 multi-sig transaction (unsigned)
      
      self.scriptTypes    = [TXOUT_SCRIPT_MULTISIG, 
                             TXOUT_SCRIPT_STANDARD,   
                             TXOUT_SCRIPT_STANDARD]

      self.inputValues    = [ 2313000000, 
                              400000000, 
                              1000000000]

      self.signatures     = [ ['', '', ''],
                              [''],
                              [''],         ]

      self.inAddr20Lists  = [ [addr1, addr2, addr3],
                              [addr4]
                              [addr5]         ]

      # Usually only have public keys on multi-sig TxOuts
      self.inPubKeyLists  = [ [pubKey1, pubKey2, pubKey3],
                              ['']
                              ['']         ]   

      self.numSigsNeeded  = [ 2
                              1
                              1 ]

      self.relevantTxMap  = [ prevTx0Hash: prevTx0.serialize(),
                              prevTx1Hash: prevTx1.serialize(),
                              prevTx2Hash: prevTx2.serialize() ]
      
   UPDATE Feb 2012:  Before Jan 29, 2012, BIP 0010 used a different technique
                     for communicating blockchain information to the offline
                     device.  This is no longer the case
                     
                     Gregory Maxwell identified a reasonable-enough security
                     risk with the fact that previous BIP 0010 cannot guarantee 
                     validity of stated input values in a TxDP.  This is solved
                     by adding the supporting transactions to the TxDP, so that 
                     the signing device can get the input values from those 
                     tx and verify the hash matches the OutPoint on the tx 
                     being signed (which *is* part of what's being signed).  
                     The concern was that someone could manipulate your online
                     computer to misrepresent the inputs, and cause you to 
                     send you entire wallet to tx-fees.  Not the most useful
                     attack (for someone trying to steal your coins), but it is
                     still a risk that can be avoided by adding some "bloat" to
                     the TxDP

                     
   
   """
   #############################################################################
   def __init__(self, pytx=None, txMap={}):
      self.pytxObj       = UNINITIALIZED
      self.uniqueB58     = ''
      self.scriptTypes   = []
      self.signatures    = []
      self.txOutScripts  = []
      self.inAddr20Lists = []
      self.inPubKeyLists = []
      self.inputValues   = []
      self.numSigsNeeded = []
      self.relevantTxMap = {}  # needed to support input values of each TxIn
      if pytx:
         self.createFromPyTx(pytx, txMap)

   #############################################################################
   def createFromPyTx(self, pytx, txMap={}):
      sz = len(pytx.inputs)
      self.pytxObj        = pytx.copy()
      self.uniqueB58 = binary_to_base58(hash256(pytx.serialize()))[:8]
      self.scriptTypes    = []
      self.signatures     = []
      self.txOutScripts   = []
      self.inAddr20Lists  = []
      self.inPubKeyLists  = []
      self.inputValues    = []
      self.numSigsNeeded  = []
      self.relevantTxMap  = {}  # needed to support input values of each TxIn

      if len(txMap)==0 and not TheBDM.isInitialized():
         raise BlockchainUnavailableError, ('Must input supporting transactions '
                                            'or access to the blockchain, to '
                                            'create the TxDP')
      for i in range(sz):
         # First, make sure that we have the previous Tx data available
         # We can't continue without it, since BIP 0010 will now require
         # the full tx of outputs being spent
         outpt = self.pytxObj.inputs[i].outpoint
         txhash = outpt.txHash
         txidx  = outpt.txOutIndex
         pyPrevTx = None
         if len(txMap)>0:
            # If supplied a txMap, we expect it to have everything we need
            if not txMap.has_key(txhash):
               raise InvalidHashError, ('Could not find the referenced tx '
                                        'in supplied txMap')
            pyPrevTx = txMap[txhash].copy()
         elif TheBDM.isInitialized():
            cppPrevTx = TheBDM.getTxByHash(txhash)
            if not cppPrevTx:
               raise InvalidHashError, 'Could not find the referenced tx'
            pyPrevTx = PyTx().unserialize(cppPrevTx.serialize())
         else:
            raise InvalidHashError, 'No previous-tx data available for TxDP'
         self.relevantTxMap[txhash] = pyPrevTx.copy()
               
           
         # Now we have the previous transaction.  We need to pull the 
         # script out of the specific TxOut so we know how it can be
         # spent.
         script =  pyPrevTx.outputs[txidx].binScript
         value  =  pyPrevTx.outputs[txidx].value
         scrType = getTxOutScriptType(script)

         self.inputValues.append(value)
         self.txOutScripts.append(str(script)) # copy it
         self.scriptTypes.append(scrType)
         self.inAddr20Lists.append([])
         self.inPubKeyLists.append([])
         self.signatures.append([])
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            self.inAddr20Lists[-1].append(TxOutScriptExtractAddr160(script))
            self.inPubKeyLists[-1].append('')
            self.signatures[-1].append('')
            self.numSigsNeeded.append(1)
         elif scrType==TXOUT_SCRIPT_MULTISIG:
            mstype, addrs, pubs = getTxOutMultiSigInfo(script)
            self.inAddr20Lists[-1] = addrs
            self.inPubKeyLists[-1] = pubs
            self.signatures[-1]    = ['']*len(addrs)
            self.numSigsNeeded[-1] = mstype[0]  # mstype for M-of-N tx is (M,N)
         elif scrType in (TXOUT_SCRIPT_OP_EVAL, TXOUT_SCRIPT_UNKNOWN):
            pass

      return self


   #############################################################################
   def createFromTxOutSelection(self, utxoSelection, recip160ValPairs, txMap={}):
      """
      This creates a TxDP for a standard transaction from a list of inputs and 
      a list of recipient-value-pairs.  

      NOTE:  I have modified this so that if the "recip" is not a 20-byte binary
             string, it is instead interpretted as a SCRIPT -- which could be
             anything, including a multi-signature transaction
      """

      pprintUnspentTxOutList(utxoSelection)
      #print sumTxOutList(utxoSelection)
      #print sum([a[1] for a in recip160ValPairs])
      assert(sumTxOutList(utxoSelection) >= sum([a[1] for a in recip160ValPairs]))
      thePyTx = PyTx()
      thePyTx.version = 1
      thePyTx.lockTime = 0
      thePyTx.inputs = []
      thePyTx.outputs = []

      # We can prepare the outputs, first
      for recipObj,value in recip160ValPairs:
         txout = PyTxOut()
         txout.value = long(value)

         # Assume recipObj is either a PBA or a string
         if isinstance(recipObj, PyBtcAddress):
            recipObj = recipObj.getAddr160()

         # Now recipObj is def a string
         if len(recipObj)!=20:
            # If not an address, it's a full script
            txout.binScript = recipObj
         else:
            # Construct a std TxOut from addr160 str
            txout.binScript = ''.join([  getOpCode('OP_DUP'        ), \
                                         getOpCode('OP_HASH160'    ), \
                                         '\x14',                      \
                                         recipObj,
                                         getOpCode('OP_EQUALVERIFY'), \
                                         getOpCode('OP_CHECKSIG'   )])
         thePyTx.outputs.append(txout)

      # Prepare the inputs based on the utxo objects
      for iin,utxo in enumerate(utxoSelection):
         # First, make sure that we have the previous Tx data available
         # We can't continue without it, since BIP 0010 will now require
         # the full tx of outputs being spent
         txin = PyTxIn()
         txin.outpoint = PyOutPoint()
         txin.binScript = ''
         txin.intSeq = 2**32-1

         txhash = utxo.getTxHash()
         txidx  = utxo.getTxOutIndex()
         txin.outpoint.txHash = str(txhash)
         txin.outpoint.txOutIndex = txidx
         thePyTx.inputs.append(txin)

      return self.createFromPyTx(thePyTx, txMap)



   #############################################################################
   def appendSignature(self, binSig, txinIndex=None):
      """
      Use this to add a signature to the TxDP object in memory.
      """
      idx, pos, addr = self.processSignature(binSig, txinIndex, checkAllInputs=True)
      if addr:
         self.signatures[validIdx].append(binSig)
         return True
   
      return False


   #############################################################################
   def processSignature(self, sigStr, txinIdx, checkAllInputs=False):
      """
      For standard transaction types, the signature field is actually the raw
      script to be plugged into the final transaction that allows it to eval
      to true -- except for multi-sig transactions.  We have to mess with the 
      data a little bit if we want to use the script-processor to verify the
      signature.  Instead, we will use the crypto ops directly.

      The return value is everything we need to know about this signature:
      -- TxIn-index:    if checkAllInputs=True, we need to know which one worked
      -- Addr-position: for multi-sig tx, we need to know which addr it matches
      -- Addr160:       address to which this signature corresponds
      """

      if txinIdx==None or txinIdx<0 or txinIdx>=len(self.pytxObj.inputs):
         pass
      else:
         scriptType = self.scriptTypes[txinIdx]
         txCopy = self.pytxObj.copy()
         if scriptType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            # For standard Tx types, sigStr is the full script itself (copy it)
            txCopy.inputs[txinIdx].binScript = str(sigStr)
            prevOutScript = str(self.txOutScripts[txinIdx])
            psp = PyScriptProcessor(prevOutScript, txCopy, txinIdx)
            if psp.verifyTransactionValid():
               return txinIdx, 0, TxOutScriptExtractAddr160(prevOutScript)
         elif scriptType == TXOUT_SCRIPT_MULTISIG:
            # For multi-sig, sigStr is the raw ECDSA sig ... we will have to
            # manually construct a tx that the script processor can check,
            # without the other signatures
            for i in range(len(txCopy.inputs)):
               if not i==idx:
                  txCopy.inputs[i].binScript = ''
               else:
                  txCopy.inputs[i].binScript = self.txOutScripts[i]
   
            hashCode   = binary_to_int(sigStr[-1])
            hashCode4  = int_to_binary(hashcode, widthBytes=4)
            preHashMsg = txCopy.serialize() + hashCode4
            if not hashCode==1:
               raise NotImplementedError, 'Non-standard hashcodes not supported!'
   
            # Now check all public keys in the multi-sig TxOut script
            for i,pubkey in enumerate(self.inPubKeyLists):
               tempAddr = PyBtcAddress().createFromPublicKeyData(pubkey)
               if tempAddr.verifyDERSignature(preHashMsg, sigStr):
                  return txInIdx, i, hash160(pubkey)
         

      if checkAllInputs:
         for i in range(len(self.pytxObj.inputs)):
            idx, pos, addr160 = self.processSignature(sigStr, i)
            if idx>0:
               return idx, pos, addr160
         
      return -1,-1,''
      

   #############################################################################
   def checkTxHasEnoughSignatures(self, alsoVerify=False):
      """
      This method only counts signatures, unless verify==True
      """
      for i in range(len(self.pytxObj.inputs)):
         numSigsHave = sum( [(1 if sig else 0) for sig in self.signatures[i]] )
         if numSigsHave<self.numSigsNeeded[i]:
            return False

      if not alsoVerify:
         return True

      if not self.getBroadcastTxIfReady():
         return False

      return True
      
      
      
            

   #############################################################################
   def getBroadcastTxIfReady(self):
      try:
         return self.prepareFinalTx()
      except SignatureError, msg:
         return None
      # Let all other exceptions go on up the chain
   

   
   #############################################################################
   def isSigValidForInput(self, i):
      """
      For now we assume that each input only requires one signature, and thus 
      we have it or we don't.  In the future, this will be expanded for the 
      multi-sig case, and return a list signatures needed and which ones are 
      signed/valid
      """
      psp = PyScriptProcessor()
      # STUB -- will get to this when I need it



   #############################################################################
   def prepareFinalTx(self):
      """
      This converts the TxDP back into a regular PyTx object, verifying
      signatures as it goes.  Throw an error if the TxDP does not have
      the complete set of valid signatures needed to be accepted by the 
      network.
      """
      if not self.checkTxHasEnoughSignatures():
         return None

      # We must make/modify a copy of the TxDP, because serialization relies
      # on having the original TxDP intact.
      finalTx = self.pytxObj.copy()

      # Put the txIn scripts together (non-trivial for multi-sig cases)
      # then run them through the script evaluator to make sure they
      # are valid. 
      psp = PyScriptProcessor()
      for i,txin in enumerate(finalTx.inputs):
         if self.scriptTypes[i] in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            finalTx.inputs[i].binScript = self.signatures[i][0]
         elif self.scriptTypes[i]==TXOUT_SCRIPT_MULTISIG:
            sortedSigs = ['']*len(self.inAddr20Lists[i])
            for sig in self.signatures[i]:
               idx, pos, addr = self.processSignature(sig, i)
               if not addr:
                  raise SignatureError, 'Sig is not valid for input', i
               else:
                  sortedSigs[pos] = sig
            finalTx.inputs[i].binScript = getOpCode('OP_0') + ''.join(sortedSigs)

         psp.setTxObjects(self.txOutScripts[i], finalTx, i)
         totalScriptValid = psp.verifyTransactionValid()
         if not totalScriptValid:
            LOGWARN('Invalid script for input %d:')
            pprintScript(finalTx.inputs[i].binScript, 2)
            LOGWARN('Spending txout script:')
            pprintScript(self.txOutScripts[i], 2)
            raise SignatureError, 'Invalid script for input %d' % i
         else:
            if len(self.inAddr20Lists)==1: print 'Signature', i, 'is valid!'
            else: LOGDEBUG('Signatures for input %d are valid!', i)
      return finalTx


   #############################################################################
   def serializeAscii(self):
      txdpLines = []
      headline = ('-----BEGIN-TRANSACTION-' + self.uniqueB58 + '-----').ljust(80,'-')
      txdpLines.append( headline )
      dpsz = len(self.pytxObj.serialize())
      pieces = ['', 'TXDIST', binary_to_hex(MAGIC_BYTES), self.uniqueB58, \
                      int_to_hex(dpsz, widthBytes=2, endOut=BIGENDIAN)]
      txdpLines.append('_'.join(pieces))
      
      # First tx is always the tx being created/signed, others are supporting tx
      try:
         txList = [self.pytxObj.serialize()]
         txList.extend([self.relevantTxMap[txin.outpoint.txHash].serialize() \
                                                for txin in self.pytxObj.inputs])
      except KeyError:
         raise InvalidHashError, ('One or more OutPoints could not be found -- '
                                  'the TxDP could not be serialized')

      txHex = binary_to_hex(''.join(txList))
      for byte in range(0,len(txHex),80):
         txdpLines.append( txHex[byte:byte+80] )

      for iin,txin in enumerate(self.pytxObj.inputs):
         if self.inputValues[iin]:
            formattedVal = coin2str(self.inputValues[iin], ndec=8)
         else:
            formattedVal = '0'

         txdpLines.append('_TXINPUT_%02d_%s' % (iin, formattedVal.strip()))
         for s,sig in enumerate(self.signatures[iin]):
            if len(sig)==0:
               continue
            addrB58 = hash160_to_addrStr(self.inAddr20Lists[iin][s])
            sigsz = int_to_hex(len(sig), widthBytes=2, endOut=BIGENDIAN)
            txdpLines.append('_SIG_%s_%02d_%s' % (addrB58, iin, sigsz))
            sigHex = binary_to_hex(sig)
            for byte in range(0,len(sigHex),80):
               txdpLines.append( sigHex[byte:byte+80] )

      endline = ('-------END-TRANSACTION-' + self.uniqueB58 + '-----').ljust(80,'-')
      txdpLines.append( endline )
      LOGPPRINT(self, logging.DEBUG)
      return '\n'.join(txdpLines)
      

   #############################################################################
   def unserializeAscii(self, asciiStr):
      txdpTxt = [line.strip() for line in asciiStr.split('\n')]

      # Why can't I figure out the best way to do this with generators?
      # I know there's a bettery [python-]way to do this...
      L = [0]
      def nextLine(i):
         s = txdpTxt[i[0]].strip()
         i[0] += 1
         return s

      line = nextLine(L)
      while not ('BEGIN-TRANSACTION' in line):
         line = nextLine(L)

      # Get the network, dp ID and number of bytes
      line = nextLine(L)
      magicBytesHex, dpIdB58, dpsz = line.split('_')[2:]
      magic = hex_to_binary(magicBytesHex)

      # Read in the full, hex, tx list: first one is to be signed, remaining
      # are there to support verification of input values
      dpser = ''
      line = nextLine(L)
      while not 'TXINPUT' in line:
         dpser += line
         line = nextLine(L)

      txListBin = hex_to_binary(dpser) 
      binUnpacker = BinaryUnpacker(txListBin)
      txList = []
      targetTx = PyTx().unserialize(binUnpacker)
      while binUnpacker.getRemainingSize() > 0:
         nextTx = PyTx().unserialize(binUnpacker)
         self.relevantTxMap[nextTx.getHash()] = nextTx

      for txin in targetTx.inputs:
         if not self.relevantTxMap.has_key(txin.outpoint.txHash):
            raise TxdpError, 'Not all inputs can be verified for TxDP.  Aborting!'

      self.createFromPyTx( targetTx, self.relevantTxMap )
      numIn = len(self.pytxObj.inputs)

      # Do some sanity checks
      if not self.uniqueB58 == dpIdB58:
         raise UnserializeError, 'TxDP: Actual DPID does not match listed ID'
      if not MAGIC_BYTES==magic:
         raise NetworkIDError, 'TxDP is for diff blockchain! (%s)' % \
                                                         BLOCKCHAINS[magic]

      # At this point, we should have a TxDP constructed, now we need to 
      # simply scan the rest of the serialized structure looking for any
      # signatures that may be included
      while not 'END-TRANSACTION' in line: 
         [iin, val] = line.split('_')[2:]
         iin = int(iin)
         self.inputValues[iin] = str2coin(val)
         
         line = nextLine(L)
         while '_SIG_' in line:
            addrB58, sz, sigszHex = line.split('_')[2:]
            sz = int(sz) 
            sigsz = hex_to_int(sigszHex, endIn=BIGENDIAN)
            hexSig = ''
            line = nextLine(L)
            while (not '_SIG_' in line)   and \
                  (not 'TXINPUT' in line) and \
                  (not 'END-TRANSACTION' in line):
               hexSig += line
               line = nextLine(L)
            binSig = hex_to_binary(hexSig)
            idx, sigOrder, addr160 = self.processSignature(binSig, iin)
            if idx == -1:
               LOGWARN('Invalid sig: Input %d, addr=%s' % (iin, addrB58))
            elif not hash160_to_addrStr(addr160)== addrB58:
               LOGERROR('Listed addr does not match computed addr')
               raise BadAddressError 
            # If we got here, the signature is valid!
            self.signatures[iin][sigOrder] = binSig

      return self
      


   #############################################################################
   def pprint(self, indent='   '):
      tx = self.pytxObj
      propID = hash256(tx.serialize())
      print indent+'Distribution Proposal : ', binary_to_base58(propID)[:8]
      print indent+'Transaction Version   : ', tx.version
      print indent+'Transaction Lock Time : ', tx.lockTime
      print indent+'Num Inputs            : ', len(tx.inputs)
      for i,txin in enumerate(tx.inputs):
         prevHash = txin.outpoint.txHash
         prevIndex = txin.outpoint.txOutIndex
         #print '   PrevOut: (%s, index=%d)' % (binary_to_hex(prevHash[:8]),prevIndex),
         print indent*2 + 'Value: %s' % self.inputValues[i]
         print indent*2 + 'SrcScript:   %s' % binary_to_hex(self.txOutScripts[i])
         for ns, sig in enumerate(self.signatures[i]):
            print indent*2 + 'Sig%d = "%s"'%(ns, binary_to_hex(sig))
      print indent+'Num Outputs           : ', len(tx.outputs)
      for i,txout in enumerate(tx.outputs):
         print '   Recipient: %s BTC' % coin2str(txout.value),
         scrType = getTxOutScriptType(txout.binScript)
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            print hash160_to_addrStr(TxOutScriptExtractAddr160(txout.binScript))
         elif scrType in (TXOUT_SCRIPT_MULTISIG,):
            mstype, addrs, pubs = getTxOutMultiSigInfo(txout.binScript)
            print 'MULTI-SIG-SCRIPT:%d-of-%d' % mstype
            for addr in addrs:
               print indent*2, hash160_to_addrStr(addr)
            
         

# Random method for creating
def touchFile(fname):
   try:
      os.utime(fname, None)
   except:
      f = open(fname, 'a')
      f.flush()
      os.fsync(f.fileno())
      f.close()

BLOCKCHAIN_READONLY   = 0
BLOCKCHAIN_READWRITE  = 1
BLOCKCHAIN_DONOTUSE   = 2

WLT_UPDATE_ADD = 0
WLT_UPDATE_MODIFY = 1

WLT_DATATYPE_KEYDATA     = 0
WLT_DATATYPE_ADDRCOMMENT = 1
WLT_DATATYPE_TXCOMMENT   = 2
WLT_DATATYPE_OPEVAL      = 3
WLT_DATATYPE_DELETED     = 4

DEFAULT_COMPUTE_TIME_TARGET = 0.25
DEFAULT_MAXMEM_LIMIT        = 32*1024*1024



################################################################################
################################################################################
class PyBtcWallet(object):
   """
   This class encapsulates all the concepts and variables in a "wallet",
   and maintains the passphrase protection, key stretching, encryption,
   etc, required to maintain the wallet.  This class also includes the
   file I/O methods for storing and loading wallets.

   ***NOTE:  I have ONLY implemented deterministic wallets, using ECDSA
             Diffie-Hellman shared-secret crypto operations.  This allows
             one to actually determine the next PUBLIC KEY in the address
             chain without actually having access to the private keys.
             This makes it possible to synchronize online-offline computers
             once and never again.

             You can import random keys into your wallet, but if it is
             encrypted, you will have to supply a passphrase to make sure
             it can be encrypted as well.

   Presumably, wallets will be used for one of three purposes:

   (1) Spend money and receive payments
   (2) Watching-only wallets - have the private keys, just not on this computer
   (3) May be watching *other* people's addrs.  There's a variety of reasons
       we might want to watch other peoples' addresses, but most them are not
       relevant to a "basic" BTC user.  Nonetheless it should be supported to
       watch money without considering it part of our own assets

   This class is included in the combined-python-cpp module, because we really
   need to maintain a persistent Cpp.BtcWallet if this class is to be useful
   (we don't want to have to rescan the entire blockchain every time we do any
   wallet operations).

   The file format was designed from the outset with lots of unused space to
   allow for expansion without having to redefine the file format and break
   previous wallets.  Luckily, wallet information is cheap, so we don't have
   to stress too much about saving space (100,000 addresses should take 15 MB)

   This file is NOT for storing Tx-related information.  I want this file to
   be the minimal amount of information you need to secure and backup your
   entire wallet.  Tx information can always be recovered from examining the
   blockchain... your private keys cannot be.

   We track version numbers, just in case.  We start with 1.0

   Version 1.0:
   ---
   fileID      -- (8)  '\xbaWALLET\x00' for wallet files
   version     -- (4)   getVersionInt(PYBTCWALLET_VERSION)
   magic bytes -- (4)   defines the blockchain for this wallet (BTC, NMC)
   wlt flags   -- (8)   64 bits/flags representing info about wallet
   binUniqueID -- (6)   first 5 bytes of first address in wallet
                        (rootAddr25Bytes[:5][::-1]), reversed
                        This is not intended to look like the root addr str
                        and is reversed to avoid having all wallet IDs start 
                        with the same characters (since the network byte is front)
   create date -- (8)   unix timestamp of when this wallet was created
                        (actually, the earliest creation date of any addr
                        in this wallet -- in the case of importing addr
                        data).  This is used to improve blockchain searching
   Short Name  -- (32)  Null-terminated user-supplied short name for wlt
   Long Name   -- (256) Null-terminated user-supplied description for wlt
   Highest Used-- (8)   The chain index of the highest used address
   ---
   Crypto/KDF  -- (512) information identifying the types and parameters
                        of encryption used to secure wallet, and key
                        stretching used to secure your passphrase.
                        Includes salt. (the breakdown of this field will
                        be described separately)
   KeyGenerator-- (237) The base address for a determinstic wallet.
                        Just a serialized PyBtcAddress object.
   ---
   UNUSED     -- (1024) unused space for future expansion of wallet file
   ---
   Remainder of file is for key storage and various other things.  Each
   "entry" will start with a 4-byte code identifying the entry type, then
   20 bytes identifying what address the data is for, and finally then
   the subsequent data .  So far, I have three types of entries that can
   be included:

      \x01 -- Address/Key data (as of PyBtcAddress version 1.0, 237 bytes)
      \x02 -- Address comments (variable-width field)
      \x03 -- Address comments (variable-width field)
      \x04 -- OP_EVAL subscript (when this is enabled, in the future)

   Please see PyBtcAddress for information on how key data is serialized.
   Comments (\x02) are var-width, and if a comment is changed to
   something longer than the existing one, we'll just blank out the old
   one and append a new one to the end of the file.  It looks like

   02000000 01 <Addr> 4f This comment is enabled (01) with 4f characters


   For file syncing, we protect against corrupted wallets by doing atomic
   operations before even telling the user that new data has been added.
   We do this by copying the wallet file, and creating a walletUpdateFailed
   file.  We then modify the original, verify its integrity, and then delete
   the walletUpdateFailed file.  Then we create a backupUpdateFailed flag,
   do the identical update on the backup file, and delete the failed flag. 
   This guaranatees that no matter which nanosecond the power goes out,
   there will be an uncorrupted wallet and we know which one it is.

   We never let the user see any data until the atomic write-to-file operation
   has completed


   Additionally, we implement key locking and unlocking, with timeout.  These
   key locking features are only DEFINED here, not actually enforced (because
   this is a library, not an application).  You can set the default/temporary
   time that the KDF key is maintained in memory after the passphrase is
   entered, and this class will keep track of when the wallet should be next
   locked.  It is up to the application to check whether the current time
   exceeds the lock time.  This will probably be done in a kind of heartbeat
   method, which checks every few seconds for all sorts of things -- including
   wallet locking.
   """

   #############################################################################
   def __init__(self):
      self.fileTypeStr    = '\xbaWALLET\x00'
      self.magicBytes     = MAGIC_BYTES
      self.version        = PYBTCWALLET_VERSION  # (Major, Minor, Minor++, even-more-minor)
      self.eofByte        = 0
      self.cppWallet      = None   # Mirror of PyBtcWallet in C++ object
      self.cppInfo        = {}     # Extra info about each address to help sync
      self.watchingOnly   = False
      self.wltCreateDate  = 0

      # Three dictionaries hold all data
      self.addrMap     = {}  # maps 20-byte addresses to PyBtcAddress objects
      self.commentsMap = {}  # maps 20-byte addresses to user-created comments
      self.commentLocs = {}  # map comment keys to wallet file locations
      self.opevalMap   = {}  # maps 20-byte addresses to OP_EVAL data (future)
      self.labelName   = ''
      self.labelDescr  = ''
      self.linearAddr160List = []
      self.chainIndexMap = {}
      if USE_TESTNET:
         self.addrPoolSize = 10  # this makes debugging so much easier!
      else:
         self.addrPoolSize = 100

      # For file sync features
      self.walletPath = ''
      self.doBlockchainSync = BLOCKCHAIN_READONLY
      self.lastSyncBlockNum = 0

      # Private key encryption details
      self.useEncryption  = False
      self.kdf            = None
      self.crypto         = None
      self.kdfKey         = None
      self.defaultKeyLifetime = 10    # seconds after unlock, that key is discarded
      self.lockWalletAtTime   = 0    # seconds after unlock, that key is discarded
      self.isLocked       = False
      self.testedComputeTime=None

      # Deterministic wallet, need a root key.  Though we can still import keys.
      # The unique ID contains the network byte (id[-1]) but is not intended to
      # resemble the address of the root key
      self.uniqueIDBin = ''
      self.uniqueIDB58 = ''   # Base58 version of reversed-uniqueIDBin
      self.lastComputedChainAddr160  = ''
      self.lastComputedChainIndex = 0
      self.highestUsedChainIndex  = 0 

      # All PyBtcAddress serializations are exact same size, figure it out now
      self.pybtcaddrSize = len(PyBtcAddress().serialize())


      # Finally, a bunch of offsets that tell us where data is stored in the
      # file: this can be generated automatically on unpacking (meaning it
      # doesn't require manually updating offsets if I change the format), and
      # will save us a couple lines of code later, when we need to update things
      self.offsetWltFlags  = -1
      self.offsetLabelName = -1
      self.offsetLabelDescr  = -1
      self.offsetTopUsed   = -1
      self.offsetRootAddr  = -1
      self.offsetKdfParams = -1
      self.offsetCrypto    = -1

      # These flags are ONLY for unit-testing the walletFileSafeUpdate function
      self.interruptTest1  = False
      self.interruptTest2  = False
      self.interruptTest3  = False

   #############################################################################
   def getWalletVersion(self):
      return (getVersionInt(self.version), getVersionString(self.version))

   #############################################################################
   def getWalletVersion(self):
      return (getVersionInt(self.version), getVersionString(self.version))


   #############################################################################
   def getWalletPath(self):
      return self.walletPath

   #############################################################################
   def getTimeRangeForAddress(self, addr160):
      if not self.addrMap.has_key(addr160):
         return None
      else:
          return self.addrMap[addr160].getTimeRange()

   #############################################################################
   def getBlockRangeForAddress(self, addr20):
      if not self.addrMap.has_key(addr160):
         return None
      else:
          return self.addrMap[addr160].getBlockRange()

   #############################################################################
   def setBlockchainSyncFlag(self, syncYes=True):
      self.doBlockchainSync = syncYes

   #############################################################################
   def syncWithBlockchain(self, startBlk=None):
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         assert(TheBDM.isInitialized())
         if startBlk==None:
            startBlk = self.lastSyncBlockNum + 1
         TheBDM.scanBlockchainForTx(self.cppWallet, startBlk)
         self.lastSyncBlockNum = TheBDM.getTopBlockHeader().getBlockHeight()
      else:
         LOGERROR('Blockchain-sync requested, but current wallet')
         LOGERROR('is set to BLOCKCHAIN_DONOTUSE')






   #############################################################################
   def getCommentForAddrBookEntry(self, abe):
      comment = self.getComment(abe.getAddr160())
      if len(comment)>0:
         return comment

      for regTx in abe.getTxList():
         comment = self.getComment(regTx.getTxHash())
         if len(comment)>0:
            return comment

      return ''
      
   #############################################################################
   def printAddressBook(self):
      addrbook = self.cppWallet.createAddressBook()
      for abe in addrbook:
         print hash160_to_addrStr(abe.getAddr160()),
         txlist = abe.getTxList()
         print len(txlist)
         for rtx in txlist:
            print '\t', binary_to_hex(rtx.getTxHash(), BIGENDIAN)
         

   #############################################################################
   def getBalance(self, balType="Spendable"):
      if not TheBDM.isInitialized():
         return -1
      else:
         currBlk = TheBDM.getTopBlockHeader().getBlockHeight()
         if balType.lower() in ('spendable','spend'):
            return self.cppWallet.getSpendableBalance(currBlk)
         elif balType.lower() in ('unconfirmed','unconf'):
            return self.cppWallet.getUnconfirmedBalance(currBlk)
         elif balType.lower() in ('total','ultimate','unspent','full'):
            return self.cppWallet.getFullBalance()
         else:
            raise TypeError, 'Unknown balance type! "' + balType + '"'


   #############################################################################
   def getAddrBalance(self, addr160, balType="Spendable", currBlk=UINT32_MAX):
      if not TheBDM.isInitialized() or not self.hasAddr(addr160):
         return -1
      else:
         addr = self.cppWallet.getAddrByHash160(addr160)
         if balType.lower() in ('spendable','spend'):
            return addr.getSpendableBalance(currBlk)
         elif balType.lower() in ('unconfirmed','unconf'):
            return addr.getUnconfirmedBalance(currBlk)
         elif balType.lower() in ('ultimate','unspent','full'):
            return addr.getFullBalance()
         else:
            raise TypeError, 'Unknown balance type!'

   #############################################################################
   def getTxLedger(self, ledgType='Full'):
      """ 
      Gets the ledger entries for the entire wallet, from C++/SWIG data structs
      """
      if not TheBDM.isInitialized():
         return []
      else:
         ledgBlkChain = self.cppWallet.getTxLedger()
         ledgZeroConf = self.cppWallet.getZeroConfLedger()
         if ledgType.lower() in ('full','all','ultimate'):
            ledg = []
            ledg.extend(ledgBlkChain)
            ledg.extend(ledgZeroConf)
            return ledg
         elif ledgType.lower() in ('blk', 'blkchain', 'blockchain'):
            return ledgBlkChain
         elif ledgType.lower() in ('zeroconf', 'zero'):
            return ledgZeroConf
         else:
            raise TypeError, 'Unknown ledger type! "' + ledgType + '"'




   #############################################################################
   def getAddrTxLedger(self, addr160, ledgType='Full'):
      """ 
      Gets the ledger entries for the entire wallet, from C++/SWIG data structs
      """
      if not TheBDM.isInitialized() or not self.hasAddr(addr160):
         return []
      else:
         ledgBlkChain = self.cppWallet.getAddrByHash160(addr160).getTxLedger()
         ledgZeroConf = self.cppWallet.getAddrByHash160(addr160).getZeroConfLedger()
         if ledgType.lower() in ('full','all','ultimate'):
            ledg = []
            ledg.extend(ledgBlkChain)
            ledg.extend(ledgZeroConf)
            return ledg
         elif ledgType.lower() in ('blk', 'blkchain', 'blockchain'):
            return ledgBlkChain
         elif ledgType.lower() in ('zeroconf', 'zero'):
            return ledgZeroConf
         else:
            raise TypeError, 'Unknown balance type! "' + ledgType + '"'


   #############################################################################
   def getTxOutList(self, txType='Spendable'):
      """ Returns UnspentTxOut/C++ objects """
      if TheBDM.isInitialized() and not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         currBlk = TheBDM.getTopBlockHeader().getBlockHeight()
         self.syncWithBlockchain()
         if txType.lower() in ('spend', 'spendable'):
            return self.cppWallet.getSpendableTxOutList(currBlk);
         elif txType.lower() in ('full', 'all', 'unspent', 'ultimate'):
            return self.cppWallet.getFullTxOutList(currBlk);
         else:
            raise TypeError, 'Unknown balance type! ' + txType
      else:
         LOGERROR('***Blockchain is not available for accessing wallet-tx data')
         return []

   #############################################################################
   def getAddrTxOutList(self, addr160, txType='Spendable'):
      """ Returns UnspentTxOut/C++ objects """
      if TheBDM.isInitialized() and self.hasAddr(addr160) and \
                        not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         currBlk = TheBDM.getTopBlockHeader().getBlockHeight()
         self.syncWithBlockchain()
         if txType.lower() in ('spend', 'spendable'):
            return self.cppWallet.getAddrByHash160(addr160).getSpendableTxOutList(currBlk);
         elif txType.lower() in ('full', 'all', 'unspent', 'ultimate'):
            return self.cppWallet.getAddrByHash160(addr160).getFullTxOutList(currBlk);
         else:
            raise TypeError, 'Unknown TxOutList type! ' + txType
      else:
         LOGERROR('***Blockchain is not available for accessing wallet-tx data')
         return []


   #############################################################################
   def getAddrByHash160(self, addr160):
      return (None if not self.hasAddr(addr160) else self.addrMap[addr160])

   #############################################################################
   def hasAddr(self, addrData):
      if isinstance(addrData, str):
         if len(addrData) == 20:
            return self.addrMap.has_key(addrData)
         elif isLikelyDataType(addrData)==DATATYPE.Base58:
            return self.addrMap.has_key(addrStr_to_hash160(addrData))
         else:
            return False
      elif isinstance(addrData, PyBtcAddress):
         return self.addrMap.has_key(addrData.getAddr160())
      else:
         return False


   #############################################################################
   def setDefaultKeyLifetime(self, newlifetime):
      """ Set a new default lifetime for holding the unlock key. Min 2 sec """
      self.defaultKeyLifetime = max(newlifetime, 2)

   #############################################################################
   def checkWalletLockTimeout(self):
      if not self.isLocked and self.kdfKey and RightNow()>self.lockWalletAtTime:
         self.lock()
         if self.kdfKey:
            self.kdfKey.destroy()
         self.kdfKey = None

         if self.useEncryption:
            self.isLocked = True



   #############################################################################
   def lockTxOutsOnNewTx(self, pytxObj):
      for txin in pytxObj.inputs:
         self.cppWallet.lockTxOutSwig(txin.outpoint.txHash, txin.outpoint.txOutIndex)
         
   

   #############################################################################
   def setDefaultKeyLifetime(self, lifetimeInSec):
      """
      This is used to set (in memory only) the default time to keep the encrypt
      key in memory after the encryption passphrase has been entered.  This is
      NOT enforced by PyBtcWallet, but the unlock method will use it to calc a
      unix timestamp when the wallet SHOULD be locked, and the external program
      can use that to decide when to call the lock method.
      """
      self.defaultKeyLifetime = lifetimeInSec

   #############################################################################
   def createNewWallet(self, newWalletFilePath=None, \
                             plainRootKey=None, chaincode=None, \
                             withEncrypt=True, IV=None, securePassphrase=None, \
                             kdfTargSec=DEFAULT_COMPUTE_TIME_TARGET, \
                             kdfMaxMem=DEFAULT_MAXMEM_LIMIT, \
                             shortLabel='', longLabel='', isActuallyNew=True):
      """
      This method will create a new wallet, using as much customizability
      as you want.  You can enable encryption, and set the target params
      of the key-derivation function (compute-time and max memory usage).
      The KDF parameters will be experimentally determined to be as hard
      as possible for your computer within the specified time target
      (default, 0.25s).  It will aim for maximizing memory usage and using
      only 1 or 2 iterations of it, but this can be changed by scaling
      down the kdfMaxMem parameter (default 32 MB).

      If you use encryption, don't forget to supply a 32-byte passphrase,
      created via SecureBinaryData(pythonStr).  This method will apply
      the passphrase so that the wallet is "born" encrypted.

      The field plainRootKey could be used to recover a written backup
      of a wallet, since all addresses are deterministically computed
      from the root address.  This obviously won't reocver any imported
      keys, but does mean that you can recover your ENTIRE WALLET from
      only those 32 plaintext bytes AND the 32-byte chaincode.

      We skip the atomic file operations since we don't even have
      a wallet file yet to safely update.
      """

      if securePassphrase:
         securePassphrase = SecureBinaryData(securePassphrase)
      if plainRootKey:
         plainRootKey = SecureBinaryData(plainRootKey)
      if chaincode:
         chaincode = SecureBinaryData(chaincode)

      if withEncrypt and not securePassphrase:
         raise EncryptionError, 'Cannot create encrypted wallet without passphrase'

      LOGINFO('***Creating new deterministic wallet')

      # Set up the KDF
      if not withEncrypt:
         self.kdfKey = None
      else:
         LOGINFO('(with encryption)')
         self.kdf = KdfRomix()
         LOGINFO('Target (time,RAM)=(%0.3f,%d)', kdfTargSec, kdfMaxMem)
         (mem,niter,salt) = self.computeSystemSpecificKdfParams( \
                                                kdfTargSec, kdfMaxMem)
         self.kdf.usePrecomputedKdfParams(mem, niter, salt)
         self.kdfKey = self.kdf.DeriveKey(securePassphrase)

      if not plainRootKey:
         # TODO: We should find a source for injecting extra entropy
         #       At least, Crypto++ grabs from a few different sources, itself
         plainRootKey = SecureBinaryData().GenerateRandom(32)

      if not chaincode:
         chaincode = SecureBinaryData().GenerateRandom(32)

      # Create the root address object
      rootAddr = PyBtcAddress().createFromPlainKeyData( \
                                             plainRootKey, \
                                             IV16=IV, \
                                             willBeEncr=withEncrypt, \
                                             generateIVIfNecessary=True)
      rootAddr.markAsRootAddr(chaincode)

      # This does nothing if no encryption
      rootAddr.lock(self.kdfKey)
      rootAddr.unlock(self.kdfKey)

      firstAddr = rootAddr.extendAddressChain(self.kdfKey)
      first160  = firstAddr.getAddr160()

      # Update wallet object with the new data
      # NEW IN WALLET VERSION 1.35:  unique ID is now based on
      # the first chained address: this guarantees that the unique ID
      # is based not only on the private key, BUT ALSO THE CHAIN CODE
      self.useEncryption = withEncrypt
      self.addrMap['ROOT'] = rootAddr
      self.addrMap[firstAddr.getAddr160()] = firstAddr
      self.uniqueIDBin = (ADDRBYTE + firstAddr.getAddr160()[:5])[::-1]
      self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)
      self.labelName  = shortLabel[:32]
      self.labelDescr  = longLabel[:256]
      self.lastComputedChainAddr160 = first160
      self.lastComputedChainIndex  = firstAddr.chainIndex
      self.highestUsedChainIndex   = firstAddr.chainIndex-1
      self.wltCreateDate = long(RightNow())
      self.linearAddr160List = [first160]
      self.chainIndexMap[firstAddr.chainIndex] = first160

      # We don't have to worry about atomic file operations when
      # creating the wallet: so we just do it naively here.
      self.walletPath = newWalletFilePath
      if not newWalletFilePath:
         shortName = self.labelName .replace(' ','_')
         # This was really only needed when we were putting name in filename
         #for c in ',?;:\'"?/\\=+-|[]{}<>':
            #shortName = shortName.replace(c,'_')
         newName = 'armory_%s_.wallet' % self.uniqueIDB58
         self.walletPath = os.path.join(ARMORY_HOME_DIR, newName)

      LOGINFO('   New wallet will be written to: %s', self.walletPath)
      newfile = open(self.walletPath, 'wb')
      fileData = BinaryPacker()

      # packHeader method writes KDF params and root address
      headerBytes = self.packHeader(fileData)

      # We make sure we have byte locations of the two addresses, to start
      self.addrMap[first160].walletByteLoc = headerBytes + 21

      fileData.put(BINARY_CHUNK, '\x00' + first160 + firstAddr.serialize())


      # Store the current localtime and blocknumber.  Block number is always 
      # accurate if available, but time may not be exactly right.  Whenever 
      # basing anything on time, please assume that it is up to one day off!
      time0,blk0 = getCurrTimeAndBlock() if isActuallyNew else (0,0)

      # Don't forget to sync the C++ wallet object
      self.cppWallet = Cpp.BtcWallet()
      self.cppWallet.addAddress_5_(rootAddr.getAddr160(), time0,blk0,time0,blk0)
      self.cppWallet.addAddress_5_(first160,              time0,blk0,time0,blk0)
      TheBDM.registerWallet(self.cppWallet, True) # new wallet


      newfile.write(fileData.getBinaryString())
      newfile.close()

      walletFileBackup = self.getWalletPath('backup')
      shutil.copy(self.walletPath, walletFileBackup)

      # Let's fill the address pool while we have the KDF key in memory.
      # It will get a lot more expensive if we do it on the next unlock
      self.fillAddressPool(self.addrPoolSize, isActuallyNew=isActuallyNew)

      if self.useEncryption:
         self.unlock(secureKdfOutput=self.kdfKey)
         self.lock()
      return self

   #############################################################################
   def advanceHighestIndex(self, ct=1):
      topIndex = self.highestUsedChainIndex + ct
      topIndex = min(topIndex, self.lastComputedChainIndex)
      topIndex = max(topIndex, 0)

      self.highestUsedChainIndex = topIndex
      self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, self.offsetTopUsed, \
                    int_to_binary(self.highestUsedChainIndex, widthBytes=8)]])
      self.fillAddressPool()
      
   #############################################################################
   def rewindHighestIndex(self, ct=1):
      self.advanceHighestIndex(-ct)


   #############################################################################
   def peekNextUnusedAddr160(self):
      try:
         return self.getAddress160ByChainIndex(self.highestUsedChainIndex+1)
      except:
         # Not sure why we'd fail, maybe addrPoolSize==0?
         return ''

   #############################################################################
   def getNextUnusedAddress(self):
      if self.lastComputedChainIndex - self.highestUsedChainIndex < \
                                              max(self.addrPoolSize-1,1):
         self.fillAddressPool(self.addrPoolSize)

      self.advanceHighestIndex(1)
      new160 = self.getAddress160ByChainIndex(self.highestUsedChainIndex)
      self.addrMap[new160].touch()
      self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, \
                                  self.addrMap[new160].walletByteLoc, \
                                  self.addrMap[new160].serialize()]]  )
      return self.addrMap[new160]


   #############################################################################
   def computeNextAddress(self, addr160=None, isActuallyNew=True):
      """
      Use this to extend the chain beyond the last-computed address.

      We will usually be computing the next address from the tip of the 
      chain, but I suppose someone messing with the file format may
      leave gaps in the chain requiring some to be generated in the middle
      (then we can use the addr160 arg to specify which address to extend)
      """
      if not addr160:
         addr160 = self.lastComputedChainAddr160

      newAddr = self.addrMap[addr160].extendAddressChain(self.kdfKey)
      new160 = newAddr.getAddr160()
      newDataLoc = self.walletFileSafeUpdate( \
         [[WLT_UPDATE_ADD, WLT_DATATYPE_KEYDATA, new160, newAddr]])
      self.addrMap[new160] = newAddr
      self.addrMap[new160].walletByteLoc = newDataLoc[0] + 21

      if newAddr.chainIndex > self.lastComputedChainIndex:
         self.lastComputedChainAddr160 = new160
         self.lastComputedChainIndex = newAddr.chainIndex

      self.linearAddr160List.append(new160)
      self.chainIndexMap[newAddr.chainIndex] = new160

      # In the future we will enable first/last seen, but not yet
      time0,blk0 = getCurrTimeAndBlock() if isActuallyNew else (0,0)
      self.cppWallet.addAddress_5_(new160, time0,blk0,time0,blk0)
      return new160
      



   #############################################################################
   def fillAddressPool(self, numPool=None, isActuallyNew=True):
      if not numPool:
         numPool = self.addrPoolSize

      gap = self.lastComputedChainIndex - self.highestUsedChainIndex
      numToCreate = max(numPool - gap, 0)
      for i in range(numToCreate):
         self.computeNextAddress(isActuallyNew=isActuallyNew)
      return self.lastComputedChainIndex

   #############################################################################
   def setAddrPoolSize(self, newSize):
      if newSize<5:
         LOGERROR('Will not allow address pool sizes smaller than 5...')
         return

      self.addrPoolSize = newSize
      self.fillAddressPool(newSize)


   #############################################################################
   def getHighestUsedIndex(self):
      """ 
      This only retrieves the stored value, but it may not be correct if,
      for instance, the wallet was just imported but has been used before.
      """
      return self.highestUsedChainIndex

          
   #############################################################################
   def getHighestComputedIndex(self):
      """ 
      This only retrieves the stored value, but it may not be correct if,
      for instance, the wallet was just imported but has been used before.
      """
      return self.lastComputedChainIndex
      

         
   #############################################################################
   def detectHighestUsedIndex(self, writeResultToWallet=False):
      """
      This method is used to find the highestUsedChainIndex value of the 
      wallet WITHIN its address pool.  It will NOT extend its address pool
      in this search, because it is assumed that the wallet couldn't have
      used any addresses it had not calculated yet.

      If you have a wallet IMPORT, though, or a wallet that has been used
      before but does not have this information stored with it, then you
      should be using the next method:

            self.freshImportFindHighestIndex()

      which will actually extend the address pool as necessary to find the
      highest address used.      
      """
      if not TheBDM.isInitialized():
         LOGERROR('Cannot detect any usage information without the blockchain')
         return -1

      oldSync = self.doBlockchainSync
      self.doBlockchainSync = BLOCKCHAIN_READONLY
      self.syncWithBlockchain(0)  # make sure we're always starting from blk 0
      self.doBlockchainSync = oldSync

      highestIndex = 0
      for addr in self.getLinearAddrList(withAddrPool=True):
         a160 = addr.getAddr160()
         if len(self.getAddrTxLedger(a160)) > 0:
            highestIndex = max(highestIndex, addr.chainIndex)

      if writeResultToWallet:
         self.highestUsedChainIndex = highestIndex
         self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, self.offsetTopUsed, \
                                      int_to_binary(highestIndex, widthBytes=8)]])


      return highestIndex


   #############################################################################
   def freshImportFindHighestIndex(self, stepSize=None):
      """ 
      This is much like detectHighestUsedIndex, except this will extend the
      address pool as necessary.  It assumes that you have a fresh wallet
      that has been used before, but was deleted and restored from its root
      key and chaincode, and thus we don't know if only 10 or 10,000 addresses
      were used.

      If this was an exceptionally active wallet, it's possible that we
      may need to manually increase the step size to be sure we find  
      everything.  In fact, there is no way to tell FOR SURE what is the
      last addressed used: one must make an assumption that the wallet 
      never calculated more than X addresses without receiving a payment...
      """
      if not stepSize:
         stepSize = self.addrPoolSize

      topCompute = 0
      topUsed    = 0
      oldPoolSize = self.addrPoolSize
      self.addrPoolSize = stepSize
      # When we hit the highest address, the topCompute value will extend
      # out [stepsize] addresses beyond topUsed, and the topUsed will not
      # change, thus escaping the while loop
      nWhile = 0
      while topCompute - topUsed < 0.9*stepSize:
         topCompute = self.fillAddressPool(stepSize, isActuallyNew=False)
         topUsed = self.detectHighestUsedIndex(True)
         nWhile += 1
         if nWhile>10000:
            raise WalletAddressError, 'Escaping inf loop in freshImport...'
            

      self.addrPoolSize = oldPoolSize
      return topUsed


   #############################################################################
   def writeFreshWalletFile(self, path, newName='', newDescr=''):
      newFile = open(path, 'wb')
      bp = BinaryPacker()
      self.packHeader(bp)
      newFile.write(bp.getBinaryString())

      for addr160,addrObj in self.addrMap.iteritems():
         if not addr160=='ROOT':
            newFile.write('\x00' + addr160 + addrObj.serialize())

      for hashVal,comment in self.commentsMap.iteritems():
         twoByteLength = int_to_binary(len(comment), widthBytes=2)
         if len(hashVal)==20:
            typestr = int_to_binary(WLT_DATATYPE_ADDRCOMMENT)
            newFile.write(typestr + hashVal + twoByteLength + comment)
         elif len(hashVal)==32:
            typestr = int_to_binary(WLT_DATATYPE_TXCOMMENT)
            newFile.write(typestr + hashVal + twoByteLength + comment)

      for addr160,opevalData in self.opevalMap.iteritems():
         pass

      newFile.close()
   

   #############################################################################
   def forkOnlineWallet(self, newWalletFile, shortLabel='', longLabel=''):
      """
      Make a copy of this wallet that contains no private key data
      """
      if not self.addrMap['ROOT'].hasPrivKey():
         LOGWARN('This wallet is already void of any private key data!')
         LOGWARN('Aborting wallet fork operation.')

      onlineWallet = PyBtcWallet()
      onlineWallet.fileTypeStr = self.fileTypeStr
      onlineWallet.version = self.version
      onlineWallet.magicBytes = self.magicBytes
      onlineWallet.wltCreateDate = self.wltCreateDate
      onlineWallet.useEncryption = False
      onlineWallet.watchingOnly = True

      if not shortLabel:
         shortLabel = self.labelName
      if not longLabel:
         longLabel = self.labelDescr

      onlineWallet.labelName  = (shortLabel + ' (Watch)')[:32]
      onlineWallet.labelDescr = (longLabel + ' (Watching-only copy)')[:256]

      newAddrMap = {}
      for addr160,addrObj in self.addrMap.iteritems():
         onlineWallet.addrMap[addr160] = addrObj.copy()
         onlineWallet.addrMap[addr160].binPrivKey32_Encr  = SecureBinaryData()
         onlineWallet.addrMap[addr160].binPrivKey32_Plain = SecureBinaryData()
         onlineWallet.addrMap[addr160].useEncryption = False
         onlineWallet.addrMap[addr160].createPrivKeyNextUnlock = False

      onlineWallet.commentsMap = self.commentsMap
      onlineWallet.opevalMap = self.opevalMap

      onlineWallet.uniqueIDBin = self.uniqueIDBin
      onlineWallet.highestUsedChainIndex     = self.highestUsedChainIndex
      onlineWallet.lastComputedChainAddr160  = self.lastComputedChainAddr160
      onlineWallet.lastComputedChainIndex    = self.lastComputedChainIndex

      onlineWallet.writeFreshWalletFile(newWalletFile, shortLabel, longLabel)
      return onlineWallet


   #############################################################################
   def supplyRootKeyForWatchingOnlyWallet(self, securePlainRootKey32, \
                                                permanent=False):
      """
      If you have a watching only wallet, you might want to upgrade it to a
      full wallet by supplying the 32-byte root private key.  Generally, this
      will be used to make a 'permanent' upgrade to your wallet, and the new
      keys will be written to file ( NOTE:  you should setup encryption just
      after doing this, to make sure that the plaintext keys get wiped from
      your wallet file).

      On the other hand, if you don't want this to be a permanent upgrade,
      this could potentially be used to maintain a watching only wallet on your
      harddrive, and actually plug in your plaintext root key instead of an
      encryption password whenever you want sign transactions. 
      """
      pass


   #############################################################################
   def touchAddress(self, addr20):
      """
      Use this to update your wallet file to recognize the first/last times
      seen for the address.  This information will improve blockchain search
      speed, if it knows not to search transactions that happened before they
      were created.
      """
      pass

   #############################################################################
   def testKdfComputeTime(self):
      """
      Experimentally determines the compute time required by this computer
      to execute with the current key-derivation parameters.  This may be
      useful for when you transfer a wallet to a new computer that has
      different speed/memory characteristic.
      """
      if self.testedComputeTime==None:
         testPassphrase = SecureBinaryData('This is a simple passphrase')
         start = RightNow()
         self.kdf.DeriveKey(testPassphrase)
         self.testedComputeTime = (RightNow()-start)
      return self.testedComputeTime

   #############################################################################
   def serializeKdfParams(self, kdfObj=None, binWidth=256):
      """
      Pack key-derivation function parameters into a binary stream.
      As of wallet version 1.0, there is only one KDF technique used
      in these wallets, and thus we only need to store the parameters
      of this KDF.  In the future, we may have multiple KDFs and have
      to store the selection in this serialization.
      """
      if not kdfObj:
         kdfObj = self.kdf

      if not kdfObj:
         return '\x00'*binWidth

      binPacker = BinaryPacker()
      binPacker.put(UINT64, kdfObj.getMemoryReqtBytes())
      binPacker.put(UINT32, kdfObj.getNumIterations())
      binPacker.put(BINARY_CHUNK, kdfObj.getSalt().toBinStr(), width=32)

      kdfStr = binPacker.getBinaryString()
      binPacker.put(BINARY_CHUNK, computeChecksum(kdfStr,4), width=4)
      padSize = binWidth - binPacker.getSize()
      binPacker.put(BINARY_CHUNK, '\x00'*padSize)

      return binPacker.getBinaryString()



   #############################################################################
   def unserializeKdfParams(self, toUnpack, binWidth=256):

      if isinstance(toUnpack, BinaryUnpacker):
         binUnpacker = toUnpack
      else:
         binUnpacker = BinaryUnpacker(toUnpack)



      allKdfData = binUnpacker.get(BINARY_CHUNK, 44)
      kdfChksum  = binUnpacker.get(BINARY_CHUNK,  4)
      kdfBytes   = len(allKdfData) + len(kdfChksum)
      padding    = binUnpacker.get(BINARY_CHUNK, binWidth-kdfBytes)

      if allKdfData=='\x00'*44:
         return None

      fixedKdfData = verifyChecksum(allKdfData, kdfChksum)
      if len(fixedKdfData)==0:
         raise UnserializeError, 'Corrupted KDF params, could not fix'
      elif not fixedKdfData==allKdfData:
         self.walletFileSafeUpdate( \
               [[WLT_UPDATE_MODIFY, self.offsetKdfParams, fixedKdfData]])
         allKdfData = fixedKdfData
         LOGWARN('KDF params in wallet were corrupted, but fixed')

      kdfUnpacker = BinaryUnpacker(allKdfData)
      mem   = kdfUnpacker.get(UINT64)
      nIter = kdfUnpacker.get(UINT32)
      salt  = kdfUnpacker.get(BINARY_CHUNK, 32)

      kdf = KdfRomix(mem, nIter, SecureBinaryData(salt))
      return kdf


   #############################################################################
   def serializeCryptoParams(self, binWidth=256):
      """
      As of wallet version 1.0, all wallets use the exact same encryption types,
      so there is nothing to serialize or unserialize.  The 256 bytes here may
      be used in the future, though.
      """
      return '\x00'*binWidth

   #############################################################################
   def unserializeCryptoParams(self, toUnpack, binWidth=256):
      """
      As of wallet version 1.0, all wallets use the exact same encryption types,
      so there is nothing to serialize or unserialize.  The 256 bytes here may
      be used in the future, though.
      """
      if isinstance(toUnpack, BinaryUnpacker):
         binUnpacker = toUnpack
      else:
         binUnpacker = BinaryUnpacker(toUnpack)

      binUnpacker.get(BINARY_CHUNK, binWidth)
      return CryptoAES()

   #############################################################################
   def verifyPassphrase(self, securePassphrase):
      """
      Verify a user-submitted passphrase.  This passphrase goes into
      the key-derivation function to get actual encryption key, which
      is what actually needs to be verified

      Since all addresses should have the same encryption, we only need
      to verify correctness on the root key
      """
      kdfOutput = self.kdf.DeriveKey(securePassphrase)
      try:
         isValid = self.addrMap['ROOT'].verifyEncryptionKey(kdfOutput)
         return isValid
      finally:
         kdfOutput.destroy()


   #############################################################################
   def verifyEncryptionKey(self, secureKdfOutput):
      """
      Verify the underlying encryption key (from KDF).
      Since all addresses should have the same encryption,
      we only need to verify correctness on the root key.
      """
      return self.addrMap['ROOT'].verifyEncryptionKey(secureKdfOutput)


   #############################################################################
   def computeSystemSpecificKdfParams(self, targetSec=0.25, maxMem=32*1024*1024):
      """
      WARNING!!! DO NOT CHANGE KDF PARAMS AFTER ALREADY ENCRYPTED THE WALLET
                 By changing them on an already-encrypted wallet, we are going
                 to lose the original AES256-encryption keys -- which are
                 uniquely determined by (numIter, memReqt, salt, passphrase)

                 Only use this method before you have encrypted your wallet,
                 in order to determine good KDF parameters based on your
                 computer's specific speed/memory capabilities.
      """
      kdf = KdfRomix()
      kdf.computeKdfParams(targetSec, long(maxMem))

      mem   = kdf.getMemoryReqtBytes()
      nIter = kdf.getNumIterations()
      salt  = SecureBinaryData(kdf.getSalt().toBinStr())
      return (mem, nIter, salt)

   #############################################################################
   def restoreKdfParams(self, mem, numIter, secureSalt):
      """
      This method should only be used when we are loading an encrypted wallet
      from file.  DO NOT USE THIS TO CHANGE KDF PARAMETERS.  Doing so may
      result in data loss!
      """
      self.kdf = KdfRomix(mem, numIter, secureSalt)


   #############################################################################
   def changeKdfParams(self, mem, numIter, salt, securePassphrase=None):
      """
      Changing KDF changes the wallet encryption key which means that a KDF
      change is essentially the same as an encryption key change.  As such,
      the wallet must be unlocked if you intend to change an already-
      encrypted wallet with KDF.

      TODO: this comment doesn't belong here...where does it go? :
      If the KDF is NOT yet setup, this method will do it.  Supply the target
      compute time, and maximum memory requirements, and the underlying C++
      code will experimentally determine the "hardest" key-derivation params
      that will run within the specified time and memory usage on the system
      executing this method.  You should set the max memory usage very low
      (a few kB) for devices like smartphones, which have limited memory
      availability.  The KDF will then use less memory but more iterations
      to achieve the same compute time.
      """
      if self.useEncryption:
         if not securePassphrase:
            LOGERROR('')
            LOGERROR('You have requested changing the key-derivation')
            LOGERROR('parameters on an already-encrypted wallet, which')
            LOGERROR('requires modifying the encryption on this wallet.')
            LOGERROR('Please unlock your wallet before attempting to')
            LOGERROR('change the KDF parameters.')
            raise WalletLockError, 'Cannot change KDF without unlocking wallet'
         elif not self.verifyPassphrase(securePassphrase):
            LOGERROR('Incorrect passphrase to unlock wallet')
            raise PassphraseError, 'Incorrect passphrase to unlock wallet'

      secureSalt = SecureBinaryData(salt)
      newkdf = KdfRomix(mem, numIter, secureSalt)
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.serializeKdfParams(newkdf), width=256)
      updList = [[WLT_UPDATE_MODIFY, self.offsetKdfParams, bp.getBinaryString()]]

      if not self.useEncryption:
         # We may be setting the kdf params before enabling encryption
         self.walletFileSafeUpdate(updList)
      else:
         # Must change the encryption key: and we won't get here unless
         # we have a passphrase to use.  This call will take the
         self.changeWalletEncryption(securePassphrase=securePassphrase, \
                                     extraFileUpdates=updList, kdfObj=newkdf)

      self.kdf = newkdf




   #############################################################################
   def changeWalletEncryption(self, secureKdfOutput=None, \
                                    securePassphrase=None, \
                                    extraFileUpdates=[],
                                    kdfObj=None):
      """
      Supply the passphrase you would like to use to encrypt this wallet
      (or supply the KDF output directly, to skip the passphrase part).
      This method will attempt to re-encrypt with the new passphrase.
      This fails if the wallet is already locked with a different passphrase.
      If encryption is already enabled, please unlock the wallet before
      calling this method.

      Make sure you set up the key-derivation function (KDF) before changing
      from an unencrypted to an encrypted wallet.  An error will be thrown
      if you don't.  You can use something like the following

         # For a target of 0.05-0.1s compute time:
         (mem,nIter,salt) = wlt.computeSystemSpecificKdfParams(0.1)
         wlt.changeKdfParams(mem, nIter, salt)

      Use the extraFileUpdates to pass in other changes that need to be
      written to the wallet file in the same atomic operation as the
      encryption key modifications.
      """

      if not kdfObj:
         kdfObj = self.kdf

      oldUsedEncryption = self.useEncryption
      if securePassphrase or secureKdfOutput:
         newUsesEncryption = True
      else:
         newUsesEncryption = False

      oldKdfKey = None
      if oldUsedEncryption:
         if self.isLocked:
            raise WalletLockError, 'Must unlock wallet to change passphrase'
         else:
            oldKdfKey = self.kdfKey.copy()


      if newUsesEncryption and not self.kdf:
         raise EncryptionError, 'KDF must be setup before encrypting wallet'

      # Prep the file-update list with extras passed in as argument
      walletUpdateInfo = list(extraFileUpdates)

      # Derive the new KDF key if a passphrase was supplied
      newKdfKey = secureKdfOutput
      if securePassphrase:
         newKdfKey = self.kdf.DeriveKey(securePassphrase)

      if oldUsedEncryption and newUsesEncryption and self.verifyEncryptionKey(newKdfKey):
         LOGWARN('Attempting to change encryption to same passphrase!')
         return # Wallet is encrypted with the new passphrase already


      # With unlocked key data, put the rest in a try/except/finally block
      # To make sure we destroy the temporary kdf outputs
      try:
         # If keys were previously unencrypted, they will be not have
         # initialization vectors and need to be generated before encrypting.
         # This is why we have the enableKeyEncryption() call

         if not oldUsedEncryption==newUsesEncryption:
            # If there was an encryption change, we must change the flags
            # in the wallet file in the same atomic operation as changing
            # the stored keys.  We can't let them get out of sync.
            self.useEncryption = newUsesEncryption
            walletUpdateInfo.append(self.createChangeFlagsEntry())
            self.useEncryption = oldUsedEncryption
            # Restore the old flag just in case the file write fails

         newAddrMap  = {}
         for addr160,addr in self.addrMap.iteritems():
            newAddrMap[addr160] = addr.copy()
            newAddrMap[addr160].enableKeyEncryption(generateIVIfNecessary=True)
            newAddrMap[addr160].changeEncryptionKey(oldKdfKey, newKdfKey)
            newAddrMap[addr160].walletByteLoc = addr.walletByteLoc
            walletUpdateInfo.append( \
               [WLT_UPDATE_MODIFY, addr.walletByteLoc, newAddrMap[addr160].serialize()])


         # Try to update the wallet file with the new encrypted key data
         updateSuccess = self.walletFileSafeUpdate( walletUpdateInfo )

         if updateSuccess:
            # Finally give the new data to the user
            for addr160,addr in newAddrMap.iteritems():
               self.addrMap[addr160] = addr.copy()

         self.useEncryption = newUsesEncryption
         if newKdfKey:
            self.unlock(newKdfKey)
      finally:
         # Make sure we always destroy the temporary passphrase results
         if newKdfKey: newKdfKey.destroy()
         if oldKdfKey: oldKdfKey.destroy()



   #############################################################################
   def getWalletPath(self, nameSuffix=None):
      fpath = self.walletPath

      if self.walletPath=='':
         fpath = os.path.join(ARMORY_HOME_DIR, 'armory_%s_.wallet' % self.uniqueIDB58)

      if not nameSuffix==None:
         pieces = os.path.splitext(fpath)
         if not pieces[0].endswith('_'):
            fpath = pieces[0] + '_' + nameSuffix + pieces[1]
         else:
            fpath = pieces[0] + nameSuffix + pieces[1]
      return fpath



   #############################################################################
   def getCommentForAddress(self, addr160):
      if self.commentsMap.has_key(addr160):
         return self.commentsMap[addr160]
      else:
         return ''

   #############################################################################
   def getComment(self, hashVal):
      """
      This method is used for both address comments, as well as tx comments
      In the first case, use the 20-byte binary pubkeyhash.  Use 32-byte tx
      hash for the tx-comment case.
      """
      if self.commentsMap.has_key(hashVal):
         return self.commentsMap[hashVal]
      else:
         return ''

   #############################################################################
   def setComment(self, hashVal, newComment):
      """
      This method is used for both address comments, as well as tx comments
      In the first case, use the 20-byte binary pubkeyhash.  Use 32-byte tx
      hash for the tx-comment case.
      """
      updEntry = []
      isNewComment = False
      if self.commentsMap.has_key(hashVal):
         # If there is already a comment for this address, overwrite it
         oldCommentLen = len(self.commentsMap[hashVal])
         oldCommentLoc = self.commentLocs[hashVal]
         # The first 23 bytes are the datatype, hashVal, and 2-byte comment size
         offset = 1 + len(hashVal) + 2
         updEntry.append([WLT_UPDATE_MODIFY, oldCommentLoc+offset, '\x00'*oldCommentLen])
      else:
         isNewComment = True


      dtype = WLT_DATATYPE_ADDRCOMMENT
      if len(hashVal)>20:
         dtype = WLT_DATATYPE_TXCOMMENT
         
      updEntry.append([WLT_UPDATE_ADD, dtype, hashVal, newComment])
      newCommentLoc = self.walletFileSafeUpdate(updEntry)
      self.commentsMap[hashVal] = newComment

      # If there was a wallet overwrite, it's location is the first element
      self.commentLocs[hashVal] = newCommentLoc[-1]

   
   #############################################################################
   def setWalletLabels(self, lshort, llong=''):
      toWriteS = lshort.ljust( 32, '\x00')
      toWriteL = llong.ljust(256, '\x00')

      updList = []
      updList.append([WLT_UPDATE_MODIFY, self.offsetLabelName,  toWriteS])
      updList.append([WLT_UPDATE_MODIFY, self.offsetLabelDescr, toWriteL])
      self.walletFileSafeUpdate(updList)
      self.labelName = toWriteS
      self.labelDescr = toWriteL


   #############################################################################
   def packWalletFlags(self, binPacker):
      nFlagBytes = 8
      flags = [False]*nFlagBytes*8
      flags[0] = self.useEncryption
      flags[1] = self.watchingOnly
      flagsBitset = ''.join([('1' if f else '0') for f in flags])
      binPacker.put(UINT64, bitset_to_int(flagsBitset))

   #############################################################################
   def createChangeFlagsEntry(self):
      """
      Packs up the wallet flags and returns a update-entry that can be included
      in a walletFileSafeUpdate call.
      """
      bp = BinaryPacker()
      self.packWalletFlags(bp)
      toWrite = bp.getBinaryString()
      return [WLT_UPDATE_MODIFY, self.offsetWltFlags, toWrite]

   #############################################################################
   def unpackWalletFlags(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         flagData = toUnpack
      else:
         flagData = BinaryUnpacker( toUnpack )

      wltflags = flagData.get(UINT64, 8)
      wltflags = int_to_bitset(wltflags, widthBytes=8)
      self.useEncryption = (wltflags[0]=='1')
      self.watchingOnly  = (wltflags[1]=='1')


   #############################################################################
   def packHeader(self, binPacker):
      if not self.addrMap['ROOT']:
         raise WalletAddressError, 'Cannot serialize uninitialzed wallet!'

      startByte = binPacker.getSize()

      binPacker.put(BINARY_CHUNK, self.fileTypeStr, width=8)
      binPacker.put(UINT32, getVersionInt(self.version))
      binPacker.put(BINARY_CHUNK, self.magicBytes,  width=4)

      # Wallet info flags
      self.offsetWltFlags = binPacker.getSize() - startByte
      self.packWalletFlags(binPacker)

      # Binary Unique ID (firstAddr25bytes[:5][::-1])
      binPacker.put(BINARY_CHUNK, self.uniqueIDBin, width=6)

      # Unix time of wallet creations
      binPacker.put(UINT64, self.wltCreateDate)

      # User-supplied wallet label (short)
      self.offsetLabelName = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.labelName , width=32)

      # User-supplied wallet label (long)
      self.offsetLabelDescr = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.labelDescr,  width=256)

      # Highest used address: 
      self.offsetTopUsed = binPacker.getSize() - startByte
      binPacker.put(INT64, self.highestUsedChainIndex)

      # Key-derivation function parameters
      self.offsetKdfParams = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.serializeKdfParams(), width=256)

      # Wallet encryption parameters (currently nothing to put here)
      self.offsetCrypto = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.serializeCryptoParams(), width=256)

      # Address-chain root, (base-address for deterministic wallets)
      self.offsetRootAddr = binPacker.getSize() - startByte
      self.addrMap['ROOT'].walletByteLoc = self.offsetRootAddr
      binPacker.put(BINARY_CHUNK, self.addrMap['ROOT'].serialize())

      # In wallet version 1.0, this next kB is unused -- may be used in future
      binPacker.put(BINARY_CHUNK, '\x00'*1024)
      return binPacker.getSize() - startByte




   #############################################################################
   def unpackHeader(self, binUnpacker):
      """
      Unpacking the header information from a wallet file.  See the help text
      on the base class, PyBtcWallet, for more information on the wallet
      serialization.
      """
      self.fileTypeStr = binUnpacker.get(BINARY_CHUNK, 8)
      self.version     = readVersionInt(binUnpacker.get(UINT32))
      self.magicBytes  = binUnpacker.get(BINARY_CHUNK, 4)

      # Decode the bits to get the flags
      self.offsetWltFlags = binUnpacker.getPosition()
      self.unpackWalletFlags(binUnpacker)

      # This is the first 4 bytes of the 25-byte address-chain-root address
      # This includes the network byte (i.e. main network, testnet, namecoin)
      self.uniqueIDBin = binUnpacker.get(BINARY_CHUNK, 6)
      self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)
      self.wltCreateDate  = binUnpacker.get(UINT64)

      # We now have both the magic bytes and network byte
      if not self.magicBytes == MAGIC_BYTES:
         LOGERROR('Requested wallet is for a different blockchain!')
         LOGERROR('Wallet is for:   ', BLOCKCHAINS[self.magicBytes])
         LOGERROR('ArmoryEngine:    ', BLOCKCHAINS[MAGIC_BYTES])
         return
      if not self.uniqueIDBin[-1] == ADDRBYTE:
         LOGERROR('Requested wallet is for a different network!')
         LOGERROR('Wallet is for:   ', NETWORKS[netByte])
         LOGERROR('ArmoryEngine:    ', NETWORKS[ADDRBYTE])
         return

      # User-supplied description/name for wallet
      self.offsetLabelName = binUnpacker.getPosition()
      self.labelName  = binUnpacker.get(BINARY_CHUNK, 32).strip('\x00')


      # Longer user-supplied description/name for wallet
      self.offsetLabelDescr  = binUnpacker.getPosition()
      self.labelDescr  = binUnpacker.get(BINARY_CHUNK, 256).strip('\x00')


      self.offsetTopUsed = binUnpacker.getPosition()
      self.highestUsedChainIndex = binUnpacker.get(INT64)


      # Read the key-derivation function parameters
      self.offsetKdfParams = binUnpacker.getPosition()
      self.kdf = self.unserializeKdfParams(binUnpacker)

      # Read the crypto parameters
      self.offsetCrypto    = binUnpacker.getPosition()
      self.crypto = self.unserializeCryptoParams(binUnpacker)

      # Read address-chain root address data
      self.offsetRootAddr  = binUnpacker.getPosition()
      

      rawAddrData = binUnpacker.get(BINARY_CHUNK, self.pybtcaddrSize)
      self.addrMap['ROOT'] = PyBtcAddress().unserialize(rawAddrData)
      fixedAddrData = self.addrMap['ROOT'].serialize()
      if not rawAddrData==fixedAddrData:
         self.walletFileSafeUpdate([ \
            [WLT_UPDATE_MODIFY, self.offsetRootAddr, fixedAddrData]])

      self.addrMap['ROOT'].walletByteLoc = self.offsetRootAddr
      if self.useEncryption:
         self.addrMap['ROOT'].isLocked = True
         self.isLocked = True

      # In wallet version 1.0, this next kB is unused -- may be used in future
      binUnpacker.advance(1024)

      # TODO: automatic conversion if the code uses a newer wallet
      #       version than the wallet... got a manual script, but it
      #       would be nice to autodetect and correct
      #convertVersion


   #############################################################################
   def unpackNextEntry(self, binUnpacker):
      dtype   = binUnpacker.get(UINT8)
      hashVal = ''
      binData = ''
      if dtype==WLT_DATATYPE_KEYDATA:
         hashVal = binUnpacker.get(BINARY_CHUNK, 20)
         binData = binUnpacker.get(BINARY_CHUNK, self.pybtcaddrSize)
      elif dtype==WLT_DATATYPE_ADDRCOMMENT:
         hashVal = binUnpacker.get(BINARY_CHUNK, 20)
         commentLen = binUnpacker.get(UINT16)
         binData = binUnpacker.get(BINARY_CHUNK, commentLen)
      elif dtype==WLT_DATATYPE_TXCOMMENT:
         hashVal = binUnpacker.get(BINARY_CHUNK, 32)
         commentLen = binUnpacker.get(UINT16)
         binData = binUnpacker.get(BINARY_CHUNK, commentLen)
      elif dtype==WLT_DATATYPE_OPEVAL:
         raise NotImplementedError, 'OP_EVAL not support in wallet yet'
      elif dtype==WLT_DATATYPE_DELETED:
         deletedLen = binUnpacker.get(UINT16)
         binUnpacker.advance(deletedLen)
         

      return (dtype, hashVal, binData)

   #############################################################################
   def readWalletFile(self, wltpath, verifyIntegrity=True, skipBlockChainScan=False):

      if not os.path.exists(wltpath):
         raise FileExistsError, "No wallet file:"+wltpath

      self.__init__()
      self.walletPath = wltpath

      if verifyIntegrity:
         try:
            nError = self.doWalletFileConsistencyCheck()
         except KeyDataError, errmsg:
            LOGEXCEPT('***ERROR:  Wallet file had unfixable errors.')
            raise KeyDataError, errmsg


      wltfile = open(wltpath, 'rb')
      wltdata = BinaryUnpacker(wltfile.read())
      wltfile.close()

      self.cppWallet = Cpp.BtcWallet()
      self.unpackHeader(wltdata)

      self.lastComputedChainIndex = -UINT32_MAX
      self.lastComputedChainAddr160  = None
      while wltdata.getRemainingSize()>0:
         byteLocation = wltdata.getPosition()
         dtype, hashVal, rawData = self.unpackNextEntry(wltdata)
         if dtype==WLT_DATATYPE_KEYDATA:
            newAddr = PyBtcAddress()
            newAddr.unserialize(rawData)
            newAddr.walletByteLoc = byteLocation + 21
            # Fix byte errors in the address data
            fixedAddrData = newAddr.serialize()
            if not rawData==fixedAddrData:
               self.walletFileSafeUpdate([ \
                  [WLT_UPDATE_MODIFY, newAddr.walletByteLoc, fixedAddrData]])
            if newAddr.useEncryption:
               newAddr.isLocked = True
            self.addrMap[hashVal] = newAddr
            if newAddr.chainIndex > self.lastComputedChainIndex:
               self.lastComputedChainIndex   = newAddr.chainIndex
               self.lastComputedChainAddr160 = newAddr.getAddr160()
            self.linearAddr160List.append(newAddr.getAddr160())
            self.chainIndexMap[newAddr.chainIndex] = newAddr.getAddr160()

            # Update the parallel C++ object that scans the blockchain for us
            timeRng = newAddr.getTimeRange()
            blkRng  = newAddr.getBlockRange()
            self.cppWallet.addAddress_5_(hashVal, timeRng[0], blkRng[0], \
                                                  timeRng[1], blkRng[1])
         if dtype in (WLT_DATATYPE_ADDRCOMMENT, WLT_DATATYPE_TXCOMMENT):
            self.commentsMap[hashVal] = rawData # actually ASCII data, here
            self.commentLocs[hashVal] = byteLocation
         if dtype==WLT_DATATYPE_OPEVAL:
            raise NotImplementedError, 'OP_EVAL not support in wallet yet'
         if dtype==WLT_DATATYPE_DELETED:
            pass


      if (skipBlockChainScan or \
          not TheBDM.isInitialized() or \
          self.doBlockchainSync==BLOCKCHAIN_DONOTUSE):
         pass
      else:
         self.syncWithBlockchain()


      ### Update the wallet version if necessary ###
      if getVersionInt(self.version) < getVersionInt(PYBTCWALLET_VERSION):
         LOGERROR('Wallets older than version 1.35 no loger supported!')
         return

      return self



   #############################################################################
   def walletFileSafeUpdate(self, updateList):
            
      """
      The input "toAddDataList" should be a list of triplets, such as:
      [
        [WLT_DATA_ADD,    WLT_DATATYPE_KEYDATA, addr160_1,  PyBtcAddrObj1]
        [WLT_DATA_ADD,    WLT_DATATYPE_KEYDATA, addr160_2,  PyBtcAddrObj2]
        [WLT_DATA_MODIFY, modifyStartByte1,  binDataForOverwrite1  ]
        [WLT_DATA_ADD,    WLT_DATATYPE_ADDRCOMMENT, addr160_3,  'Long-term savings']
        [WLT_DATA_MODIFY, modifyStartByte2,  binDataForOverwrite2 ]
      ]

      The return value is the list of new file byte offsets (from beginning of
      the file), that specify the start of each modification made to the
      wallet file.  For MODIFY fields, this just returns the modifyStartByte
      field that was provided as input.  For adding data, it specifies the
      starting byte of the new field (the DATATYPE byte).  We keep this data
      in PyBtcAddress objects so that we know where to apply modifications in
      case we need to change something, like converting from unencrypted to
      encrypted private keys.

      If this method fails, we simply return an empty list.  We can check for
      an empty list to know if the file update succeeded.

      WHY IS THIS SO COMPLICATED?  -- Because it's atomic!

      When we want to add data to the wallet file, we will do so in a completely
      recoverable way.  We define this method to make sure a backup exists when
      we start modifying the file, and keep a flag to identify when the wallet
      might be corrupt.  If we ever try to load the wallet file and see another
      file with the _update_unsuccessful suffix, we should instead just restore
      from backup.

      Similarly, we have to update the backup file after updating the main file
      so we will use a similar technique with the backup_unsuccessful suffix.
      We don't want to rely on a backup if somehow *the backup* got corrupted
      and the original file is fine.  THEREFORE -- this is implemented in such
      a way that the user should know two things:

         (1) No matter when the power goes out, we ALWAYS have a uncorrupted
             wallet file, and know which one it is.  Either the backup is safe,
             or the original is safe.  Based on the flag files, we know which
             one is guaranteed to be not corrupted.
         (2) ALWAYS DO YOUR FILE OPERATIONS BEFORE SETTING DATA IN MEMORY
             You must write it to disk FIRST using this SafeUpdate method,
             THEN give the new data to the user -- never give it to them
             until you are sure that it was written safely to disk.

      Number (2) is easy to screw up because you plan to write the file just
      AFTER the data is created and stored in local memory.  But an error
      might be thrown halfway which is handled higher up, and instead the data
      never made it to file.  Then there is a risk that the user uses their
      new address that never made it into the wallet file.
      """

      if not os.path.exists(self.walletPath):
         raise FileExistsError, 'No wallet file exists to be updated!'

      if len(updateList)==0:
         return []

      # Make sure that the primary and backup files are synced before update
      self.doWalletFileConsistencyCheck()

      walletFileBackup = self.getWalletPath('backup')
      mainUpdateFlag   = self.getWalletPath('update_unsuccessful')
      backupUpdateFlag = self.getWalletPath('backup_unsuccessful')


      # Will be passing back info about all data successfully added
      oldWalletSize = os.path.getsize(self.walletPath)
      updateLocations = []
      dataToChange    = []
      toAppend = BinaryPacker()

      try:
         for entry in updateList:
            modType    = entry[0]
            updateInfo = entry[1:]

            if(modType==WLT_UPDATE_ADD):
               dtype = updateInfo[0]
               updateLocations.append(toAppend.getSize()+oldWalletSize)
               if dtype==WLT_DATATYPE_KEYDATA:
                  if len(updateInfo[1])!=20 or not isinstance(updateInfo[2], PyBtcAddress):
                     raise Exception, 'Data type does not match update type'
                  toAppend.put(UINT8, WLT_DATATYPE_KEYDATA)
                  toAppend.put(BINARY_CHUNK, updateInfo[1])
                  toAppend.put(BINARY_CHUNK, updateInfo[2].serialize())

               elif dtype in (WLT_DATATYPE_ADDRCOMMENT, WLT_DATATYPE_TXCOMMENT):
                  if not isinstance(updateInfo[2], str):
                     raise Exception, 'Data type does not match update type'
                  toAppend.put(UINT8, dtype)
                  toAppend.put(BINARY_CHUNK, updateInfo[1])
                  toAppend.put(UINT16, len(updateInfo[2]))
                  toAppend.put(BINARY_CHUNK, updateInfo[2])

               elif dtype==WLT_DATATYPE_OPEVAL:
                  raise Exception, 'OP_EVAL not support in wallet yet'

            elif(modType==WLT_UPDATE_MODIFY):
               updateLocations.append(updateInfo[0])
               dataToChange.append( updateInfo )
            else:
               LOGERROR('Unknown wallet-update type!')
               raise Exception, 'Unknown wallet-update type!'
      except Exception:
         LOGEXCEPT('Bad input to walletFileSafeUpdate')
         return []

      binaryToAppend = toAppend.getBinaryString()

      # We need to safely modify both the main wallet file and backup
      # Start with main wallet
      touchFile(mainUpdateFlag)

      try:
         wltfile = open(self.walletPath, 'ab')
         wltfile.write(binaryToAppend)
         wltfile.close()

         # This is for unit-testing the atomic-wallet-file-update robustness
         if self.interruptTest1: raise InterruptTestError

         wltfile = open(self.walletPath, 'r+b')
         for loc,replStr in dataToChange:
            wltfile.seek(loc)
            wltfile.write(replStr)
         wltfile.close()

      except IOError:
         LOGEXCEPT('Could not write data to wallet.  Permissions?')
         shutil.copy(walletFileBackup, self.walletPath)
         os.remove(mainUpdateFlag)
         return []

      # Write backup flag before removing main-update flag.  If we see
      # both flags, we know file IO was interrupted RIGHT HERE
      touchFile(backupUpdateFlag)

      # This is for unit-testing the atomic-wallet-file-update robustness
      if self.interruptTest2: raise InterruptTestError

      os.remove(mainUpdateFlag)

      # Modify backup
      try:
         # This is for unit-testing the atomic-wallet-file-update robustness
         if self.interruptTest3: raise InterruptTestError

         backupfile = open(walletFileBackup, 'ab')
         backupfile.write(binaryToAppend)
         backupfile.close()

         backupfile = open(walletFileBackup, 'r+b')
         for loc,replStr in dataToChange:
            backupfile.seek(loc)
            backupfile.write(replStr)
         backupfile.close()

      except IOError:
         LOGEXCEPT('Could not write backup wallet.  Permissions?')
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(mainUpdateFlag)
         return []

      os.remove(backupUpdateFlag)

      return updateLocations



   #############################################################################
   def doWalletFileConsistencyCheck(self, onlySyncBackup=True):
      """
      First we check the file-update flags (files we touched/removed during
      file modification operations), and then restore the primary wallet file
      and backup file to the exact same state -- we know that at least one of
      them is guaranteed to not be corrupt, and we know based on the flags
      which one that is -- so we execute the appropriate copy operation.

      ***NOTE:  For now, the remaining steps are untested and unused!

      After we have guaranteed that main wallet and backup wallet are the
      same, we want to do a check that the data is consistent.  We do this
      by simply reading in the key-data from the wallet, unserializing it
      and reserializing it to see if it matches -- this works due to the
      way the PyBtcAddress::unserialize() method works:  it verifies the
      checksums in the address data, and corrects errors automatically!
      And it's part of the unit-tests that serialize/unserialize round-trip
      is guaranteed to match for all address types if there's no byte errors.

      If an error is detected, we do a safe-file-modify operation to re-write
      the corrected information to the wallet file, in-place.  We DO NOT
      check comment fields, since they do not have checksums, and are not
      critical to protect against byte errors.
      """



      if not os.path.exists(self.walletPath):
         raise FileExistsError, 'No wallet file exists to be checked!'

      walletFileBackup = self.getWalletPath('backup')
      mainUpdateFlag   = self.getWalletPath('update_unsuccessful')
      backupUpdateFlag = self.getWalletPath('backup_unsuccessful')

      if not os.path.exists(walletFileBackup):
         # We haven't even created a backup file, yet
         LOGDEBUG('Creating backup file %s', walletFileBackup)
         touchFile(backupUpdateFlag)
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(backupUpdateFlag)

      if os.path.exists(backupUpdateFlag) and os.path.exists(mainUpdateFlag):
         # Here we actually have a good main file, but backup never succeeded
         LOGWARN('***WARNING: error in backup file... how did that happen?')
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(mainUpdateFlag)
         os.remove(backupUpdateFlag)
      elif os.path.exists(mainUpdateFlag):
         LOGWARN('***WARNING: last file operation failed!  Restoring wallet from backup')
         # main wallet file might be corrupt, copy from backup
         shutil.copy(walletFileBackup, self.walletPath)
         os.remove(mainUpdateFlag)
      elif os.path.exists(backupUpdateFlag):
         LOGWARN('***WARNING: creation of backup was interrupted -- fixing')
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(backupUpdateFlag)

      if onlySyncBackup:
         return 0






   #############################################################################
   #def getAddrByIndex(self, i):
      #return self.addrMap.values()[i]

   #############################################################################
   def deleteImportedAddress(self, addr160):
      """
      We want to overwrite a particular key in the wallet.  Before overwriting
      the data looks like this:
         [  \x00  |  <20-byte addr160>  |  <237-byte keydata> ]
      And we want it to look like:
         [  \x04  |  <2-byte length>  | \x00\x00\x00... ]
      So we need to construct a wallet-update vector to modify the data
      starting at the first byte, replace it with 0x04, specifies how many
      bytes are in the deleted entry, and then actually overwrite those 
      bytes with 0s
      """

      if not self.addrMap[addr160].chainIndex==-2:
         raise WalletAddressError, 'You can only delete imported addresses!'

      overwriteLoc = self.addrMap[addr160].walletByteLoc - 21
      overwriteLen = 20 + self.pybtcaddrSize - 2

      overwriteBin = ''
      overwriteBin += int_to_binary(WLT_DATATYPE_DELETED, widthBytes=1)
      overwriteBin += int_to_binary(overwriteLen,         widthBytes=2)
      overwriteBin += '\x00'*overwriteLen

      self.walletFileSafeUpdate([[WLT_UPDATE_MODIFY, overwriteLoc, overwriteBin]])

      # IMPORTANT:  we need to update the wallet structures to reflect the
      #             new state of the wallet.  This will actually be easiest
      #             if we just "forget" the current wallet state and re-read
      #             the wallet from file
      wltPath = self.walletPath
      self.readWalletFile(wltPath)
      

   #############################################################################
   def importExternalAddressData(self, privKey=None, privChk=None, \
                                       pubKey=None,  pubChk=None, \
                                       addr20=None,  addrChk=None, \
                                       firstTime=UINT32_MAX,  firstBlk=UINT32_MAX, \
                                       lastTime=0,   lastBlk=0):
      """
      This wallet fully supports importing external keys, even though it is
      a deterministic wallet: determinism only adds keys to the pool based
      on the address-chain, but there's nothing wrong with adding new keys
      not on the chain.

      We don't know when this address was created, so we have to set its
      first/last-seen times to 0, to make sure we search the whole blockchain
      for tx related to it.  This data will be updated later after we've done
      the search and know for sure when it is "relevant".
      (alternatively, if you know it's first-seen time for some reason, you
      can supply it as an input, but this seems rare: we don't want to get it
      wrong or we could end up missing wallet-relevant transactions)
      """

      if not privKey and not self.watchingOnly:
         LOGERROR('')
         LOGERROR('This wallet is strictly for addresses that you')
         LOGERROR('own.  You cannot import addresses without the')
         LOGERROR('the associated private key.  Instead, use a')
         LOGERROR('watching-only wallet to import this address.')
         LOGERROR('(actually, this is currently, completely disabled)')
         raise WalletAddressError, 'Cannot import non-private-key addresses'



      # First do all the necessary type conversions and error corrections
      computedPubKey = None
      computedAddr20 = None
      if privKey:
         if isinstance(privKey, str):
            privKey = SecureBinaryData(privKey)

         if privChk:
            privKey = SecureBinaryData(verifyChecksum(privKey.toBinStr(), privChk))

         computedPubkey = CryptoECDSA().ComputePublicKey(privKey)
         computedAddr20 = convertKeyDataToAddress(pubKey=computedPubkey)

      # If public key is provided, we prep it so we can verify Pub/Priv match
      if pubKey:
         if isinstance(pubKey, str):
            pubKey = SecureBinaryData(pubKey)
         if pubChk:
            pubKey = SecureBinaryData(verifyChecksum(pubKey.toBinStr(), pubChk))

         if not computedAddr20:
            computedAddr20 = convertKeyDataToAddress(pubKey=pubKey)

      # The 20-byte address (pubkey hash160) should always be a python string
      if addr20:
         if not isinstance(pubKey, str):
            addr20 = addr20.toBinStr()
         if addrChk:
            addr20 = verifyChecksum(addr20, addrChk)


      # Now a few sanity checks
      if self.addrMap.has_key(addr20):
         LOGWARN('This address is already in your wallet!')
         return

      #if pubKey and not computedPubkey==pubKey:
         #raise ECDSA_Error, 'Private and public keys to be imported do not match!'
      #if addr20 and not computedAddr20==addr20:
         #raise ECDSA_Error, 'Supplied address hash does not match key data!'

      addr20 = computedAddr20
      
      if self.addrMap.has_key(addr20):
         return None

      # If a private key is supplied and this wallet is encrypted&locked, then 
      # we have no way to secure the private key without unlocking the wallet.
      if self.useEncryption and privKey and not self.kdfKey:
         raise WalletLockError, 'Cannot import private key when wallet is locked!'


      if privKey:
         # For priv key, lots of extra encryption and verification options
         newAddr = PyBtcAddress().createFromPlainKeyData( addr160=addr20, \
                                  plainPrivKey=privKey, publicKey65=computedPubkey,  \
                                  willBeEncr=self.useEncryption, \
                                  generateIVIfNecessary=self.useEncryption, \
                                  skipCheck=True, skipPubCompute=True)
         if self.useEncryption:
            newAddr.lock(self.kdfKey)
            newAddr.unlock(self.kdfKey)
      elif pubKey:
         securePubKey = SecureBinaryData(pubKey)
         newAddr = PyBtcAddress().createFromPublicKeyData(securePubKey)
      else:
         newAddr = PyBtcAddress().createFromPublicKeyHash160(addr20)


      newAddr.chaincode  = SecureBinaryData('\xff'*32)
      newAddr.chainIndex = -2
      newAddr.timeRange = [firstTime, lastTime]
      newAddr.blkRange  = [firstBlk,  lastBlk ]
      #newAddr.binInitVect16  = SecureBinaryData().GenerateRandom(16)
      newAddr160 = newAddr.getAddr160()

      newDataLoc = self.walletFileSafeUpdate( \
         [[WLT_UPDATE_ADD, WLT_DATATYPE_KEYDATA, newAddr160, newAddr]])
      self.addrMap[newAddr160] = newAddr.copy()
      self.addrMap[newAddr160].walletByteLoc = newDataLoc[0] + 21
      self.linearAddr160List.append(newAddr160)
      if self.useEncryption and self.kdfKey:
         self.addrMap[newAddr160].lock(self.kdfKey)
         if not self.isLocked:
            self.addrMap[newAddr160].unlock(self.kdfKey)

      self.cppWallet.addAddress_5_(newAddr160, \
                                   firstTime, firstBlk, lastTime, lastBlk)
      TheBDM.registerImportedAddress(newAddr160, firstTime, firstBlk, \
                                                 lastTime,  lastBlk)


      return newAddr160


   #############################################################################
   def bulkImportAddresses(self, textBlock, privKeyEndian=BIGENDIAN, \
                     sepList=":;'[]()=-_*&^%$#@!,./?\n"):
      """
      Attempts to import plaintext key data stored in a file.  This method
      expects all data to be in hex or Base58:

         20 bytes / 40  hex chars -- public key hashes
         25 bytes / 50  hex chars -- full binary addresses
         65 bytes / 130 hex chars -- public key
         32 bytes / 64  hex chars -- private key

         33 or 34 Base58 chars    -- address strings
         50 to 52 Base58 chars    -- base58-encoded private key

      Since this is python, I don't have to require any particular format:
      I can pretty easily break apart the entire file into individual strings,
      search for addresses and public keys, then, search for private keys that
      correspond to that data.  Obviously, simpler is better, but as long as
      the data is encoded as in the above list and separated by whitespace or
      punctuation, this method should succeed.

      We must throw an error if this is NOT a watching-only address and we
      find an address without a private key.  We will need to create a
      separate watching-only wallet in order to import these keys.

      TODO: will finish this later
      """

      """
      STUB: (AGAIN) I just can't make this work out to be as stupid-proof 
            as I originally planned.  I'll have to put it on hold.
      self.__init__()

      newfile = open(filename,'rb')
      newdata = newfile.read()
      newfile.close()

      # Change all punctuation to the same char so split() works easier
      for ch in sepList:
         newdata.replace(ch, ' ')

      newdata = newdata.split()
      hexChars = '01234567890abcdef'
      b58Chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
      DATATYPES = enum( 'UNKNOWN', \
                        'Addr_Hex_20', \
                        'Addr_B58_25', \
                        'PubX_Hex_32', \
                        'PubY_Hex_32', \
                        'PubK_Hex_65', \
                        'Priv_Hex_32', \
                        'Priv_Hex_36', \
                        'Priv_Hex_37', \
                        'Priv_B58_32', \
                        'Priv_B58_37', \
                        'Priv_MiniPriv', \
                        'PubK_Hex_33_Compressed', \
                        'Priv_Hex_33_Compressed')

      DTYPES = enum('Unknown', 'Hash160', 'PubKey', 'PrivKey', 'Byte32', 'Byte33')
      

      lastAddr = None
      lastPubK = None
      lastPriv = None
      for theStr in newdata:
         if len(theStr)<20:
            continue

         hexCount = sum([1 if c in hexChars else 0 for c in theStr])
         b58Count = sum([1 if c in b58Chars else 0 for c in theStr])
         canBeHex = hexCount==len(theStr)
         canBeB58 = b58Count==len(theStr)
         isHex = canBeHex
         isB58 = canBeB58 and not canBeHex
         isStr = not isHex and not isB58

         dataAndType = [DTYPES.Unknown, '']
         if isHex:
            binData = hex_to_binary(theStr)
            sz = len(binData)

            if sz==20:
               dataAndType = [DTYPES.Hash160, binData]
            elif sz==25:
               dataAndType = [DTYPES.Hash160, binData[1:21]]
            elif sz==32:
               dataAndType = [DTYPES., binData[1:21]]
         elif isB58:
            binData = base58_to_binary(theStr)
            sz = len(binData)

            
         if isHex and sz==40:
         elif isHex and sz==50:
            dataAndType = [DTYPES.Hash160, hex_to_binary(theStr)[1:21]]
         elif isB58 and sz>=31 and sz<=35:
            dataAndType = [DTYPES.Hash160, addrStr_to_hash160(theStr)]
         elif isHex is sz==130:
            dataAndType = [DTYPES.PubKey, hex_to_binary(theStr)]
         elif isHex is sz==128:
            dataAndType = [DTYPES.PubKey, '\x04'+hex_to_binary(theStr)]
         elif isHex is sz==128:
            
             

         potentialKey = SecureBinaryData('\x04' + piece)
         isValid = CryptoECDSA().VerifyPublicKeyValid(potentialKey)
      """
      pass





   #############################################################################
   def checkIfRescanRequired(self):
      """ 
      Returns true is we have to go back to disk/mmap and rescan more than two
      weeks worth of blocks
      """
      if TheBDM.isInitialized():
         return (TheBDM.numBlocksToRescan(self.cppWallet) > 2016)
      else:
         return False



   #############################################################################
   def signTxDistProposal(self, txdp, hashcode=1):
      if not hashcode==1:
         LOGERROR('hashcode!=1 is not supported at this time!')
         return

      # If the wallet is locked, we better bail now
      if self.isLocked:
         raise WalletLockError, "Cannot sign Tx when wallet is locked!"

      numInputs = len(txdp.pytxObj.inputs)
      wltAddr = []
      for index,txin in enumerate(txdp.pytxObj.inputs):
         scriptType = getTxOutScriptType(txdp.txOutScripts[index])
         
         if scriptType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            addr160 = TxOutScriptExtractAddr160(txdp.txOutScripts[index])
            if self.hasAddr(addr160) and self.addrMap[addr160].hasPrivKey():
               wltAddr.append( (self.addrMap[addr160], index, 0))
         elif scriptType==TXOUT_SCRIPT_MULTISIG:
            # Basically the same check but multiple addresses to consider
            addrList = getTxOutMultiSigInfo(txdp.txOutScripts[index])[1]
            for addrIdx, addr in enumerate(addrList):
               if self.hasAddr(addr) and self.addrMap[addr].hasPrivKey():
                  wltAddr.append( (self.addrMap[addr], index, addrIdx) )
                  break
                  

      # WltAddr now contains a list of every input we can sign for, and the
      # PyBtcAddress object that can be used to sign it.  Let's do it.
      numMyAddr = len(wltAddr)
      LOGDEBUG('Total number of inputs in transaction:  %d', numInputs)
      LOGDEBUG('Number of inputs that you can sign for: %d', numMyAddr)


      # Unlock the wallet if necessary, sign inputs 
      maxChainIndex = -1
      for addrObj,idx, sigIdx in wltAddr:
         maxChainIndex = max(maxChainIndex, addrObj.chainIndex)
         if addrObj.isLocked:
            if self.kdfKey:
               addrObj.unlock(self.kdfKey)
            else:
               raise WalletLockError, 'Cannot sign tx without unlocking wallet'

         if not addrObj.hasPubKey():
            # Make sure the public key is available for this address
            addrObj.binPublicKey65 = CryptoECDSA().ComputePublicKey(addrObj.binPrivKey32_Plain)

         # Copy the script, blank out out all other scripts (assume hashcode==1)
         txCopy = PyTx().unserialize(txdp.pytxObj.serialize())
         for i in range(len(txCopy.inputs)):
            if not i==idx:
               txCopy.inputs[i].binScript = ''
            else:
               txCopy.inputs[i].binScript = txdp.txOutScripts[i]

         hashCode1  = int_to_binary(hashcode, widthBytes=1)
         hashCode4  = int_to_binary(hashcode, widthBytes=4)
         preHashMsg = txCopy.serialize() + hashCode4
         signature  = addrObj.generateDERSignature(preHashMsg) + hashCode1

         # Now we attach a binary signature or full script, depending on the type
         if txdp.scriptTypes[idx]==TXOUT_SCRIPT_COINBASE:
            # Only need the signature to complete coinbase TxOut
            sigLenInBinary = int_to_binary(len(signature))
            txdp.signatures[idx][0] = sigLenInBinary + signature
         elif txdp.scriptTypes[idx]==TXOUT_SCRIPT_STANDARD:
            # Gotta include the public key, too, for standard TxOuts
            pubkey = addrObj.binPublicKey65.toBinStr()
            sigLenInBinary    = int_to_binary(len(signature))
            pubkeyLenInBinary = int_to_binary(len(pubkey)   )
            txdp.signatures[idx][0] = sigLenInBinary    + signature + \
                                      pubkeyLenInBinary + pubkey
         elif txdp.scriptTypes[idx]==TXOUT_SCRIPT_MULTISIG:
            # We attach just the sig for multi-sig transactions
            sigLenInBinary = int_to_binary(len(signature))
            txdp.signatures[idx][sigIdx] = (sigLenInBinary + signature)
         else:
            LOGERROR('Unknown txOut script type')

      
      prevHighestIndex = self.highestUsedChainIndex  
      if prevHighestIndex<maxChainIndex:
         self.advanceHighestIndex(maxChainIndex-prevHighestIndex)
         self.fillAddressPool()
      
      return txdp



   #############################################################################
   def unlock(self, secureKdfOutput=None, \
                    securePassphrase=None, \
                    tempKeyLifetime=0):
      """
      We must assume that the kdfResultKey is a SecureBinaryData object
      containing the result of the KDF-passphrase.  The wallet unlocked-
      lifetime will be set to X seconds from time.time() [now] and next
      time the checkWalletLockTimeout function is called it will be re-
      locked.
      """
      
      LOGDEBUG('Attempting to unlock wallet: %s', self.uniqueIDB58)
      if not secureKdfOutput and not securePassphrase:
         raise PassphraseError, "No passphrase/key provided to unlock wallet!"
         
      if not secureKdfOutput:
         if not self.kdf:
            raise EncryptionError, 'How do we have a locked wallet w/o KDF???'
         secureKdfOutput = self.kdf.DeriveKey(securePassphrase)


      if not self.verifyEncryptionKey(secureKdfOutput):
         raise PassphraseError, "Incorrect passphrase for wallet"

      # For now, I assume that all keys have the same passphrase and all
      # unlocked successfully at the same time.
      # It's an awful lot of work to design a wallet to consider partially-
      # successful unlockings.
      self.kdfKey = secureKdfOutput
      if tempKeyLifetime==0:
         self.lockWalletAtTime = RightNow() + self.defaultKeyLifetime
      else:
         self.lockWalletAtTime = RightNow() + tempKeyLifetime

      for addrObj in self.addrMap.values():
         needToSaveAddrAfterUnlock = addrObj.createPrivKeyNextUnlock
         addrObj.unlock(self.kdfKey)
         if needToSaveAddrAfterUnlock:
            updateLoc = addrObj.walletByteLoc 
            self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, addrObj.walletByteLoc, \
                                                addrObj.serialize()]])

      self.isLocked = False
      LOGDEBUG('Unlock succeeded: %s', self.uniqueIDB58)


   #############################################################################
   def lock(self):
      """
      We assume that we have already set all encryption parameters (such as
      IVs for each key) and thus all we need to do is call the "lock" method
      on each PyBtcAddress object.

      If wallet is unlocked, try to re-lock addresses, regardless of whether
      we have a kdfKey or not.  In some circumstances (such as when the addrs
      have never been locked before) we will need the key to encrypt them.
      However, in most cases, the encrypted versions are already available
      and the PyBtcAddress objects can destroy the plaintext keys without
      ever needing access to the encryption keys.

      ANY METHOD THAT CALLS THIS MUST CATCH WALLETLOCKERRORS UNLESS YOU ARE
      POSITIVE THAT THE KEYS HAVE ALREADY BEEN ENCRYPTED BEFORE, OR ARE
      ALREADY SITTING IN THE ENCRYPTED WALLET FILE.  PyBtcAddress objects
      were designed to do this, but in case of a bug, you don't want the
      program crashing with money-bearing private keys sitting in memory only.

      TODO: If things like IVs are not set properly, we should implement
            a way to check for this, correct it, and update the wallet
            file if necessary
      """

      # Wallet is unlocked, will try to re-lock addresses, regardless of whether
      # we have a kdfKey or not.  If a key is required, we will throw a
      # WalletLockError, and the caller can get the passphrase from the user,
      # unlock the wallet, then try locking again.
      # NOTE: If we don't have kdfKey, it is set to None, which is the default
      #       input for PyBtcAddress::lock for "I don't have it".  In most 
      #       cases, it is actually possible to lock the wallet without the 
      #       kdfKey because we saved the encrypted versions before unlocking
      LOGDEBUG('Attempting to lock wallet: %s', self.uniqueIDB58)
      try:
         for addr160,addrObj in self.addrMap.iteritems():
            self.addrMap[addr160].lock(self.kdfKey)

         if self.kdfKey:
            self.kdfKey.destroy()
            self.kdfKey = None
         self.isLocked = True
      except WalletLockError:
         LOGERROR('Locking wallet requires encryption key.  This error')
         LOGERROR('Usually occurs on newly-encrypted wallets that have')
         LOGERROR('never been encrypted before.')
         raise WalletLockError, 'Unlock with passphrase before locking again'
      LOGDEBUG('Wallet locked: %s', self.uniqueIDB58)


   #############################################################################
   def getAddrListSortedByChainIndex(self, withRoot=False):
      """ Returns Addr160 list """
      addrList = []
      for addr160 in self.linearAddr160List:
         addr=self.addrMap[addr160]
         addrList.append( [addr.chainIndex, addr160, addr] )

      addrList.sort(key=lambda x: x[0])
      return addrList

   #############################################################################
   def getAddrList(self):
      """ Returns list of PyBtcAddress objects """
      addrList = []
      for addr160,addrObj in self.addrMap.iteritems():
         if addr160=='ROOT':
            continue
         # I assume these will be references, not copies
         addrList.append( addrObj )
      return addrList


   #############################################################################
   def getLinearAddrList(self, withImported=True, withAddrPool=False):
      """ 
      Retrieves a list of addresses, by hash, in the order they 
      appear in the wallet file.  Can ignore the imported addresses
      to get only chained addresses, if necessary.

      I could do this with one list comprehension, but it would be long.
      I'm resisting the urge...
      """
      addrList = []
      for a160 in self.linearAddr160List:
         addr = self.addrMap[a160]
         if not a160=='ROOT' and (withImported or addr.chainIndex>=0):
            # Either we want imported addresses, or this isn't one
            if (withAddrPool or addr.chainIndex<=self.highestUsedChainIndex):
               addrList.append(addr)
         
      return addrList
      

   #############################################################################
   def getAddress160ByChainIndex(self, desiredIdx):
      """
      It should be safe to assume that if the index is less than the highest 
      computed, it will be in the chainIndexMap, but I don't like making such
      assumptions.  Perhaps something went wrong with the wallet, or it was
      manually reconstructed and has holes in the chain.  We will regenerate
      addresses up to that point, if necessary (but nothing past the value
      self.lastComputedChainIndex.
      """
      if desiredIdx>self.lastComputedChainIndex or desiredIdx<0:
         # I removed the option for fillPoolIfNecessary, because of the risk
         # that a bug may lead to generation of billions of addresses, which
         # would saturate the system's resources and fill the HDD.
         raise WalletAddressError, 'Chain index is out of range'
         

      if self.chainIndexMap.has_key(desiredIdx):
         return self.chainIndexMap[desiredIdx]
      else:
         # Somehow the address isn't here, even though it is less than the
         # last computed index
         closestIdx = 0
         for idx,addr160 in self.chainIndexMap.iteritems():
            if closestIdx<idx<=desiredIdx:
               closestIdx = idx
               
         gap = desiredIdx - closestIdx
         extend160 = self.chainIndexMap[closestIdx]
         for i in range(gap+1):
            extend160 = computeNextAddress(extend160)
            if desiredIdx==self.addrMap[extend160].chainIndex:
               return self.chainIndexMap[desiredIdx]


   #############################################################################
   def pprint(self, indent='', allAddrInfo=True):
      print indent + 'PyBtcWallet  :', self.uniqueIDB58
      print indent + '   useEncrypt:', self.useEncryption
      print indent + '   watchOnly :', self.watchingOnly
      print indent + '   isLocked  :', self.isLocked
      print indent + '   ShortLabel:', self.labelName 
      print indent + '   LongLabel :', self.labelDescr
      print ''
      print indent + 'Root key:', self.addrMap['ROOT'].getAddrStr(),
      print '(this address is never used)'
      if allAddrInfo:
         self.addrMap['ROOT'].pprint(indent=indent)
      print indent + 'All usable keys:'
      sortedAddrList = self.getAddrListSortedByChainIndex()
      for i,addr160,addrObj in sortedAddrList:
         if not addr160=='ROOT':
            print '\n' + indent + 'Address:', addrObj.getAddrStr()
            if allAddrInfo:
               addrObj.pprint(indent=indent)



   #############################################################################
   def isEqualTo(self, wlt2, debug=False):
      isEqualTo = True
      isEqualTo = isEqualTo and (self.uniqueIDB58 == wlt2.uniqueIDB58)
      isEqualTo = isEqualTo and (self.labelName  == wlt2.labelName )
      isEqualTo = isEqualTo and (self.labelDescr == wlt2.labelDescr)
      try:

         rootstr1 = binary_to_hex(self.addrMap['ROOT'].serialize())
         rootstr2 = binary_to_hex(wlt2.addrMap['ROOT'].serialize())
         isEqualTo = isEqualTo and (rootstr1 == rootstr2)
         if debug:
            print ''
            print 'RootAddrSelf:'
            print prettyHex(rootstr1, indent=' '*5)
            print 'RootAddrWlt2:'
            print prettyHex(rootstr2, indent=' '*5)
            print 'RootAddrDiff:',
            pprintDiff(rootstr1, rootstr2, indent=' '*5)

         for addr160 in self.addrMap.keys():
            addrstr1 = binary_to_hex(self.addrMap[addr160].serialize())
            addrstr2 = binary_to_hex(wlt2.addrMap[addr160].serialize())
            isEqualTo = isEqualTo and (addrstr1 == addrstr2)
            if debug:
               print ''
               print 'AddrSelf:', binary_to_hex(addr160),
               print prettyHex(binary_to_hex(self.addrMap['ROOT'].serialize()), indent='     ')
               print 'AddrSelf:', binary_to_hex(addr160),
               print prettyHex(binary_to_hex(wlt2.addrMap['ROOT'].serialize()), indent='     ')
               print 'AddrDiff:',
               pprintDiff(addrstr1, addrstr2, indent=' '*5)
      except:
         return False

      return isEqualTo



def pprintLedgerEntry(le, indent=''):
   
   if len(le.getAddrStr20())==20:
      addrStr = hash160_to_addrStr(le.getAddrStr20())[:12]
   else:
      addrStr = ''

   leVal = coin2str(le.getValue(), maxZeros=1)
   txType = ''
   if le.isSentToSelf():
      txType = 'ToSelf'
   else:
      txType = 'Recv' if le.getValue()>0 else 'Sent'

   blkStr = str(le.getBlockNum())
   print indent + 'LE %s %s %s %s' % \
            (addrStr.ljust(15), leVal, txType.ljust(8), blkStr.ljust(8))

"""
class PyLedgerEntry(object):
   def __init__(self):
      self.addr20       = UNINITIALIZED
      self.value        = UNINITIALIZED
      self.blockNum     = UNINITIALIZED
      self.txHash       = UNINITIALIZED
      self.index        = UNINITIALIZED
      self.isValid      = UNINITIALIZED
      self.isSentToSelf = UNINITIALIZED
      self.isChangeBack = UNINITIALIZED

   def createForWalletFromTx(self, wlt, tx):
      numIn  = len(tx.inputs)
      numOut = len(tx.outputs)

      

   //    addr20_    -  useless - originally had a purpose, but lost it
   //    value_     -  total debit/credit on WALLET balance, in Satoshis (1e-8 BTC)
   //    blockNum_  -  block height of the block in which this tx was included
   //    txHash_    -  hash of this tx 
   //    index_     -  index of the tx in the block
   //    isValid_   -  default to true -- invalidated due to reorg/double-spend
   //    isSentToSelf_ - if we supplied inputs and rx ALL outputs
   //    isChangeBack_ - if we supplied inputs and rx ANY outputs
"""




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

   def __init__(self, startCt=-1, hashStartList=[], hashStop=''):
      self.startCount = startCt
      self.hashStart  = hashStartList
      self.hashStop   = hashStop
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         ghData = toUnpack
      else:
         ghData = BinaryUnpacker( toUnpack )

      self.startCount = ghData.get(VAR_INT)
      for i in range(self.startCount):
         self.hashStart.append(ghData.get(BINARY_CHUNK, 32))
      self.hashStop = ghData.get(BINARY_CHUNK, 32)
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_INT, self.startCount)
      for i in range(self.startCount):
         bp.put(BINARY_CHUNK, self.hashStart[i], width=32)
      bp.put(BINARY_CHUNK, self.hashStop, width=32)
      return bp.getBinaryString()
   
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getheaders):'
      print indstr + indent + 'HashStart(s) :' + binary_to_hex(self.hashStart[0])
      for i in range(1,len(self.hashStart)):
         print indstr + indent + '             :' + binary_to_hex(self.hashStart[i])
      print indstr + indent + 'HashStop     :' + binary_to_hex(self.hashStop)
         


################################################################################
################################################################################
class PayloadGetBlocks(object):
   command = 'getblocks'

   def __init__(self, version=1, startCt=-1, hashStartList=[], hashStop=''):
      self.version    = 1
      self.startCount = startCt
      self.hashStart  = hashStartList
      self.hashStop   = hashStop
   

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         gbData = toUnpack
      else:
         gbData = BinaryUnpacker( toUnpack )

      self.version = gbData.get(UINT32)
      self.startCount = gbData.get(VAR_INT)
      for i in range(self.startCount):
         self.hashStart.append(gbData.get(BINARY_CHUNK, 32))
      self.hashStop = gbData.get(BINARY_CHUNK, 32)
      return self

   def serialize(self):
      bp = BinaryPacker()
      bp.put(UINT32, self.version)
      bp.put(VAR_INT, self.startCount)
      for i in range(self.startCount):
         bp.put(BINARY_CHUNK,  self.hashStart[i], width=32)
      bp.put(BINARY_CHUNK, self.hashStart, width=32)
      return bp.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print ''
      print indstr + 'Message(getheaders):'
      print indstr + indent + 'Version      :' + str(self.version)
      print indstr + indent + 'HashStart(s) :' + binary_to_hex(self.hashStart[0])
      for i in range(1,len(self.hashStart)):
         print indstr + indent + '             :' + binary_to_hex(self.hashStart[i])
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
   'alert':       PayloadAlert }





try:
   from twisted.internet.protocol import Protocol, ReconnectingClientFactory
   from twisted.internet.defer import Deferred
except ImportError:
   LOGERROR('***Python-Twisted is not installed -- cannot enable')
   LOGERROR('   networking-related methods for ArmoryEngine' )


################################################################################
def forceDeferred(callbk):
   if callbk:
      if isinstance(callbk, Deferred):
         return callbk
      else:
         d = Deferred()
         d.addCallback(callbk)


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
      self.handshakeFinished = False
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
      msgVersion.subver   = ''
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
      #pprintHex(binary_to_hex(data))

      # Put the current buffer into an unpacker, process until empty
      self.recvData += data
      buf = BinaryUnpacker(self.recvData)

      messages = []
      while True:
         try:
            # recvData is only modified if the unserialize succeeds
            messages.append( PyMessage().unserialize(buf) )
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
      for msg in messages:
         cmd = msg.cmd
         if CLI_OPTIONS.netlog:
            LOGDEBUG( 'DataReceived: %s', msg.payload.command)
            if not msg.payload.command in ['tx','inv']:
               LOGRAWDATA( msg.serialize() )

         # We process version and verackk regardless of handshakeFinished
         if cmd=='version' and not self.handshakeFinished:
            self.sendMessage( PayloadVerack() )
         elif cmd=='verack':
            self.handshakeFinished = True
            self.factory.handshakeFinished(self)

         ####################################################################
         # Don't process any other messages unless the handshake is finished
         if self.handshakeFinished:
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
         #print 'Received inv message'
         invobj = msg.payload
         getdataMsg = PyMessage('getdata')
         for inv in invobj.invList:
            if inv[0]==MSG_INV_BLOCK:
               # We'll hear about the new block via blk0001.dat... and when
               # we do (within 5s), we should purge the zero-conf tx list
               from twisted.internet import reactor
            if inv[0]==MSG_INV_TX and not TheBDM.getTxByHash(inv[1]).isInitialized():
               #print 'Requesting new tx data'
               getdataMsg.payload.invList.append(inv)
         self.sendMessage(getdataMsg)
      if msg.cmd=='tx':
         #print 'Received tx message'
         pytx = msg.payload.tx
         #newAlert = self.factory.checkForDoubleBroadcast(pytx)
         #if newAlert:
            #print '***!!!*** DOUBLE-BROADCAST DETECTED!'
            #print '***!!!*** The person who just send you money may be'
            #print '***!!!*** Attempting to defraud you.  It is especially'
            #print '***!!!*** important that you wait for 6+ confirmations'
            #print '***!!!*** before considering this transaction valid!'
         #else:
         self.factory.func_newTx(pytx)
      if msg.cmd=='block':
         # We don't care much about blocks right now --  We will find
         # out about them when the Satoshi client updates blk0001.dat
         #print 'Received block message (ignoring)'
         pass
                  

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
            if not msg.payload.command in ['tx','inv','getdata']:
               LOGRAWDATA( msg.serialize() )
         self.transport.write(msg.serialize())
      else:
         msg = PyMessage(payload=msg)
         #print '\n\nSending Message:', msg.payload.command.upper()
         #pprintHex(binary_to_hex(msg.serialize()), indent='   ')
         if CLI_OPTIONS.netlog:
            LOGDEBUG( 'SendMessage: %s', msg.payload.command)
            if not msg.payload.command in ['tx','inv','getdata']:
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

   Note that I am implementing a special security feature:  besides collecting
   tx's not in the blockchain yet, I also monitor for double-broadcast events
   which are due to two transactions being sent at the same time with different
   recipients but the same inputs.  
   """
   protocol = ArmoryClient
   doubleBroadcastAlerts = {}  #   map[Addr160]  = txHash
   lastAlert = 0

   #############################################################################
   def __init__(self, \
                def_handshake=None, \
                func_loseConnect=None, \
                func_madeConnect=None, \
                func_newTx=None, \
                func_doubleSpendAlert=None):
      """
      Initialize the ReconnectingClientFactory with a deferred for when the handshake 
      finishes:  there should be only one handshake, and thus one firing 
      of the handshake-finished callback
      """
      self.doubleBroadcastAlerts = {}
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
      self.func_doubleSpendAlert = func_doubleSpendAlert
      self.func_newTx = func_newTx

      self.proto = None

   

   #############################################################################
   def addTxToMemoryPool(self, pytx):
      if TheBDM.isInitialized():
         txHash = pytx.getHash()
         TheBDM.addNewZeroConfTx(pytx.serialize(), RightNow(), True)    
      


   #############################################################################
   def handshakeFinished(self, protoObj):
      LOGINFO('Handshake finished, connection open!')
      self.proto = protoObj
      if self.deferred_handshake:
         d, self.deferred_handshake = self.deferred_handshake, None
         d.callback(protoObj)




   #############################################################################
   # CHANGED ALL THE ZERO-CONF CODE, so this is now broken.  Will re-implement
   # later.
   #def checkForDoubleBroadcast(self, pytxObj):
      #newAlerts = False
      #for txin in pytxObj.inputs:
         #op = (txin.outpoint.txHash, txin.outpoint.txOutIndex)
         #if self.zeroConfTxOutMap.has_key(op):
            ## !!! Someone tried to spend the same inputs twice !!!
            #newAlerts = True
            #self.lastAlert = RightNow()
            #prevHash = self.zeroConfTxOutMap[op]
            #prevTx = zeroConfTx[prevHash]
            #for tx in (pytxObj, prevTx):
               ## Add all recipients from both transactions
               #for txout in tx.outputs:
                  ## Search all the TxOuts for recipients
                  #addr = TxOutScriptExtractAddr160(txout.binScript)
                  #if isinstance(addrs, list):
                     #for addr in addrs:
                        #self.doubleBroadcastAlerts[addr] = tx.getHash()
                  #else:
                     #self.doubleBroadcastAlerts[addrs] = tx.getHash()

      #if self.func_doubleSpendAlert:
         #self.func_doubleSpendAlert()


   #############################################################################
   def clientConnectionLost(self, connector, reason):
      LOGERROR('***Connection to Satoshi client LOST!  Attempting to reconnect...')
      self.func_loseConnect()
      ReconnectingClientFactory.clientConnectionLost(self,connector,reason)

      

   #############################################################################
   def connectionFailed(self, protoObj, reason):
      """
      This method needs some serious work... I don't quite know yet how
      to reopen the connection... and I'll need to copy the Deferred so
      that it is ready for the next connection failure
      """
      LOGERROR('***Initial connection to Satoshi client failed!  Retrying...')
      ReconnectingClientFactory.connectionFailed(self, protoObj, reason)


   #############################################################################
   #def checkForTx(self, txHash):
      #if self.proto:
         #self.proto.sendTx(pytxObj)
      #else:
         #raise ConnectionError, 'Connection to localhost DNE.'
      
      

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


class FakeClientFactory(ReconnectingClientFactory):
   """
   A fake class that has the same methods as an ArmoryClientFactory,
   but doesn't do anything.  If there is no internet, then we want 
   to be able to use the same calls
   """
   #############################################################################
   doubleBroadcastAlerts = {}  #   map[Addr160]  = txHash
   def __init__(self, \
                def_handshake=None, \
                func_loseConnect=None, \
                func_newTx=None, \
                func_doubleSpendAlert=None): pass
   def addTxToMemoryPool(self, pytx): pass
   def handshakeFinished(self, protoObj): pass
   def checkForDoubleBroadcast(self, pytxObj): pass
   def clientConnectionLost(self, connector, reason): pass
   def connectionFailed(self, protoObj, reason): pass
   def sendTx(self, pytxObj): pass


################################################################################
################################################################################
class SettingsFile(object):
   """
   This class could be replaced by the built-in QSettings in PyQt, except
   that older versions of PyQt do not support the QSettings (or at least
   I never figured it out).  Easy enough to do it here

   All settings must populated with a simple datatype -- non-simple 
   datatypes should be broken down into pieces that are simple:  numbers 
   and strings, or lists/tuples of them.

   Will write all the settings to file.  Each line will look like:
         SingleValueSetting1 | 3824.8 
         SingleValueSetting2 | this is a string
         Tuple Or List Obj 1 | 12 $ 43 $ 13 $ 33
         Tuple Or List Obj 2 | str1 $ another str
   """

   #############################################################################
   def __init__(self, path=None):
      self.settingsPath = path
      self.settingsMap = {}
      if not path:
         self.settingsPath = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt') 

      LOGINFO('Using settings file: %s', self.settingsPath)
      if os.path.exists(self.settingsPath):
         self.loadSettingsFile(path)



   #############################################################################
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'Settings:'
      for k,v in self.settingsMap.iteritems():
         print indstr + indent + k.ljust(15), v


   #############################################################################
   def hasSetting(self, name):
      return self.settingsMap.has_key(name)
   
   #############################################################################
   def set(self, name, value):
      if isinstance(value, tuple):
         self.settingsMap[name] = list(value)
      else:
         self.settingsMap[name] = value
      self.writeSettingsFile()

   #############################################################################
   def extend(self, name, value):
      """ Adds/converts setting to list, appends value to the end of it """
      if not self.settingsMap.has_key(name):
         if isinstance(value, list):
            self.set(name, value)
         else:
            self.set(name, [value])
      else:
         origVal = self.get(name, expectList=True)
         if isinstance(value, list):
            origVal.extend(value)
         else:
            origVal.append(value)
         self.settingsMap[name] = origVal
      self.writeSettingsFile()

   #############################################################################
   def get(self, name, expectList=False):
      if not self.hasSetting(name) or self.settingsMap[name]=='':
         return ([] if expectList else '')
      else:
         val = self.settingsMap[name]
         if expectList:
            if isinstance(val, list):
               return val
            else:
               return [val]
         else:
            return val

   #############################################################################
   def getAllSettings(self):
      return self.settingsMap

   #############################################################################
   def getSettingOrSetDefault(self, name, defaultVal, expectList=False):
      output = defaultVal
      if self.hasSetting(name):
         output = self.get(name)
      else:
         self.set(name, defaultVal)

      return output

 



   #############################################################################
   def delete(self, name):
      if self.hasSetting(name):
         del self.settingsMap[name]
      self.writeSettingsFile()

   #############################################################################
   def writeSettingsFile(self, path=None):
      if not path:
         path = self.settingsPath
      f = open(path, 'w')
      for key,val in self.settingsMap.iteritems():
         try:
            # Skip anything that throws an exception
            valStr = '' 
            if isinstance(val, str) or \
               isinstance(val, unicode) or \
               isinstance(val, int) or \
               isinstance(val, float) or \
               isinstance(val, long):
               valStr = str(val)
            elif isinstance(val, list) or \
                 isinstance(val, tuple):
               valStr = ' $  '.join([str(v) for v in val])
            f.write(key.ljust(36) + ' | ' + valStr + '\n')
         except:
            LOGWARN('Invalid entry in SettingsFile... skipping')
      f.close()
      

   #############################################################################
   def loadSettingsFile(self, path=None):
      if not path:
         path = self.settingsPath

      if not os.path.exists(path):
         raise FileExistsError, 'Settings file DNE:', path

      f = open(path, 'rb')
      sdata = f.read()
      f.close()

      # Automatically convert settings to numeric if possible
      def castVal(v):
         v = v.strip()
         a,b = v.isdigit(), v.replace('.','').isdigit()
         if a:   
            return int(v)
         elif b: 
            return float(v)
         else:   
            if v.lower()=='true':
               return True
            elif v.lower()=='false':
               return False
            else:
               return v
         

      sdata = [line.strip() for line in sdata.split('\n')]
      for line in sdata:
         if len(line.strip())==0:
            continue

         try:
            key,vals = line.split('|')
            valList = [castVal(v) for v in vals.split('$')]
            if len(valList)==1:
               self.settingsMap[key.strip()] = valList[0]
            else:
               self.settingsMap[key.strip()] = valList
         except:
            LOGWARN('Invalid setting in %s (skipping...)', path)





################################################################################
################################################################################
# Read Satoshi Wallets (wallet.dat) to import into Armory wallet
# BSDDB wallet-reading code taken from Joric's pywallet:  he declared it 
# public domain. 
#try:
#   from bsddb.db import *
#except ImportError:
#   # Apparently bsddb3 is needed on OSX 
#   from bsddb3.db import *
#
#import json
#import struct
#
#class BCDataStream(object):
#   def __init__(self):
#      self.input = None
#      self.read_cursor = 0
#
#   def clear(self):
#      self.input = None
#      self.read_cursor = 0
#
#   def write(self, bytes):   # Initialize with string of bytes
#      if self.input is None:
#         self.input = bytes
#      else:
#         self.input += bytes
#
#   def map_file(self, file, start):   # Initialize with bytes from file
#      self.input = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
#      self.read_cursor = start
#   def seek_file(self, position):
#      self.read_cursor = position
#   def close_file(self):
#      self.input.close()
#
#   def read_string(self):
#      # Strings are encoded depending on length:
#      # 0 to 252 :   1-byte-length followed by bytes (if any)
#      # 253 to 65,535 : byte'253' 2-byte-length followed by bytes
#      # 65,536 to 4,294,967,295 : byte '254' 4-byte-length followed by bytes
#      # ... and the Bitcoin client is coded to understand:
#      # greater than 4,294,967,295 : byte '255' 8-byte-length followed by bytes of string
#      # ... but I don't think it actually handles any strings that big.
#      if self.input is None:
#         raise SerializationError("call write(bytes) before trying to deserialize")
#
#      try:
#         length = self.read_compact_size()
#      except IndexError:
#         raise SerializationError("attempt to read past end of buffer")
#
#      return self.read_bytes(length)
#
#   def write_string(self, string):
#      # Length-encoded as with read-string
#      self.write_compact_size(len(string))
#      self.write(string)
#
#   def read_bytes(self, length):
#      try:
#         result = self.input[self.read_cursor:self.read_cursor+length]
#         self.read_cursor += length
#         return result
#      except IndexError:
#         raise SerializationError("attempt to read past end of buffer")
#
#      return ''
#
#   def read_boolean(self): return self.read_bytes(1)[0] != chr(0)
#   def read_int16(self): return self._read_num('<h')
#   def read_uint16(self): return self._read_num('<H')
#   def read_int32(self): return self._read_num('<i')
#   def read_uint32(self): return self._read_num('<I')
#   def read_int64(self): return self._read_num('<q')
#   def read_uint64(self): return self._read_num('<Q')
#
#   def write_boolean(self, val): return self.write(chr(1) if val else chr(0))
#   def write_int16(self, val): return self._write_num('<h', val)
#   def write_uint16(self, val): return self._write_num('<H', val)
#   def write_int32(self, val): return self._write_num('<i', val)
#   def write_uint32(self, val): return self._write_num('<I', val)
#   def write_int64(self, val): return self._write_num('<q', val)
#   def write_uint64(self, val): return self._write_num('<Q', val)
#
#   def read_compact_size(self):
#      size = ord(self.input[self.read_cursor])
#      self.read_cursor += 1
#      if size == 253:
#         size = self._read_num('<H')
#      elif size == 254:
#         size = self._read_num('<I')
#      elif size == 255:
#         size = self._read_num('<Q')
#      return size
#
#   def write_compact_size(self, size):
#      if size < 0:
#         raise SerializationError("attempt to write size < 0")
#      elif size < 253:
#          self.write(chr(size))
#      elif size < 2**16:
#         self.write('\xfd')
#         self._write_num('<H', size)
#      elif size < 2**32:
#         self.write('\xfe')
#         self._write_num('<I', size)
#      elif size < 2**64:
#         self.write('\xff')
#         self._write_num('<Q', size)
#
#   def _read_num(self, format):
#      (i,) = struct.unpack_from(format, self.input, self.read_cursor)
#      self.read_cursor += struct.calcsize(format)
#      return i
#
#   def _write_num(self, format, num):
#      s = struct.pack(format, num)
#      self.write(s)
#
#
#################################################################################
#def create_env(wltDir):
#   """ 
#   This appears to set the "environment" for BSDDB:  the directory containing
#   all the DB we plan to open: which in this case is just one:  wallet.dat
#   """
#   db_env = DBEnv(0)
#   r = db_env.open(wltDir, \
#     (DB_CREATE|DB_INIT_LOCK|DB_INIT_LOG|DB_INIT_MPOOL|DB_INIT_TXN|DB_THREAD|DB_RECOVER))
#   return db_env
#
#################################################################################
#def pubkey_to_addrStr(pubKey):
#   a160 = hash160(pubKey)
#   return hash160_to_addrStr(a160)
#
#################################################################################
#def open_wallet(db_env, wltFile):
#   db = DB(db_env)
#   flags = DB_THREAD | DB_RDONLY
#   try:
#      r = db.open(wltFile, "main", DB_BTREE, flags)
#   except DBError:
#      r = True
#
#   if r is not None:
#      LOGERROR("Couldn't open wallet.dat/main. Try quitting Bitcoin and running this again.")
#      sys.exit(1)
#   
#   return db
#
#
#
#################################################################################
#def GetKeyFromPassphraseSatoshi(passwd, vSalt, nIter, deriveMethod):
#   """
#   Returns the encryption (key, IV) to be used to decrypt the master key
#   """
#   if deriveMethod != 0:
#      return 0
#
#   if not isinstance(passwd, str):
#      passwd = passwd.toBinStr()
#
#   data = passwd + vSalt
#   for i in xrange(nIter):
#      data = sha512(data)
#   return data[0:32], data[32:32+16]
#
#
#
#################################################################################
#def read_wallet(db_env, wltFile):
#   db = open_wallet(db_env, wltFile)
#
#   # Moved parse_wallet code inline here
#   kds = BCDataStream()
#   vds = BCDataStream()
#
#   plainPrivList = []
#   cryptPrivList = []
#   masterEncrKey = {}
#   poolKeysList  = []
#   addrNames     = {}
#
#   wltNetByte = None
#   for (key, value) in db.items():
#      d = { }
#
#      kds.clear()
#      vds.clear()
#      kds.write(key)
#      vds.write(value)
#
#      dType = kds.read_string()
#
#      d["__key__"] = key
#      d["__value__"] = value
#      d["__type__"] = dType
#
#
#      if dType == "key":
#         priv = SecureBinaryData(vds.read_bytes(vds.read_compact_size())[9:9+32])
#         plainPrivList.append(priv)
#      elif dType == "ckey":
#         pub = kds.read_bytes(kds.read_compact_size())
#         ckey = vds.read_bytes(vds.read_compact_size())
#         cryptPrivList.append( [pub, ckey] )
#      elif dType == "mkey":
#         masterEncrKey['mkey'] = vds.read_bytes(vds.read_compact_size())
#         masterEncrKey['salt'] = vds.read_bytes(vds.read_compact_size())
#         masterEncrKey['mthd'] = vds.read_int32()
#         masterEncrKey['iter'] = vds.read_int32()
#         masterEncrKey['othr'] = vds.read_bytes(vds.read_compact_size())
#      elif dType == "pool":
#         d['n'] = kds.read_int64()
#         ver = vds.read_int32()
#         ntime = vds.read_int64()
#         pubkey = vds.read_bytes(vds.read_compact_size())
#         poolKeysList.append(pubkey_to_addrStr(pubkey))
#      elif dType == "name":
#         addrB58 = kds.read_string()
#         name    = vds.read_string()
#         addrNames[addrB58] = name
#         wltNetByte = base58_to_binary(addrB58)[0]
#         if not wltNetByte==ADDRBYTE:
#            s = 'Wallet is for a different network!  ' 
#            if NETWORKS.has_key(wltNetByte):
#               s += '(for network: %s)' %  NETWORKS[wltNetByte]
#            raise NetworkIDError, s
#      else:
#         pass
#
#   db.close()
#
#   return (plainPrivList, masterEncrKey, cryptPrivList, poolKeysList, addrNames)
#
#
#
#
#
#
#def extractSatoshiKeys(wltPath, passphrase=None):
#   # Returns a list of [privKey, usedYet] pairs
#   if not os.path.exists(wltPath):
#      raise FileExistsError, 'Specified Satoshi wallet does not exist!'
#
#   wltDir,wltFile = os.path.split(wltPath)
#
#   db_env = create_env(wltDir) 
#
#   plainkeys,mkey,crypt,pool,names = read_wallet(db_env, wltFile)
#   
#   if len(crypt)>0:
#      # Satoshi Wallet is encrypted!
#      plainkeys = []
#      if not passphrase:
#         raise EncryptionError, 'Satoshi wallet is encrypted but no passphrase supplied'
#      
#      pKey,IV = GetKeyFromPassphraseSatoshi( passphrase, \
#                                             mkey['salt'], \
#                                             mkey['iter'], \
#                                             mkey['mthd'])
#
#      masterKey = CryptoAES().DecryptCBC( SecureBinaryData(mkey['mkey']), \
#                                          SecureBinaryData(pKey), \
#                                          SecureBinaryData(IV) )
#      masterKey.resize(32)
#
#      checkedCorrectPassphrase = False
#      for pub,ckey in crypt:
#         iv = hash256(pub)[:16]
#         privKey = CryptoAES().DecryptCBC( SecureBinaryData(ckey), \
#                                           SecureBinaryData(masterKey), \
#                                           SecureBinaryData(iv))
#         privKey.resize(32)
#         if not checkedCorrectPassphrase:
#            checkedCorrectPassphrase = True
#            if not CryptoECDSA().CheckPubPrivKeyMatch(privKey, SecureBinaryData(pub)):
#               raise EncryptionError, 'Incorrect Passphrase!'
#         plainkeys.append(privKey)
#
#   outputList = []
#   for key in plainkeys:
#      addr = hash160_to_addrStr(convertKeyDataToAddress(key.toBinStr()))
#      strName = ''
#      if names.has_key(addr):
#         strName = names[addr] 
#      outputList.append( [addr, key, (not addr in pool), strName] )
#   return outputList
#         
#
#
#def checkSatoshiEncrypted(wltPath):
#   try:
#      extractSatoshiKeys(wltPath, '')
#      return False
#   except EncryptionError:
#      return True





class PyBackgroundThread(threading.Thread):
   """
   Define a thread object that will execute a preparatory function
   (blocking), and then a long processing thread followed by something
   to do when it's done (both non-blocking).  After the 3 methods and 
   their arguments are set, use obj.start() to kick it off.
   """
   
   def __init__(self, *args, **kwargs):
      threading.Thread.__init__(self)

      self.preFunc  = lambda: ()
      self.postFunc = lambda: ()

      if len(args)==0:
         self.func  = lambda: ()
      else:
         if not hasattr(args[0], '__call__'):
            raise TypeError, ('PyBkgdThread constructor first arg '
                              '(if any) must be a function')
         else:
            self.setThreadFunction(args[0], *args[1:], **kwargs)

   def setPreThreadFunction(self, prefunc, *args, **kwargs):
      def preFuncPartial():
         prefunc(*args, **kwargs)
      self.preFunc = preFuncPartial

   def setThreadFunction(self, thefunc, *args, **kwargs):
      def funcPartial():
         thefunc(*args, **kwargs)
      self.func = funcPartial

   def setPostThreadFunction(self, postfunc, *args, **kwargs):
      def postFuncPartial():
         postfunc(*args, **kwargs)
      self.postFunc = postFuncPartial


   def run(self):
      print 'Executing thread.run()...'
      self.func()
      self.postFunc()

   def start(self):
      print 'Executing thread.start()...'
      # This is blocking: we may want to guarantee that something critical 
      #                   is in place before we start the thread
      self.preFunc()
      super(PyBackgroundThread, self).start()

      



################################################################################
# Let's create a thread-wrapper for the blockchain utilities.  Enable the
# ability for multi-threaded blockchain scanning -- have a main thread and 
# a blockchain thread:  blockchain can scan, and main thread will check back
# every now and then to see if it's done

import Queue
BLOCKCHAINMODE  = enum('Offline', \
                       'Uninitialized', \
                       'Full', \
                       'Rescanning', \
                       'FullPrune', \
                       'Lite')

BDMINPUTTYPE  = enum('RegisterAddr', \
                     'ZeroConfTxToInsert', \
                     'HeaderRequested', \
                     'TxRequested', \
                     'BlockRequested', \
                     'StartScanRequested', \
                     'RescanRequested', \
                     'UpdateWallets', \
                     'ReadBlkUpdate', \
                     'GoOnlineRequested', \
                     'GoOfflineRequested', \
                     'Passthrough', \
                     'Reset')

################################################################################
class BlockDataManagerThread(threading.Thread):
   """ 
   Serves as a layer between the GUI and the Blockchain utilities.
   If a request is made to mess with the BDM while it is in the 
   middle of scanning, it will queue it for when it's done
   """
   #############################################################################
   def __init__(self, isOffline=False, blocking=False):
      super(BlockDataManagerThread, self).__init__()

      if isOffline:
         self.blkMode = BLOCKCHAINMODE.Offline
      else:
         self.blkMode = BLOCKCHAINMODE.Uninitialized

      self.bdm = Cpp.BlockDataManager().getBDM()

      # These are for communicating with the master (GUI) thread
      self.inputQueue  = Queue.Queue()
      self.outputQueue = Queue.Queue()

      # Flags
      self.doShutdown   = False
      self.isDirty      = False
      self.allowRescan  = True
      self.startBDM     = False
      self.blkdir       = BTC_HOME_DIR
      self.blocking     = blocking

      # Lists of wallets that should be checked after blockchain updates
      self.pyWltList    = []   # these will be python refs
      self.cppWltList   = []   # these will be python refs

      # The BlockDataManager is easier to use if you put all your addresses
      # into a C++ BtcWallet object, and let it 
      self.masterCppWallet = Cpp.BtcWallet()
       


   #############################################################################
   def __getattr__(self, name):
      '''
      Anything that is not explicitly defined in this class should 
      passthrough to the C++ BlockDataManager class

      This remaps such calls into "passthrough" requests via the input
      queue.  This makes sure that the requests are processed only when
      the BDM is ready.  Hopefully, this will prevent multi-threaded
      disasters, such as seg faults due to trying to read memory that is
      in the process of being updated.
   
      Specifically, any passthrough call is expected to return output
      unless you add 'waitForReturn=False' to the arg list
      '''
      if not hasattr(self.bdm, name):
         LOGERROR('No BDM method: %s', name)
         raise
      else:
         def passthruFunc(*args, **kwargs):
            self.inputQueue.put([BDMINPUTTYPE.Passthrough, name] + args)
            waitForReturn = True
            if len(kwargs)>0 and \
               kwargs.has_key('waitForReturn') and \
               not kwargs['waitForReturn']:
               waitForReturn = False

            if waitForReturn:
               try:
                  return self.outputQueue.get(True, 1)
               except Queue.Empty:
                  LOGERROR('BDM was not ready for your request!  Waited 1 sec.')
                  return self.outputQueue.get()
         return passthruFunc

      

   #############################################################################
   def Reset(self, waitForComplete=None):
      self.inputQueue.put([BDMINPUTTYPE.Reset])

      if waitForComplete==None:
         waitForComplete = self.blocking
      if waitForComplete:
         self.inputQueue.join()

   #############################################################################
   def getBlkMode(self):
      return self.blkMode

   #############################################################################
   def getBlkModeStr(self):
      if   self.blkMode == BLOCKCHAINMODE.Offline:
         return 'Offline'
      elif self.blkMode == BLOCKCHAINMODE.Full:
         return 'Full'
      elif self.blkMode == BLOCKCHAINMODE.Rescanning:
         return 'Rescanning'
      elif self.blkMode == BLOCKCHAINMODE.Uninitialized:
         return 'Uninitialized'
      elif self.blkMode == BLOCKCHAINMODE.FullPrune:
         return 'FullPrune'
      elif self.blkMode == BLOCKCHAINMODE.Lite:
         return 'Lite'
      else:
         return '<UNKNOWN: %d>' % self.blkMode

      
   #############################################################################
   def execCleanShutdown(self):
      self.doShutdown = True

   #############################################################################
   def setSatoshiDir(self, blkdir):
      if not os.path.exists(blkdir):
         LOGERROR('setSatoshiDir: directory does not exist: %s', blkdir)
         return
      self.blkdir = blkdir

   #############################################################################
   def setOnlineMode(self, goOnline=True):
      if goOnline:
         self.inputQueue.put(BDMINPUTTYPE.GoOnlineRequested)
      else:
         self.inputQueue.put(BDMINPUTTYPE.GoOfflineRequested)

      if self.blocking:
         self.inputQueue.join()
   
   #############################################################################
   def isBusy(self):
      return (self.blkMode==BLOCKCHAINMODE.Rescanning)

   #############################################################################
   def isInitialized(self):
      return self.blkMode==BLOCKCHAINMODE.Full and self.bdm.isInitialized()

   #############################################################################
   def needsRescan(self):

      if self.blkMode == BLOCKCHAINMODE.Offline:
         LOGWARN('Asked if BDM needs rescan, but BDM is in offline mode')

      return self.isDirty


   #############################################################################
   def loadBlockchain(self, waitForComplete=None):
      self.inputQueue.put([BDMINPUTTYPE.StartScanRequested])
      print 'Initial blockchain load requested'

      if waitForComplete==None:
         waitForComplete = self.blocking
      if waitForComplete:
         self.inputQueue.join()


   #############################################################################
   def rescanBlockchain(self, waitForComplete=None):
      self.inputQueue.put([BDMINPUTTYPE.RescanRequested])
      print 'Blockchain rescan requested'

      if waitForComplete==None:
         waitForComplete = self.blocking
      if waitForComplete:
         self.inputQueue.join()



   #############################################################################
   def __checkBDMReadyToServeData(self):
      if self.blkMode==BLOCKCHAINMODE.Rescanning:
         LOGERROR('Requested blockchain data while scanning.  Don\'t do this!')
         LOGERROR('Check self.getBlkModeStr()==BLOCKCHAINMODE.Full before')
         LOGERROR('making requests!  Skipping request')
         return False
      if self.blkMode==BLOCKCHAINMODE.Offline:
         LOGERROR('Requested blockchain data while BDM is in offline mode.')
         LOGERROR('Please start the BDM using TheBDM.loadBlockchain() before,')
         LOGERROR('and then wait for it to complete, before requesting data.')
         return False
      if not self.bdm.isInitialized():
         LOGERROR('The BDM thread declares the BDM is ready, but the BDM ')
         LOGERROR('itself reports that it is not initialized!  What is ')
         LOGERROR('going on...?')
         return False
         

      return True

   #############################################################################
   def getTxByHash(self, txHash):
      if not self.__checkBDMReadyToServeData():
         return None

      self.inputQueue.put([BDMINPUTTYPE.TxRequested, txHash])

      try:
         result = self.outputQueue.get(True, 3)
         if result==None:
            LOGERROR('Requested tx does not exist:\n%s', binary_to_hex(txHash))
         return result
      except Queue.Empty:
         LOGERROR('Waited 3s for tx to be returned.  Abort')
         
      return None

   ############################################################################
   def getHeaderByHash(self, headHash):
      if not self.__checkBDMReadyToServeData():
         return None

      self.inputQueue.put([BDMINPUTTYPE.HeaderRequested, headHash])

      try:
         result = self.outputQueue.get(True, 3)
         if result==None:
            LOGERROR('Requested header does not exist:\n%s', \
                                          binary_to_hex(headHash))
         return result
      except Queue.Empty:
         LOGERROR('Waited 3s for header to be returned.  Abort')

      return None


   #############################################################################
   def getBlockByHash(self,headHash):
      if not self.__checkBDMReadyToServeData():
         return None

      self.inputQueue.put([BDMINPUTTYPE.BlockRequested, headHash])

      try:
         result = self.outputQueue.get(True, 3)
         if result==None:
            LOGERROR('Requested block does not exist:\n%s', \
                                          binary_to_hex(headHash))
         return result
      except Queue.Empty:
         LOGERROR('Waited 3s for block to be returned.  Abort')

      return None



   #############################################################################
   def addNewZeroConfTx(self, rawTx, waitForComplete=None):
      self.inputQueue.put([BDMINPUTTYPE.ZeroConfTxToInsert, rawTx])
      
      if waitForComplete==None:
         waitForComplete = self.blocking
      if waitForComplete:
         self.inputQueue.join()
 
   #############################################################################
   def registerNewAddresses(self, addr160List):
      """
      Variable isFresh==True means the address was just [freshly] created,
      and we need to watch for transactions with it, but we don't need
      to rescan any blocks
      """
      if isinstance(addr160List, str):
         # Not actually a list, just a single addr
         addr160List = [addr160List]

      for a160 in addr160List:
         self.inputQueue.put([BDMINPUTTYPE.RegisterAddr, a160, isFresh])

      if self.blocking:
         self.inputQueue.join()


   #############################################################################
   def registerImportedAddress(self, addr160, \
                                     firstTime=UINT32_MAX, \
                                     firstBlk=UINT32_MAX, \
                                     lastTime=0, \
                                     lastBlk=0):
      """
      TODO:  Need to clean up the first/last blk/time variables.  Rather,
             I need to make sure they are maintained and applied intelligently
             and consistently
      """
      self.inputQueue.put([BDMINPUTTYPE.RegisterAddr, a160, \
                                   [firstTime, firstBlk, lastTime, lastBlk]])

      if self.blocking:
         self.inputQueue.join()
         
   #############################################################################
   def registerWallet(self, wlt, isFresh=False):
      if isinstance(wlt, PyBtcWallet):
         addrs = [a.getAddrStr() for a in wlt.getAddrList()]
         addrs.remove('ROOT')
         self.registerAddresses(addrs, isFresh)
         self.pyWltList.append(wlt)
      elif isinstance(wlt, Cpp.BtcWallet):
         naddr = wlt.getNumAddr()
         for a in range(naddr):
            self.registerAddresses(wlt.getAddrByIndex(a).getAddrStr20(), isFresh)
         self.cppWltList.appen(wlt)
      else:
         LOGERROR('Unrecognized object passed to registerWallet function')
               

      if self.blocking:
         self.inputQueue.join()
   
   #############################################################################
   def __registerAddressNow(self, a160, timeInfo):
      """
      Do the registration right now.  This should not be called directly
      outside of this class.  This is only called by the BDM thread when
      any previous scans have been completed
      """
      if self.blkMode == BLOCKCHAINMODE.Rescanning:
         LOGCRIT('Called __registerAddressNow while rescanning!')
         LOGCRIT('This shouldn\'t happen...')
         LOGCRIT('Aborting address registration.')
         return

      if isinstance(timeInfo, bool):
         isFresh = timeInfo
         if isFresh:
            # We claimed to have just created this address...(so no rescan needed)
            self.masterCppWallet.addNewAddress(a160)
         else:
            self.isDirty = True
            self.masterCppWallet.addAddress_1_(a160)
      else:
         self.isDirty = True
         if isinstance(timeInfo, (list,tuple)) and len(timeInfo)==4:
            self.masterCppWallet.addAddress_5_(a160, *timeInfo)
         else:
            LOGWARN('Unrecognized time information in register method.')
            LOGWARN('   Data: %s', str(timeInfo))
            LOGWARN('Assuming imported key requires full rescan...')
            self.masterCppWallet.addAddress_1_(a160)

      
   #############################################################################
   def __switchFromOfflineToOnline(self):
      if self.blkMode == BLOCKCHAINMODE.Offline:
         if self.bdm.isInitialized():
            self.blkMode = BLOCKCHAINMODE.Rescanning
         else:
            self.blkMode = BLOCKCHAINMODE.Uninitialized
             
         self.blkMode = BLOCKCHAINMODE.Uninitialized


   #############################################################################
   def __startLoadBlockchain(self):
      """
      This should only be called by the threaded BDM, and thus there should
      never be a conflict.  But we check for it, anyway.
      """
      if self.blkMode == BLOCKCHAINMODE.Rescanning:
         LOGERROR('Blockchain is already scanning.  Was this called already?')         
         return
      elif self.blkMode == BLOCKCHAINMODE.Full:
         LOGERROR('Blockchain has already been loaded -- maybe we meant')
         LOGERROR('to call startRescanBlockchain()...?')
         return
      elif not self.blkMode == BLOCKCHAINMODE.Uninitialized:
         LOGERROR('BDM should be in "Uninitialized" mode before starting ')
         LOGERROR('the initial scan.  If BDM is in offline mode, you should ')
         LOGERROR('switch it to online-mode, first, then request the scan.')
         LOGERROR('Continuing with the scan, anyway.')
         

      # Use default home dir if nothing specified
      if self.blkdir==None:
         self.blkdir = BTC_HOME_DIR

      # Check for the existence of the Bitcoin-Qt directory
      if not os.path.exists(self.blkdir):
         raise FileExistsError, ('Directory does not exist: %s' % self.blkdir)

      # ... and its blk000X.dat files
      blk0001file = os.path.join(self.blkdir,'blk0001.dat')
      if not os.path.exists(blk0001file):
         self.blkMode = BLOCKCHAINMODE.Offline
         raise FileExistsError, ('Blockchain data not available: %s' % blk0001file)

      # We have the data, we're ready to go
      self.blkMode = BLOCKCHAINMODE.Rescanning
      self.bdm.SetBtcNetworkParams( GENESIS_BLOCK_HASH, \
                                    GENESIS_TX_HASH,    \
                                    MAGIC_BYTES)
     
      ### This is the part that takes forever
      self.bdm.parseEntireBlockchain(self.blkdir)

      # If the user registered new addresses/wallets since blockchain scanning
      # started, then start a rescan...
      if self.isDirty and self.allowRescan:
         self.__startRescanBlockchain(True)

      self.blkMode = BLOCKCHAINMODE.Full

      
   #############################################################################
   def __startRescanBlockchain(self):
      """
      This should only be called by the threaded BDM, and thus there should
      never be a conflict.  But we check for it, anyway.
      """
      if self.blkMode==BLOCKCHAINMODE.Rescanning:
         LOGERROR('Blockchain is in the middle of rescanning, cannot rescan!')
      elif self.blkMode==BLOCKCHAINMODE.Offline:
         LOGERROR('Blockchain is in offline mode.  How can we rescan?')
      elif self.blkMode==BLOCKCHAINMODE.Uninitialized:
         LOGERROR('Blockchain was never loaded.  Why did we request rescan?')

      if not self.allowRescan:
         LOGERROR('Rescan requested but allowRescan=False.  Aborting')
         return

      if not self.isDirty:
         LOGWARN('It does not look like we need a rescan... doing it anyway')

      self.blkMode = BLOCKCHAINMODE.Rescanning

      # Blockchain will rescan as much as it needs.  Then walk through all 
      self.bdm.scanBlockchainForTx(self.masterCppWallet)
      self.isDirty = False

   

   #############################################################################
   def __readBlockfileUpdates(self):
      ''' 
      This method can be blocking... it always has been without a problem
      However, this method is called from outside the thread, hoping that 
      the blkmode will prevent a threading conflict... 
      ''' 
      if self.blkMode in (BLOCKCHAINMODE.Rescanning, BLOCKCHAINMODE.Offline):
         LOGERROR('Can\'t update blockchain in %s mode!', self.getBlkModeStr())
         return

      nblk = self.bdm.readBlkFileUpdate() 
      return nblk
         

   #############################################################################
   def __updateWalletsAfterScan(self):
      """
      We make this a separate method so that the caller can choose when to 
      invoke it: perhaps to avoid headaches with multithreading 
      (i.e. if this thread was responsible for calling it after it's done
      scanning, the user might be in the middle of importing keys, etc, which
      might cause race conditions)
      """

      for pyWlt in self.pyWltList:
         self.bdm.scanRegisteredTxForWallet(pyWlt.cppWallet)

      for cppWlt in self.cppWltList:
         self.bdm.scanRegisteredTxForWallet(cppWlt)


   #############################################################################
   def __shutdown(self):
      self.bdm.Reset()
      self.blkMode = BLOCKCHAINMODE.Offline
      self.startBDM = False

   #############################################################################
   def __getFullBlock(self, headerHash):
      headerObj = self.bdm.getHeaderByHash(headerHash)
      if not headerObj:
         return None

      rawTxList = []
      txList = headerObj.getTxRefPtrList()
      for txref in txList:
         tx = txref.getTxCopy() 
         rawTxList.append(tx.serialize())

      numTxVarInt = len(rawTxList)
      blockBytes = 80 + len(numTxVarInt) + sum([len(tx) for tx in rawTxList])

      rawBlock  = MAGIC_BYTES
      rawBlock += int_to_hex(blockBytes, endOut=LITTLEENDIAN, widthBytes=4)
      rawBlock += headerObj.serialize() 
      rawBlock += packVarInt(numTx)  
      rawBlock += ''.join(rawTxList)
      return rawBlock

   #############################################################################
   def run(self):
      # Let's define input and output commands via the Queue

      while not self.doShutdown:
         try:
            # Each iteration blocks for 0.05s in a CPU-friendly way
            inputTuple = self.inputQueue.get(True, 0.05)

            if not isinstance(inputTuple, (list,tuple)):
               inputTuple = [inputTuple]

            expectOutput = False
            cmd = inputTuple[0]

            if cmd == BDMINPUTTYPE.RegisterAddr:
               expectOutput = False
               a160,timeInfo = inputTuple[1:]
               self.__registerAddressNow(a160, timeInfo)

            elif cmd == BDMINPUTTYPE.ZeroConfTxToInsert:
               expectOutput = False
               rawTx = inputTuple[1]
               if isinstance(txObj, PyTx):
                  rawTx = txObj.serialize()
               self.bdm.addNewZeroConfTx(rawTx, long(RightNow()), True)
               
            elif cmd == BDMINPUTTYPE.HeaderRequested:
               expectOutput = True
               headHash = inputTuple[1]
               rawHeader = self.bdm.getHeaderByHash(headHash)
               if rawHeader:
                  self.outputQueue.put(rawHeader.serialize())
               else:
                  self.outputQueue.put(None)

            elif cmd == BDMINPUTTYPE.TxRequested:
               expectOutput = True
               txHash = inputTuple[1] 
               rawTx = self.bdm.getTxByHash(txHash)
               if rawTx:
                  self.outputQueue.put(rawTx.serialize()) 
               else:
                  self.outputQueue.put(None)
                  
            elif cmd == BDMINPUTTYPE.BlockRequested:
               expectOutput = True
               headHash = inputTuple[1] 
               rawBlock = self.__getFullBlock(headHash)
               if rawBlock:
                  self.outputQueue.put(rawBlock)
               else:
                  self.outputQueue.put(None)
                  LOGERROR('Requested header does not exist:\n%s', \
                                             binary_to_hex(headHash))
         
            elif cmd == BDMINPUTTYPE.UpdateWallets:
               expectOutput = False
               self.__updateWalletsAfterScan()

            elif cmd == BDMINPUTTYPE.StartScanRequested:
               expectOutput = False
               self.__startLoadBlockchain()

            elif cmd == BDMINPUTTYPE.RescanRequested:
               expectOutput = False
               self.allowRescan = True
               self.__startRescanBlockchain()

            elif cmd == BDMINPUTTYPE.ReadBlkUpdate:
               expectOutput = True
               nBlkRead = self.__readBlockfileUpdates()
               self.outputQueue.put(nBlkRead)

            elif cmd == BDMINPUTTYPE.Passthrough:
               expectOutput = True
               funcName = inputTuple[1]
               funcArgs = inputTuple[2:]
               result = getattr(self.bdm, funcName)(*funcArgs)
               self.outputQueue.put(result) # may be None

            elif cmd == BDMINPUTTYPE.Reset:
               expectOutput = False
               self.bdm.Reset()
               
               if isOffline:
                  self.blkMode = BLOCKCHAINMODE.Offline
               else:
                  self.blkMode = BLOCKCHAINMODE.Uninitialized
         
               # Flags
               self.isDirty      = False
               self.allowRescan  = True
               self.startBDM     = False
               self.blkdir       = BTC_HOME_DIR
         
               # Lists of wallets that should be checked after blockchain updates
               self.pyWltList    = []   # these will be python refs
               self.cppWltList   = []   # these will be python refs
         
               # The BlockDataManager is easier to use if you put all your addresses
               # into a C++ BtcWallet object, and let it 
               self.masterCppWallet = Cpp.BtcWallet()
               
            elif cmd == BDMINPUTTYPE.GoOnlineRequested:
               expectOutput = False
               if self.bdm.isInitialized():
                  self.blkMode = BLOCKCHAINMODE.Full
                  nBlkRead = self.__readBlockfileUpdates()

            elif cmd == BDMINPUTTYPE.GoOfflineRequested:
               expectOutput = False
               self.blkMode = BLOCKCHAINMODE.Offline

            # Let any blocking join() know that this queue entry is done
            self.inputQueue.task_done()

         except Queue.Empty:
            continue
         except:
            LOGERROR('Error processing BDM input')
            LOGERROR('Received inputTuple: ' + str(inputTuple))
            LOGEXCEPT('Exception raised, attempting to continue anyway')
            if expectOutput:
               self.outputQueue.put(None)
            self.inputQueue.task_done()
            continue
           
      LOGINFO('Shutting down the BlockDataManager')
      self.__shutdown()
      LOGINFO('Complete.  Now in offline mode')
      
         



################################################################################
# Make TheBDM reference the asyncrhonous BlockDataManager wrapper if we are 
# running 

if CLI_OPTIONS.offline:
   LOGINFO('Armory loaded in offline-mode.  Will not attempt to load ')
   LOGINFO('blockchain without explicit command to do so.')
   TheBDM = BlockDataManagerThread(isOffline=True)
   TheBDM.start()
else:
   LOGINFO('Using the asynchronous/multi-threaded BlockDataManager.')
   LOGINFO('Blockchain operations will happen in the background.  ')
   LOGINFO('Devs: check TheBDM.blkMode before querying for any data.')
   LOGINFO('Registering addresses during rescans will queue them for ')
   LOGINFO('inclusing after the current scan is completed.')
   TheBDM = BlockDataManagerThread()
   TheBDM.start()









