################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import optparse
import os
import platform
import sys

from Constants import *
from Exceptions import *

try:
   if os.path.exists('update_version.py') and os.path.exists('.git'):
      subprocess.check_output(["python", "update_version.py"])
except:
   pass

try:
   from ArmoryBuild import ARMORY_BUILD
except:
   ARMORY_BUILD = None

def isWindows():
   return ARMORY_OPTIONS.isWindows

def isLinux():
   return ARMORY_OPTIONS.isLinux

def isMac():
   return ARMORY_OPTIONS.isMac

def getOS():
   if isWindows():
      return 'Windows'
   elif isLinux():
      return 'Linux'
   elif isMac():
      return 'MacOSX'
   else:
      return 'Unknown'

def getOSVariant():
   return ARMORY_OPTIONS.osVariant

def getTestnetFlag():
   return ARMORY_OPTIONS.testnet

def useTestnet():
   ARMORY_OPTIONS.testnet = True
   DEFAULT_CHILDPOOLSIZE['ABEK_StdChainExt'] = 5
   DEFAULT_CHILDPOOLSIZE['ABEK_StdChainInt'] = 2

def useMainnet():
   ARMORY_OPTIONS.testnet = False
   DEFAULT_CHILDPOOLSIZE['ABEK_StdChainExt'] = 100
   DEFAULT_CHILDPOOLSIZE['ABEK_StdChainInt'] = 5

def getMagicBytes():
   if getTestnetFlag():
      return '\x0b\x11\x09\x07'
   else:
      return '\xf9\xbe\xb4\xd9'

def getGenesisBlockHash():
   if getTestnetFlag():
      return 'CI\x7f\xd7\xf8&\x95q\x08\xf4\xa3\x0f\xd9\xce\xc3\xae' \
         '\xbay\x97 \x84\xe9\x0e\xad\x01\xea3\t\x00\x00\x00\x00'
   else:
      return 'o\xe2\x8c\n\xb6\xf1\xb3r\xc1\xa6\xa2F\xaec\xf7O\x93' \
         '\x1e\x83e\xe1Z\x08\x9ch\xd6\x19\x00\x00\x00\x00\x00'

def getGenesisTxHash():
   # TODO:  The testnet genesis tx hash can't be the same...?
   return ';\xa3\xed\xfdz{\x12\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3' \
      '\x88\x8aQ2:\x9f\xb8\xaaK\x1e^J'

def getAddrByte():
   return '\x6f' if getTestnetFlag() else '\x00'

def getP2SHByte():
   return '\xc4' if getTestnetFlag() else '\x05'

def getPrivKeyByte():
   return '\xef' if getTestnetFlag() else '\x80'

# This will usually just be used in the GUI to make links for the user
def getBlockExplorer():
   if getTestnetFlag():
      return 'blockexplorer.com'
   else:
      return 'blockchain.info'

def getBlockExplorerTxURL():
   if getTestnetFlag():
      return 'http://blockexplorer.com/testnet/tx/%s'
   else:
      return 'https://blockchain.info/tx/%s'

def getBlockExplorerAddrURL():
   if getTestnetFlag():
      return 'http://blockexplorer.com/testnet/address/%s'
   else:
      return 'https://blockchain.info/address/%s'

def getBIP32MagicPub():
   if getTestnetFlag():
      return '\x04\x35\x87\xcf'
   else:
      return '\x04\x88\xb2\x1e'

def getBIP32MagicPrv():
   if getTestnetFlag():
      return '\x04\x35\x83\x94'
   else:
      return '\x04\x88\xad\xe4'


def getBitcoinPort():
   if ARMORY_OPTIONS.satoshiPort == DEFAULT:
      return 18333 if getTestnetFlag() else 8333
   else:
      return ARMORY_OPTIONS.satoshiPort

def setBitcoinPort(val):
   ARMORY_OPTIONS.satoshiPort = int(val)

def getBitcoinRPCPort():
   if ARMORY_OPTIONS.satoshiRpcport == DEFAULT:
      return 18332 if getTestnetFlag() else 8332
   else:
      return ARMORY_OPTIONS.satoshiRpcport

