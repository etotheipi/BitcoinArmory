from armoryengine.ALL import *
from threading import Event
from jasvet import verifySignature, readSigBlock
import os
import sys
import time
import urllib


DEFAULT_FETCH_INTERVAL = 1*HOUR

if not CLI_OPTIONS.testAnnounceCode:
   # Signed with the Bitcoin offline announce key (see top of ArmoryUtils.py)
   ANNOUNCE_SIGN_PUBKEY = ARMORY_INFO_SIGN_PUBLICKEY
   HTTP_ANNOUNCE_FILE = 'https://bitcoinarmory.com/announce.txt'
else:
   # This is a lower-security announce file, fake data, just for testing
   ANNOUNCE_SIGN_PUBKEY = ('04'
      '601c891a2cbc14a7b2bb1ecc9b6e42e166639ea4c2790703f8e2ed126fce432c'
      '62fe30376497ad3efcd2964aa0be366010c11b8d7fc8209f586eac00bb763015')
   HTTP_ANNOUNCE_FILE = 'https://s3.amazonaws.com/bitcoinarmory-testing/testannounce.txt'


class AnnounceDataFetcher(object):
   """
   Armory Technologies, Inc, will post occasional SIGNED updates to be
   processed by running instances of Armory that haven't disabled it.

   The files in the fetchDir will be small.  At the time of this writing,
   the only files we will fetch and store:

      announce.txt :  announcements & alerts to be displayed to the user
      versions.txt :  changelog of versions, triggers update nofications
      dllinks.txt  :  URLs and hashes of installers for all OS and versions
      bootstrap.dat.torrent  :  torrent file for quick blockchain download 
   """

   #############################################################################
   def __init__(self, announceURL=HTTP_ANNOUNCE_FILE, fetchDir=None):
      self.currDownloading = Event()
      self.forceFetchFlag = Event()
      self.forceIsFinished = Event()
      self.firstSuccess = Event()
      self.shutdownFlag = Event()
      self.announceURL = announceURL
      self.lastFetch = 0
      self.lastChange = 0
      self.loopThread = None
      self.disabled = False
      self.setFetchInterval(DEFAULT_FETCH_INTERVAL)

      # Just disable ourselves if we have continuous exceptions
      self.numConsecutiveExceptions = 0

      # If we are on testnet, we may require matching a mainnnet addr
      self.validAddrStrings = []
      a160 = hash160(hex_to_binary(ANNOUNCE_SIGN_PUBKEY))
      self.validAddrStrings = [hash160_to_addrStr(a160), \
                               hash160_to_addrStr(a160, '\x00')]

      
      
      # Make sure the fetch directory exists (where we put downloaded files)
      self.fetchDir = fetchDir if fetchDir else os.path.join(ARMORY_HOME_DIR, 'fetched')
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
   def setFetchInterval(self, newInterval):
      self.fetchInterval = newInterval

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
   def getFetchedFile(self, fileID, forceFetch=False):
      if not self.isRunning():
         LOGERROR('Cannot fetch file, fetcher is not running!')
         return None

      if forceFetch:
         LOGINFO('Forcing fetch before returning file')
         self.forceIsFinished.clear()
         self.forceFetchFlag.set()
         self.forceIsFinished.wait()
         self.forceFetchFlag.clear()

      fname = os.path.join(self.fetchDir, fileID+'.file')
      with open(fname, 'rb') as f:
         returnData = f.read()
      
      return returnData


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
   
         argsMap['id'] = binary_to_hex(hash256(USER_HOME_DIR)[:4])

      return url + '?' + urllib.urlencode(argsMap)



   #############################################################################
   def __fetchAnnounceDigests(self, doDecorate=False):

      self.lastFetch = RightNow()
      digestURL = self.getDecoratedURL(self.announceURL, verbose=doDecorate)
      return self.__fetchFile(digestURL)
      

      
   #############################################################################
   def __fetchFile(self, url):
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
         return ''
      except:
         LOGEXCEPT('Unspecified error downloading URL')
         return ''
      


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
            self.forceFetchFlag.set()
      It will skip the time check and force a download right now.
      Using getFetchedFile(forceFetch=True) will do this for you,
      and will wait until the operation completes before returning 
      the result.
      """

      while True:
         
         try:
            if self.isDisabled() or self.shutdownFlag.isSet():
               self.shutdownFlag.clear()
               break

            ##### Only check once per hour unless force flag is set
            if not self.forceFetchFlag.isSet():
               if RightNow()-self.lastFetch < self.fetchInterval:
                  continue
            else:
               LOGINFO('Forcing announce data fetch')
               self.forceIsFinished.clear()

            ##### Always decorate the URL with OS, Armory version on the first run
            self.currDownloading.set()
            digestData = self.__fetchAnnounceDigests(not self.firstSuccess.isSet())

            if len(digestData)==0:
               LOGWARN('Error fetching announce digest')
               continue

            self.firstSuccess.set()

            ##### Digests come in signature blocks.  Verify sig using jasvet.
            try:
               sig, msg = readSigBlock(digestData)
               signAddress = verifySignature(sig, msg, 'v1', ord(ADDRBYTE))
               if not signAddress in self.validAddrStrings:
                  LOGERROR('Announce info carried invalid signature!')
                  LOGERROR('Signature addr: %s' % signAddress)
                  LOGERROR('Expected  addresses:')
                  for a in self.validAddrStrings:
                     LOGERROR('   ' + a)
                  continue 
            except:
               LOGEXCEPT('Could not verify data in signed message block')
               continue


            ##### We have a valid digest, now parse it
            justDownloadedMap = {}
            for row in [line.split() for line in msg.strip().split('\n')]:
               if len(row)==3:
                  justDownloadedMap[row[0]] = [row[1], row[2]]
               else:
                  LOGERROR('Malformed announce matrix: %s' % str(row))
                  continue
            
      
            ##### Check whether any of the hashes have changed
            for key,val in justDownloadedMap.iteritems():
               jdURL,jdHash = val[0],val[1]
               
               if not (key in self.fileHashMap and self.fileHashMap[key]==jdHash):
                  LOGINFO('Changed [ "%s" ] == [%s, %s]', key, jdURL, jdHash)
                  newData = self.__fetchFile(jdURL)
                  if len(newData) == 0:
                     LOGERROR('Failed downloading announce file : %s', key)
                     continue
                  newHash = binary_to_hex(sha256(newData))
                  if not newHash == jdHash:
                     LOGERROR('Downloaded file hash does not match!')
                     LOGERROR('Hash of downloaded data: %s', newHash)
                     continue

                  filename = os.path.join(self.fetchDir, key+'.file')
                  with open(filename, 'wb') as f:
                     f.write(newData)
                  self.lastChange = RightNow()
                  self.fileHashMap[key] = jdHash
    
            ##### Clean up as needed
            if self.forceFetchFlag.isSet():
               self.forceIsFinished.set()
            self.numConsecutiveExceptions = 0
            self.currDownloading.clear()

         except:
            self.numConsecutiveExceptions += 1
            LOGEXCEPT('Failed download')
            if self.numConsecutiveExceptions > 20:
               self.setDisabled(True)
         finally:
            time.sleep(0.5)
            
      
