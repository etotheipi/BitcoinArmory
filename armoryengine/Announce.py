################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import os
import time
import urllib

from copy import deepcopy
from threading import Event

from ArmoryUtils import *

from BackgroundThread import AllowAsync

class AnnounceDataFetcher(object):
   """
   Armory Technologies, Inc, will post occasional SIGNED updates to be
   processed by running instances of Armory that haven't disabled it.

   The files in the fetchDir will be small.  At the time of this writing,
   the only files we will fetch and store:

      announce.txt  :  announcements & alerts to be displayed to the user
      changelog.txt :  changelog of versions, triggers update nofications
      dllinks.txt   :  URLs and hashes of installers for all OS and versions
      notify.txt    :  Notifications & alerts
   """

   #############################################################################
   def __init__(self, announceURL=None, \
                      backupURL=None, \
                      fetchDir=None,
                      uniqueID='00000000'):

      self.loopIsIdle = Event()
      self.forceCheckFlag = Event()
      self.forceIsFinished = Event()
      self.firstSuccess = Event()
      self.shutdownFlag = Event()
      self.lastFetch = 0
      self.lastChange = 0
      self.loopThread = None
      self.disabled = False
      self.setFetchInterval(DEFAULT_FETCH_INTERVAL)
      self.loopIsIdle.set()
      self.lastAnnounceChange = 0

      # Where to fetch the data from
      self.announceURL = announceURL or getAnnounceURL()
      self.announceURL_backup = backupURL or getAnnounceBackupURL()

      # For OS/version statistics, we use the ID is used to remove duplicates
      self.uniqueID = uniqueID
      self.disableDecorate = False

      # Just disable ourselves if we have continuous exceptions
      self.numConsecutiveExceptions = 0

      # If we are on testnet, we may require matching a mainnnet addr
      a160 = hash160(hex_to_binary(getAnnounceSignPubKey()))
      self.validAddrStr = hash160_to_addrStr(a160)

      
      
      # Make sure the fetch directory exists (where we put downloaded files)
      self.fetchDir = fetchDir 
      if fetchDir is None:
         self.fetchDir = os.path.join(getArmoryHomeDir(), 'announcefiles')
      if not os.path.exists(self.fetchDir):
         os.mkdir(self.fetchDir)


      # Read and hash existing files in that directory
      self.fileHashMap = {}
      LOGINFO('Reading files in fetcher directory:')
      for fname in os.listdir(self.fetchDir):
         fpath = os.path.join(self.fetchDir, fname)
         if not fname.endswith('.file') or os.path.getsize(fpath) > 16*MEGABYTE:
            continue

         fid = fname[:-5]
         with open(fpath, 'rb') as f:
            self.fileHashMap[fid] = binary_to_hex(sha256(f.read()))
            LOGINFO('   %s : %s', fid.ljust(16), self.fileHashMap[fid])
         

   #############################################################################
   def start(self):
      if not self.disabled:
         self.loopThread = self.__runFetchLoop(async=True)

   #############################################################################
   def isDisabled(self):
      return self.disabled

   #############################################################################
   def shutdown(self):
      LOGINFO('Called AnnounceDataFetcher.shutdown()')
      self.shutdownFlag.set()

   #############################################################################
   def setFetchInterval(self, newInterval):
      self.fetchInterval = max(newInterval,10)

   #############################################################################
   def setFullyDisabled(self, b=True):
      self.disabled = b

   #############################################################################
   def setStatsDisable(self, b=True):
      self.disableDecorate = b

   #############################################################################
   def isRunning(self):
      return self.loopThread.isRunning() if self.loopThread else False

   #############################################################################
   def atLeastOneSuccess(self):
      return self.firstSuccess.isSet()

   #############################################################################
   def numFiles(self):
      return len(self.fileHashMap)
      
   #############################################################################
   def fetchRightNow(self, doWait=0):
      self.forceIsFinished.clear()
      self.forceCheckFlag.set()
   
      if doWait > 0:
         self.forceIsFinished.wait(doWait)
         self.forceCheckFlag.clear()
      
   #############################################################################
   def getAnnounceFilePath(self, fileID):
      fpath = os.path.join(self.fetchDir, fileID+'.file')
      return fpath if os.path.exists(fpath) else None

   #############################################################################
   def getAnnounceFile(self, fileID, forceCheck=False, forceWait=10):
      if forceCheck:
         LOGINFO('Forcing fetch before returning file')
         if not self.isRunning():
            # This is safe because there's no one to collide with
            self.__runFetchSequence()
         else:
            self.forceIsFinished.clear()
            self.forceCheckFlag.set()
   
            if not self.forceIsFinished.wait(forceWait):
               self.forceCheckFlag.clear()
               return None

            self.forceCheckFlag.clear()
      else:
         # Wait up to one second for any current ops to finish
         if not self.loopIsIdle.wait(1):
            LOGERROR('Loop was busy for more than one second')
            return None

      # If the above succeeded, it will be in the fetchedFiles dir
      # We may have 
      fpath = self.getAnnounceFilePath(fileID)

      if not (fpath and os.path.exists(fpath)):
         LOGERROR('No file with ID=%s was fetched', fileID)
         return None

      with open(fpath, 'rb') as f:
         returnData = f.read()
      
      return returnData


   #############################################################################
   def getFileModTime(self, fileID):
      fpath = self.getAnnounceFilePath(fileID)
      if not fpath or not os.path.exists(fpath):
         #LOGERROR('No file with ID=%s was fetched', fileID)
         return 0
   
      return os.path.getmtime(fpath)
         
            

   #############################################################################
   def getLastSuccessfulFetchTime(self):
      announcePath = os.path.join(self.fetchDir, 'announce.file')
      if os.path.exists(announcePath):
         return os.path.getmtime(announcePath)
      else:
         return 0

         
      

   #############################################################################
   def getDecoratedURL(self, url, verbose=False):
      """
      This always decorates the URL with at least Armory version.  Use the 
      verbose=True option to add OS, subOS, and a few "random" bytes that help
      reject duplicate queries.
      """

      # ACR UPDATE 08/2014: non-verbose now does no decorating at all.  It just
      #                     returns the same URL that was passed in.
      if (not verbose) or self.disableDecorate:
         return url
      
      argsMap = {}
      argsMap['ver'] = getVersionString(BTCARMORY_VERSION)
   
      if verbose:
         if isWindows():
            argsMap['os'] = 'win'
         elif isLinux():
            argsMap['os'] = 'lin'
         elif isMac():
            argsMap['os'] = 'mac'
         else:
            argsMap['os'] = 'unk'
   
         try:
            if isMac():
               argsMap['osvar'] = getOSVariant()
            else:
               argsMap['osvar'] = getOSVariant()[0].lower()
         except:
            LOGERR('Unrecognized OS while constructing version URL')
            argsMap['osvar'] = 'unk'
   
         argsMap['id'] = self.uniqueID

      return url + '?' + urllib.urlencode(argsMap)



   #############################################################################
   def __fetchAnnounceDigests(self, doDecorate=False):
      self.lastFetch = time.time()
      digestURL = self.getDecoratedURL(self.announceURL, verbose=doDecorate)
      backupURL = None
      if self.announceURL_backup:
         backupURL = self.getDecoratedURL(self.announceURL_backup)
      return self.__fetchFile(digestURL, backupURL)
      

      
   #############################################################################
   def __fetchFile(self, url, backupURL=None):
      LOGINFO('Fetching: %s', url)
      try:
         import urllib2
         import socket
         LOGDEBUG('Downloading URL: %s' % url)
         socket.setdefaulttimeout(getNetTimeout())
         urlobj = urllib2.urlopen(url, timeout=getNetTimeout())
         return urlobj.read()
      except ImportError:
         LOGERROR('No module urllib2 -- cannot download anything')
         return ''
      except (urllib2.URLError, urllib2.HTTPError):
         LOGERROR('Specified URL was inaccessible')
         LOGERROR('Tried: %s', url)
         return self.__fetchFile(backupURL) if backupURL else ''
      except:
         LOGEXCEPT('Unspecified error downloading URL')
         return self.__fetchFile(backupURL) if backupURL else ''
      

   #############################################################################
   def __runFetchSequence(self):
      ##### Always decorate the URL with OS, Armory version on the first run
      digestData = self.__fetchAnnounceDigests(not self.firstSuccess.isSet())
   
      if len(digestData)==0:
         LOGWARN('Error fetching announce digest')
         return

      self.firstSuccess.set()

      ##### Digests come in signature blocks.
      try:
         data = verifySignedMessage(digestData)
         signAddress, msg = data['address'], data['message']
         if signAddress != self.validAddrStr:
            LOGERROR('Announce info carried invalid signature!')
            LOGERROR('Signature addr: %s' % signAddress)
            LOGERROR('Expected address: %s', self.validAddrStr)
            return 
      except:
         LOGEXCEPT('Could not verify data in signed message block')
         return

      # Always rewrite file; it's small and will use mtime for info
      with open(os.path.join(self.fetchDir, 'announce.file'), 'w') as f:
         f.write(digestData)


      ##### We have a valid digest, now parse it
      justDownloadedMap = {}
      for row in [line.split() for line in msg.strip().split('\n')]:
         if len(row)==3:
            justDownloadedMap[row[0]] = [row[1], row[2]]
         else:
            LOGERROR('Malformed announce matrix: %s' % str(row))
            return
      
      ##### Check whether any of the hashes have changed
      for key,val in justDownloadedMap.iteritems():
         jdURL,jdHash = val[0],val[1]
         
         if not (key in self.fileHashMap and self.fileHashMap[key]==jdHash):
            LOGINFO('Changed [ "%s" ] == [%s, %s]', key, jdURL, jdHash)
            newData = self.__fetchFile(jdURL)
            if len(newData) == 0:
               LOGERROR('Failed downloading announce file : %s', key)
               return
            newHash = binary_to_hex(sha256(newData))
            if newHash != jdHash:
               LOGERROR('Downloaded file hash does not match!')
               LOGERROR('URL: %s', jdURL)
               LOGERROR('Hash of downloaded data: %s', newHash)
               LOGERROR('Hash claimed: %s', jdHash)
               continue

            filename = os.path.join(self.fetchDir, key+'.file')
            with open(filename, 'wb') as f:
               f.write(newData)
            self.lastChange = time.time()
            self.fileHashMap[key] = jdHash

      ##### Clean up as needed
      if self.forceCheckFlag.isSet():
         self.forceIsFinished.set()
         self.forceCheckFlag.clear()
      self.numConsecutiveExceptions = 0


   #############################################################################
   # I'm taking a shortcut around adding all the threading code here
   # Simply use @AllowAsync and only call with async=True.  Done.
   @AllowAsync
   def __runFetchLoop(self):
      """
      All this code runs in a separate thread (your app will freeze if 
      you don't call this with the async=True argument).  It will 
      periodically check for new announce data, and update members that
      are visible to other threads.

      By default, it will check once per hour.  If you call
            self.forceCheckFlag.set()
      It will skip the time check and force a download right now.
      Using getAnnounceFile(forceCheck=True) will do this for you,
      and will wait until the operation completes before returning 
      the result.
      """

      while True:
         
         try:
            if self.isDisabled() or self.shutdownFlag.isSet():
               self.shutdownFlag.clear()
               break

            ##### Only check once per hour unless force flag is set
            if not self.forceCheckFlag.isSet():
               if time.time()-self.lastFetch < self.fetchInterval:
                  continue
            else:
               LOGINFO('Forcing announce data fetch')
               self.forceIsFinished.clear()

            self.loopIsIdle.clear()
            self.__runFetchSequence()

         except:
            self.numConsecutiveExceptions += 1
            LOGEXCEPT('Failed download')
            if self.numConsecutiveExceptions > 20:
               self.setDisabled(True)
         finally:
            self.loopIsIdle.set()
            time.sleep(0.5)
            