def getRPCPort():
   if ARMORY_OPTIONS.rpcport == DEFAULT:
      return 18225 if getTestnetFlag() else 8225
   else:
      return ARMORY_OPTIONS.rpcport

def getInterPort():
   if ARMORY_OPTIONS.interport == DEFAULT:
      return 8224 if getTestnetFlag() else 8223
   else:
      return ARMORY_OPTIONS.interport

def getUserHomeDir():
   return ARMORY_OPTIONS.userHomeDir

def getBitcoinHomeDir():
   home = ''
   if ARMORY_OPTIONS.satoshiHome != DEFAULT:
      home = ARMORY_OPTIONS.satoshiHome
   elif isLinux():
      home = os.path.join(getUserHomeDir(), '.bitcoin')
   else:
      home = os.path.join(getUserHomeDir(), 'Bitcoin')
   if getTestnetFlag():
      return os.path.join(home, 'testnet3')
   else:
      return home

def setBitcoinHomeDir(val):
   ARMORY_OPTIONS.satoshiHome = val

def getArmoryHomeDir():
   if ARMORY_OPTIONS.datadir != DEFAULT:
      return ARMORY_OPTIONS.datadir
   elif isLinux():
      if getTestnetFlag():
         return os.path.join(getUserHomeDir(), '.armory', 'testnet3')
      else:
         return os.path.join(getUserHomeDir(), '.armory')
   else:
      if getTestnetFlag():
         return os.path.join(getUserHomeDir(), 'Armory', 'testnet3')
      else:
         return os.path.join(getUserHomeDir(), 'Armory') 

def setArmoryHomeDir(val):
   ARMORY_OPTIONS.datadir = val

def getBlockFileDir():
   return os.path.join(getBitcoinHomeDir(), 'blocks')

def getArmoryDatabaseDir():
   if ARMORY_OPTIONS.armoryDBDir == DEFAULT:
      return os.path.join(getArmoryHomeDir(), 'databases')
   else:
      return ARMORY_OPTIONS.armoryDBDir

def getArmoryLogFile():
   if ARMORY_OPTIONS.logFile == DEFAULT:
      if getExecutedScript() in ['ArmoryQt.py', 'ArmoryQt.exe', 'Armory.exe']:
         return os.path.join(getArmoryHomeDir(), 'armorylog.txt')
      else:
         basename = os.path.basename(getExecutedScript())
         return os.path.join(getArmoryHomeDir(), '%s.log.txt' % basename)
   else:
      return ARMORY_OPTIONS.logFile

def getArmoryCppLogFile():
   return os.path.join(getArmoryHomeDir(), 'armorycpplog.txt')

def getMultLogFile():
   return os.path.join(getArmoryHomeDir(), 'multipliers.txt')

def getSettingsPath():
   if ARMORY_OPTIONS.settingsPath == DEFAULT:
      return os.path.join(getArmoryHomeDir(), 'ArmorySettings.txt')
   else:
      return ARMORY_OPTIONS.settingsPath

def getMultiSigFile():
   if ARMORY_OPTIONS.multisigFile == DEFAULT:
      return os.path.join(getArmoryHomeDir(), 'multisigs.txt')
   else:
      return ARMORY_OPTIONS.multisigFile

def getTestAnnounceFlag():
   return ARMORY_OPTIONS.testAnnounceCode

def setTestAnnounceFlag(val):
   ARMORY_OPTIONS.testAnnounceCode = val

def getAnnounceSignPubKey():
   if getTestAnnounceFlag():
      return ARMORY_TEST_SIGN_PUBLICKEY
   else:
      return ARMORY_INFO_SIGN_PUBLICKEY

def getAnnounceURL():
   if getTestAnnounceFlag():
      return ANNOUNCE_TEXT_TEST_URL
   else:
      return ANNOUNCE_TEXT_URL

def getAnnounceBackupURL():
   if getTestAnnounceFlag():
      return ANNOUNCE_TEXT_TEST_URL
   else:
      return ANNOUNCE_TEXT_BACKUP_URL

