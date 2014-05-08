from armoryengine.ALL import *
from threading import Event
from jasvet import verifySignature, readSigBlock
import os
import sys
import time
import urllib


DEFAULT_FETCH_INTERVAL = 30*MINUTE
DEFAULT_MIN_PRIORITY = 2048

if not CLI_OPTIONS.testAnnounceCode:
   # Signed with the Bitcoin offline announce key (see top of ArmoryUtils.py)
   ANNOUNCE_SIGN_PUBKEY = ARMORY_INFO_SIGN_PUBLICKEY
   ANNOUNCE_URL = 'https://bitcoinarmory.com/announce.txt'
   ANNOUNCE_URL_BACKUP = 'https://s3.amazonaws.com/bitcoinarmory-media/announce.txt'
else:
   # This is a lower-security announce file, fake data, just for testing
   ANNOUNCE_SIGN_PUBKEY = ('04'
      '601c891a2cbc14a7b2bb1ecc9b6e42e166639ea4c2790703f8e2ed126fce432c'
      '62fe30376497ad3efcd2964aa0be366010c11b8d7fc8209f586eac00bb763015')
   ANNOUNCE_URL = 'https://s3.amazonaws.com/bitcoinarmory-testing/testannounce.txt'
   ANNOUNCE_URL_BACKUP = ANNOUNCE_URL


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
      bootstrap.dat.torrent  :  torrent file for quick blockchain download 
   """

   #############################################################################
   def __init__(self, announceURL=ANNOUNCE_URL, \
                      backupURL=ANNOUNCE_URL_BACKUP, \
                      fetchDir=None):

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
      self.announceURL = announceURL
      self.announceURL_backup = backupURL

      # Just disable ourselves if we have continuous exceptions
      self.numConsecutiveExceptions = 0

      # If we are on testnet, we may require matching a mainnnet addr
      a160 = hash160(hex_to_binary(ANNOUNCE_SIGN_PUBKEY))
      self.validAddrStr = hash160_to_addrStr(a160)

      
      
      # Make sure the fetch directory exists (where we put downloaded files)
      self.fetchDir = fetchDir 
      if fetchDir is None:
         self.fetchDir = os.path.join(ARMORY_HOME_DIR, 'announcefiles')
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
   def setDisabled(self, b=True):
      self.disabled = b

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
      argsMap = {}
      argsMap['ver'] = getVersionString(BTCARMORY_VERSION)
   
      if verbose:
         if OS_WINDOWS:
            argsMap['os'] = 'win'
         elif OS_LINUX:
            argsMap['os'] = 'lin'
         elif OS_MACOSX:
            argsMap['os'] = 'mac'
         else:
            argsMap['os'] = 'unk'
   
         try:
            if OS_MACOSX:
               argsMap['osvar'] = OS_VARIANT
            else:
               argsMap['osvar'] = OS_VARIANT[0].lower()
         except:
            LOGERR('Unrecognized OS while constructing version URL')
            argsMap['osvar'] = 'unk'
   
         if OS_WINDOWS:
            argsMap['id'] = binary_to_hex(hash256(USER_HOME_DIR.encode('utf8'))[:4])
         else:
            argsMap['id'] = binary_to_hex(hash256(USER_HOME_DIR)[:4])

      return url + '?' + urllib.urlencode(argsMap)



   #############################################################################
   def __fetchAnnounceDigests(self, doDecorate=False):
      self.lastFetch = RightNow()
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
         socket.setdefaulttimeout(CLI_OPTIONS.nettimeout)
         urlobj = urllib2.urlopen(url, timeout=CLI_OPTIONS.nettimeout)
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

      ##### Digests come in signature blocks.  Verify sig using jasvet.
      try:
         sig, msg = readSigBlock(digestData)
         signAddress = verifySignature(sig, msg, 'v1', ord(ADDRBYTE))
         if not signAddress == self.validAddrStr:
            LOGERROR('Announce info carried invalid signature!')
            LOGERROR('Signature addr: %s' % signAddress)
            LOGERROR('Expected  address: %s', self.validAddrStr)
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
            if not newHash == jdHash:
               LOGERROR('Downloaded file hash does not match!')
               LOGERROR('Hash of downloaded data: %s', newHash)
               return

            filename = os.path.join(self.fetchDir, key+'.file')
            with open(filename, 'wb') as f:
               f.write(newData)
            self.lastChange = RightNow()
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
               if RightNow()-self.lastFetch < self.fetchInterval:
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
            
      