################################################################################
# NOTE:  These methods DO NOT verify signatures.  It is assumed that the
#        signature verification already happened, and these methods were only
#        called if the signatures were good.  They can be called on blocks
#        of text WITH OR WITHOUT the signature block data (either pass it
#        the signed block, or just whats inside the block).

################################################################################
################################################################################
class changelogParser(object):
   """
   Returns a list of list of lists representing all version & changelg to the
   stop version (or all versions, if 0)


   changeLog ==
      [
         [ '0.88.1', 'December 27, 2013',
            [
               [ 'Auto-run Bitcoind', 'This version will now run ...'],
               [ 'Mac/OSX Version',   'Binaries now available on ...'],
               [ 'Signed installers', 'All binaries are now sign ...']
            ]
         ]
         [ '0.87', 'April 18, 2013',
            [
               [ 'QR Codes',          'QR codes added everywhere ...'],
               [ 'Export History',    'Export tx history to CSV  ...']
            ]
         ]
         ...
      ]

   """


   #############################################################################
   def __init__(self, filename='', filetext=''):
      self.changelog = []
      if not filename and not filetext:
         return

      if filename and os.path.exists(filename):
         f = open(filename, 'r')
         filetext = f.read()
         f.close()
      self.parseChangelogText(filetext)


   #############################################################################
   def parseChangelogText(self, fileText):

      self.changelog = []

      if fileText is None:
         return None

      try:
         if SIGNED_BLOCK_HEAD in fileText:
            fileText = readSigBlock(fileText)[1]
         versionLines = [line.strip() for line in fileText.split('\n')][::-1]

         # All lines have been stripped already
         while len(versionLines) > 0:
            line = versionLines.pop()
            if line.startswith('#') or len(line)==0:
               continue
            if line.startswith('VERSION') and len(line.split())==2:
               self.changelog.append([line.split(' ')[-1], '', []])
            elif line.upper().startswith('RELEASED'):
               self.changelog[-1][1] = line[8:].strip()
            elif line.startswith('-'):
               featureTitle = line[2:]
               self.changelog[-1][2].append([featureTitle, ''])
            else:
               curr = self.changelog[-1][2][-1][-1]
               self.changelog[-1][2][-1][-1] += ('' if len(curr)==0 else ' ') + line
         return self.getChangelog()
      except:
         LOGEXCEPT('Failed to parse changelog')
         return None


   #############################################################################
   def getChangelog(self, stopAtVersion=0, dontStartBefore=UINT32_MAX):
      output = []
      for ver in self.changelog:
         verInt = getVersionInt(readVersionString(ver[0]))
         if verInt > dontStartBefore:
            continue
         if verInt <= stopAtVersion:
            break
         output.append(ver[:])
      return output