def getArmoryDConfFile():
   return os.path.join(getArmoryHomeDir(), b'armoryd.conf')

def getDebugFlag():
   return ARMORY_OPTIONS.doDebug

def setDebugFlag(val):
   ARMORY_OPTIONS.doDebug = True

def getRebuildFlag():
   return ARMORY_OPTIONS.rebuild

def setRebuildFlag(val):
   ARMORY_OPTIONS.rebuild = val

def getRedownloadFlag():
   return ARMORY_OPTIONS.redownload

def setRedownloadFlag(val):
   ARMORY_OPTIONS.redownload = val

def getRescanFlag():
   return ARMORY_OPTIONS.rescan

def setRescanFlag(val):
   ARMORY_OPTIONS.rescan = val

def getClearMempoolFlag():
   return ARMORY_OPTIONS.clearMempool

def setClearMempoolFlag(val):
   ARMORY_OPTIONS.clearMempool = val

def getOfflineFlag():
   return ARMORY_OPTIONS.offline

def setOfflineFlag(val):
   ARMORY_OPTIONS.offline = val

def getNetLogFlag():
   return ARMORY_OPTIONS.netlog

def setNetLogFlag(val):
   ARMORY_OPTIONS.netlog = val

def getLogDisableFlag():
   return ARMORY_OPTIONS.logDisable

def setLogDisableFlag(val):
   ARMORY_OPTIONS.logDisable = val

def getTorFlag():
   return ARMORY_OPTIONS.useTorSettings

def getMultiThreadDebugFlag():
   return ARMORY_OPTIONS.mtdebug

def getSkipAnnounceFlag():
   return ARMORY_OPTIONS.skipAnnounceCheck

def setSkipAnnounceFlag(val):
   ARMORY_OPTIONS.skipAnnounceCheck = val

def getSkipStatsFlag():
   return ARMORY_OPTIONS.skipStatsReport

def setSkipStatsFlag(val):
   ARMORY_OPTIONS.skipStatsReport = val

def getForceOnlineFlag():
   return ARMORY_OPTIONS.forceOnline

def setForceOnlineFlag(val):
   ARMORY_OPTIONS.forceOnline = val

def getNetTimeout():
   return ARMORY_OPTIONS.nettimeout

def getModulesFlag():
   return not ARMORY_OPTIONS.disableModules

def getBitcoinForcePermissionsFlag():
   return not ARMORY_OPTIONS.disableConfPermis

def getIgnoreUnrecognizedFlag():
   return ARMORY_OPTIONS.ignoreUnrecognized

def getSupernodeFlag():
   return ARMORY_OPTIONS.enableSupernode

def setSupernodeFlag(val):
   ARMORY_OPTIONS.enableSupernode = True

def getWalletCheckFlag():
   return ARMORY_OPTIONS.forceWalletCheck

def getIgnoreZCFlag():
   return ARMORY_OPTIONS.ignoreAllZC

def getDeterministicSigFlag():
   return ARMORY_OPTIONS.enableDetSign

def setDeterministicSigFlag(val):
   ARMORY_OPTIONS.enableDetSign = val

def getDeterministicTxOrderingFlag():
   return ARMORY_OPTIONS.deterministicTxOrdering

def setDeterministicTxOrderingFlag(val):
   ARMORY_OPTIONS.deterministicTxOrdering = val

def getOptionsDict():
   return { k:v for k,v in vars(ARMORY_OPTIONS).iteritems() }

def getCommandLineArgs():
   return ARMORY_OPTIONS.commandLineArgs

def getArmoryBuild():
   return ARMORY_BUILD

def getRedownloadFile():
   return os.path.join(getArmoryHomeDir(), 'redownload.flag')

def getRebuildFile():
   return os.path.join(getArmoryHomeDir(), 'rebuild.flag')

def getRescanFile():
   return os.path.join(getArmoryHomeDir(), 'rescan.flag')

def getDelSettingsFile():
   return os.path.join(getArmoryHomeDir(), 'delsettings.flag')

def getClearMempoolFile():
   return os.path.join(getArmoryHomeDir(), 'clearmempool.flag')

def getExecutedScript():
   return ARMORY_OPTIONS.executedScript

def getArmoryHDSpace():
   return ARMORY_OPTIONS.HddAvailA

def setArmoryHDSpace(val):
   ARMORY_OPTIONS.HddAvailA = val

def getBitcoinHDSpace():
   return ARMORY_OPTIONS.HddAvailB

def setBitcoinHDSpace(val):
   ARMORY_OPTIONS.HddAvailB = val

def getNumCores():
   return ARMORY_OPTIONS.NumCores

def setNumCores(val):
   ARMORY_OPTIONS.NumCores = val

def getCPU():
   return ARMORY_OPTIONS.CpuStr

def setCPU(val):
   ARMORY_OPTIONS.CpuStr = val

def getMachine():
   return ARMORY_OPTIONS.Machine

def setMachine(val):
   ARMORY_OPTIONS.Machine = val

def getMemory():
   return ARMORY_OPTIONS.Memory

def setMemory(val):
   ARMORY_OPTIONS.Memory = val

def getX64Flag():
   return ARMORY_OPTIONS.IsX64

def setX64Flag(val):
   ARMORY_OPTIONS.IsX64 = val

class _empty(object): pass

# ARMORY_OPTIONS contains all dynamic options for armory.
# The idea is that this replaces constants and can be changed for testing.
ARMORY_OPTIONS = _empty()