################################################################################
################################################################################
class downloadLinkParser(object):
   """
   Parse files with the following format:

   -----BEGIN BITCOIN SIGNED MESSAGE-----
   # Armory for Windows
   Armory 0.91 Windows XP        32     http://url/armory_0.91_xp32.exe  3afb9881c32
   Armory 0.91 Windows XP        64     http://url/armory_0.91_xp64.exe  8993ab127cf
   Armory 0.91 Windows Vista,7,8 32,64  http://url/armory_0.91.exe       7f3b9964aa3

   # Offline Bundles
   ArmoryOffline 0.88 Ubuntu 10.04  32  http://url/offbundle-32.tar.gz   641382c93b9
   ArmoryOffline 0.88 Ubuntu 12.10  32  http://url/offbundle-64.tar.gz   5541af39c84

   # Windows 32-bit Satoshi (Bitcoin-Qt/bitcoind)
   Satoshi 0.9.0 Windows XP,Vista,7,8 32,64 http://btc.org/win0.9.0.exe  118372a9ff3
   Satoshi 0.9.0 Ubuntu  10.04              http://btc.org/win0.9.0.deb  2aa3f763c3b

   -----BEGIN BITCOIN SIGNATURE-----
   ac389861cff8a989ae57ae67af43cb3716ca189aa178cff893179531
   -----END BITCOIN SIGNATURE-----


   This will return a heavily-nested dictionary that will be easy to look up
   after we have reduced the current OS to the right set of keys (we will
   create a function that takes the output of
      platform.system(),
      platform.mac_ver(),
      platform.linux_distribution(), and
      platform.win32_ver()
   and returns a sequence of keys we can use to look up the correct version

   self.downloadMap['Armory']['0.91']['Windows']['Vista']['64'] -->
                           ['http://url/armory_0.91.exe', '7f3b9964aa3']

   Actually use "getDownloadLink

   """

   #############################################################################
   def __init__(self, filename='', filetext=''):
      self.downloadMap = {}
      if not filename and not filetext:
         return

      if filename and os.path.exists(filename):
         f = open(filename, 'r')
         self.parseDownloadList(f.read())
         f.close()
      elif filetext:
         self.parseDownloadList(filetext)



   #############################################################################
   def parseDownloadList(self, fileText):
      self.downloadMap = {}

      if fileText is None:
         return {}

      def insertLink(mapObj, urlAndHash, keyList):
         if len(keyList)>1:
            if not keyList[0] in mapObj:
               mapObj[keyList[0]] = {}
            insertLink(mapObj[keyList[0]], urlAndHash, keyList[1:])
         else:
            mapObj[keyList[0]] = urlAndHash

      try:
         if SIGNED_BLOCK_HEAD in fileText:
            fileText = readSigBlock(fileText)[1]

         dlLines = [line.strip() for line in fileText.split('\n')][::-1]
         while len(dlLines) > 0:
            line = dlLines.pop()
            if line.startswith('#') or len(line)==0:
               continue
            lineLists  = [pc.split(',') for pc in line.split()[:-2]]

            urlAndHash = line.split()[-2:]
            APPLIST, VERLIST, OSLIST, SUBOSLIST, BITLIST = range(5)
            for app in lineLists[APPLIST]:
               for ver in lineLists[VERLIST]:
                  for opsys in lineLists[OSLIST]:
                     for subOS in lineLists[SUBOSLIST]:
                        for nbit in lineLists[BITLIST]:
                           insertLink(self.downloadMap,
                                      urlAndHash,
                                      [app, ver, opsys, subOS, nbit])


         return self.getNestedDownloadMap()
      except:
         LOGEXCEPT('Failed to parse downloads')
         return None


   #############################################################################
   def printDownloadMap(self):

      def recursePrintStr(theObj, indent=0):
         if not isinstance(theObj, dict):
            return ' '*indent + str(theObj) + "\n"
         else:
            for key,val in theObj.iteritems():
               return ' '*indent + key + ':\n' + \
                  recursePrintStr(theObj[key], indent+5)

      toPrint = recursePrintStr(self.downloadMap)
      print toPrint
      return toPrint

   #############################################################################
   def getDownloadLink(self, *keyList):

      def recurseGet(theMap, keyList):
         if not isinstance(theMap, dict):
            return None

         if len(keyList)>1:
            if not keyList[0] in theMap:
               return None
            return recurseGet(theMap[keyList[0]], keyList[1:])
         else:
            return theMap[keyList[0]]

      if len(keyList)==0:
         return None

      return recurseGet(self.downloadMap, keyList)


   #############################################################################
   def getNestedDownloadMap(self):
      return deepcopy(self.downloadMap)