# These are all the options available via command-line
_ARMORY_OPTIONS_DICT = {
   "--clearmempool": {
      'dest':"clearMempool", 'default':False, 'action':"store_true",
      'help':"Clear the Mempool of all transactions",
   },
   "--datadir": {
      'dest':"datadir", 'default':DEFAULT, 'type':"str",
      'help':"Change the directory that Armory calls home",
   },
   "--dbdir": {
      'dest':"armoryDBDir", 'default':DEFAULT, 'type':'str',
      'help':"Location to store blocks database (defaults to --datadir)",
   },
   "--debug": {
      'dest':"doDebug", 'default':False, 'action':"store_true",
      'help':"Increase amount of debugging output",
   },
   "--detsign": {
      'dest':"enableDetSign", 'default':False, 'action':"store_true",
      'help':"Enable Transaction Deterministic Signing (RFC 6979)",
   },
   "--dettxordering": {
      'dest':"deterministicTxOrdering", 'default':False, 'action':"store_true",
      'help':"Enable Deterministic TX Input and Output ordering (BIP0069)",
   },
   "--disable-conf-permis": {
      'dest':"disableConfPermis", 'default':False, 'action':"store_true",
      'help':"Disable forcing permissions on bitcoin.conf",
   },
   "--disable-modules": {
      'dest':"disableModules", 'default':False, 'action':"store_true",
      'help':"Disable looking for modules in the execution directory",
   },
   "--force-wallet-check": {
      'dest':"forceWalletCheck", 'default':False, 'action':"store_true",
      'help':"Force the wallet sanity check on startup",
   },
   "--ignoreunrecognized": {
      'dest':"ignoreUnrecognized", 'default':False, 'action':"store_true",
      'help':"Ignore Unrecognized Wallet Entries",
   },
   "--interport": {
      'dest':"interport", 'default':DEFAULT,        'type':"str",
      'help':"Port for inter-process communication between Armory instances",
   },
   "--logfile": {
      'dest':"logFile", 'default':DEFAULT, 'type':'str',
      'help':"Specify a non-default location to send logging information",
   },
   "--mtdebug": {
      'dest':"mtdebug", 'default':False, 'action':"store_true",
      'help':"Log multi-threaded call sequences",
   },
   "--multisigfile": {
      'dest':"multisigFile", 'default':DEFAULT, 'type':'str',
      'help':"File to store information about multi-signature transactions",
   },
   "--netlog": {
      'dest':"netlog", 'default':False, 'action':"store_true",
      'help':"Log networking messages sent and received by Armory",
   },
   "--nettimeout": {
      'dest':"nettimeout", 'default':2,         'type':"int",
      'help':"Timeout for detecting internet connection at startup",
   },
   "--nologging": {
      'dest':"logDisable", 'default':False, 'action':"store_true",
      'help':"Disable all logging",
   },
   "--nospendzeroconfchange": {
      'dest':"ignoreAllZC",'default':False, 'action':"store_true",
      'help':"All zero-conf funds will be unspendable, including sent-to-self coins",
   },
   "--offline": {
      'dest':"offline", 'default':False, 'action':"store_true",
      'help':"Force Armory to run in offline mode",
   },
   "--port": {
      'dest':"port", 'default':None, 'type':"int",
      'help':"Unit Test Argument - Do not consume",
   },
   "--rebuild": {
      'dest':"rebuild", 'default':False, 'action':"store_true",
      'help':"Rebuild blockchain database and rescan",
   },
   "--redownload": {
      'dest':"redownload", 'default':False, 'action':"store_true",
      'help':"Delete Bitcoin-Qt/bitcoind databases; redownload",
   },
   "--rescan": {
      'dest':"rescan", 'default':False, 'action':"store_true",
      'help':"Rescan existing blockchain DB",
   },
   "--rpcport": {
      'dest':"rpcport", 'default':DEFAULT, 'type':"str",
      'help':"RPC port for running armoryd.py",
   },
   "--satoshi-datadir": {
      'dest':"satoshiHome", 'default':DEFAULT, 'type':'str',
      'help':"The Bitcoin-Qt/bitcoind home directory",
   },
   "--satoshi-port": {
      'dest':"satoshiPort", 'default':DEFAULT, 'type':"str",
      'help':"For Bitcoin-Qt instances operating on a non-standard port",
   },
   "--satoshi-rpcport": {
      'dest':"satoshiRpcport",'default':DEFAULT,'type':"str",
      'help':"RPC port Bitcoin-Qt instances operating on a non-standard port",
   },
   "--settings": {
      'dest':"settingsPath", 'default':DEFAULT, 'type':"str",
      'help':"load Armory with a specific settings file",
   },
   "--skip-announce-check": {
      'dest':"skipAnnounceCheck", 'default':False, 'action':"store_true",
      'help':"Do not query for Armory announcements",
   },
   "--skip-online-check": {
         'dest':"forceOnline", 'default':False, 'action':"store_true",
      'help':"Go into online mode, even if internet connection isn't detected",
   },
   "--skip-stats-report": {
      'dest':"skipStatsReport", 'default':False, 'action':"store_true",
      'help':"Does announcement checking without any OS/version reporting (for ATI statistics)",
   },
   "--supernode": {
      'dest':"enableSupernode", 'default':False, 'action':"store_true",
      'help':"Enabled Exhaustive Blockchain Tracking",
   },
   "--test-announce": {
      'dest':"testAnnounceCode", 'default':False, 'action':"store_true",
      'help':"Only used for developers needing to test announcement code with non-offline keys",
   },
   "--testnet": {
      'dest':"testnet", 'default':False, 'action':"store_true",
      'help':"Use the testnet protocol",
   },
   "--tor": {
      'dest':"useTorSettings", 'default':False, 'action':"store_true",
      'help':"Enable common settings for when Armory connects through Tor",
   },
}


def initializeOptions():
   parser = optparse.OptionParser(usage="%prog [options]\n")

   for key in sorted(_ARMORY_OPTIONS_DICT.keys()):
      kwargs = _ARMORY_OPTIONS_DICT[key]
      parser.add_option(key, **kwargs)

   # Pre-10.9 OS X sometimes passes a process serial number as -psn_0_xxxxxx.
   # Nuke!
   if sys.platform == 'darwin':
      parser.add_option('-p', '--psn')

   if getattr(sys, 'frozen', False):
      sys.argv = [arg.decode('utf8') for arg in sys.argv]

   global ARMORY_OPTIONS
   ARMORY_OPTIONS, commandLineArgs = parser.parse_args()

   ARMORY_OPTIONS.commandLineArgs = commandLineArgs

   # This is probably an abuse of the ARMORY_OPTIONS structure, but not
   # automatically expanding "~" symbols is killing me
   for opt,val in ARMORY_OPTIONS.__dict__.iteritems():
      if not isinstance(val, basestring) or not val.startswith('~'):
         continue
         if os.path.exists(os.path.expanduser(val)):
            ARMORY_OPTIONS.__dict__[opt] = os.path.expanduser(val)
         else:
            # If the path doesn't exist, it still won't exist when we don't
            # modify it, and I'd like to modify as few vars as possible
            pass

   if len(sys.argv) > 0:
      scriptName = sys.argv[0]
      ARMORY_OPTIONS.executedScript = os.path.basename(scriptName)
   else:
      ARMORY_OPTIONS.executedScript = ''

   # add OS-specific data
   opsys = platform.system().lower()
   ARMORY_OPTIONS.isWindows = 'win32'  in opsys or 'windows' in opsys
   ARMORY_OPTIONS.isLinux   = 'nix'    in opsys or 'nux'     in opsys
   ARMORY_OPTIONS.isMac     = 'darwin' in opsys or 'osx'     in opsys

   if isWindows():
      ARMORY_OPTIONS.osVariant = platform.win32_ver()
   elif isLinux():
      ARMORY_OPTIONS.osVariant = platform.linux_distribution()
   elif isMac():
      ARMORY_OPTIONS.osVariant = platform.mac_ver()

   if isWindows():
      import ctypes
      buffer = ctypes.create_unicode_buffer(u'\0' * 260)
      rt = ctypes.windll.shell32.SHGetFolderPathW(
         0, 26, 0, 0, ctypes.byref(buffer))
      ARMORY_OPTIONS.userHomeDir = unicode(buffer.value)
   elif isLinux():
      ARMORY_OPTIONS.userHomeDir   = os.getenv('HOME')
   elif isMac():
      ARMORY_OPTIONS.userHomeDir   = os.path.expanduser(
         '~/Library/Application Support')
   else:
      raise RuntimeError("Could not identify OS")

   # set the testnet flag
   if getTestnetFlag():
      useTestnet()
   else:
      useMainnet()

   # Validate port numbers
   if ARMORY_OPTIONS.satoshiPort != DEFAULT:
      try:
         ARMORY_OPTIONS.satoshiPort = int(ARMORY_OPTIONS.satoshiPort)
      except:
         raise TypeError('Invalid port for Bitcoin-Qt, using %s'
                        % ARMORY_OPTIONS.satoshiPort)

   if ARMORY_OPTIONS.satoshiRpcport != DEFAULT:
      try:
         ARMORY_OPTIONS.satoshiRpcport = int(ARMORY_OPTIONS.satoshiRpcport)
      except:
         raise TypeError('Invalid rpc port for Bitcoin-Qt, using %s'
                         % ARMORY_OPTIONS.satoshiRpcport)

   if ARMORY_OPTIONS.rpcport != DEFAULT:
      try:
         ARMORY_OPTIONS.rpcport = int(ARMORY_OPTIONS.rpcport)
      except:
         raise TypeError('Invalid RPC port for armoryd %s'
                         % ARMORY_OPTIONS.rpcport)

   if ARMORY_OPTIONS.interport != DEFAULT:
      try:
         ARMORY_OPTIONS.interport = int(ARMORY_OPTIONS.interport)
      except:
         raise TypeError('Invalid interport for armory %s'
                         % ARMORY_OPTIONS.interport)

   # If this is the first Armory has been run, create directories
   if getArmoryHomeDir() and not os.path.exists(getArmoryHomeDir()):
      os.makedirs(getArmoryHomeDir())

   if not os.path.exists(getArmoryDatabaseDir()):
      os.makedirs(getArmoryDatabaseDir())

   # We disable wallet checks on ARM for the sake of resources
   if platform.machine().lower().startswith('arm'):
      ARMORY_OPTIONS.forceWalletCheck = False