################################################################################
################################################################################
class notificationParser(object):
   """
   # PRIORITY VALUES:
   #    Test announce:          1024
   #    General Announcment:    2048
   #    Important non-critical: 3072
   #    Critical/security sens: 4096
   #
   # Unique ID must be first, and signals that this is a new notification

   UNIQUEID:   873fbc11
   VERSION:    0
   STARTTIME:  0
   EXPIRES:    1500111222
   CANCELID:   []
   MINVERSION: 0.87.2
   MAXVERSION: 0.88.1
   PRIORITY:   4096
   NOTIFYSEND: False
   NOTIFYRECV: True
   SHORTDESCR: Until further notice, require 30 confirmations for incoming transactions.
   LONGDESCR:
      THIS IS A FAKE ALERT FOR TESTING PURPOSES:

      There is some turbulence on the network that may result in some transactions
      being accidentally reversed up to 30 confirmations.  A clever attacker may
      be able to exploit this to scam you.  For incoming transactions from
      parties with no existing trust, please wait at least 30 confirmations before
      considering the coins to be yours.
      *****
   """

   #############################################################################
   def __init__(self, filename='', filetext=''):
      self.notifications = {}
      if not filename and not filetext:
         return

      if filename and os.path.exists(filename):
         f = open(filename, 'r')
         filetext = f.read()
         f.close()

      self.parseNotificationText(filetext)


   #############################################################################
   def parseNotificationText(self, fileText):
      self.notifications = {}

      if fileText is None:
         return None

      try:
         if SIGNED_BLOCK_HEAD in fileText:
            fileText = readSigBlock(fileText)[1]
         notifyLines = [line.strip() for line in fileText.split('\n')][::-1]
         currID = ''
         readLongDescr = False
         longDescrAccum = ''

         while len(notifyLines) > 0:
            line = notifyLines.pop()
            if not readLongDescr and (line.startswith('#') or len(line)==0):
               continue
            if line.upper().startswith('UNIQUEID'):
               currID = line.split(':')[-1].strip()
               self.notifications[currID] = {}
            elif line.upper().startswith('LONGDESCR'):
               readLongDescr = True
            elif line.startswith("*****"):
               readLongDescr = False
               self.notifications[currID]['LONGDESCR'] = longDescrAccum
               longDescrAccum = ''
            elif readLongDescr:
               if len(line.strip())==0:
                  longDescrAccum += '<br><br>'
               else:
                  longDescrAccum += line.strip() + ' '
            else:
               key = line.split(':')[ 0].strip().upper()
               val = line.split(':')[-1].strip()
               self.notifications[currID][key] = val

         return self.getNotificationMap()
      except:
         LOGEXCEPT('Failed to parse notifications')
         return None


   #############################################################################
   def getNotificationMap(self):
      return deepcopy(self.notifications)
