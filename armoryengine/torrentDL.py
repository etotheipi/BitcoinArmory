import sys
import os

sys.path.append('..')

from ArmoryUtils import ARMORY_HOME_DIR, BTC_HOME_DIR, LOGEXCEPT, \
                        LOGERROR, LOGWARN, LOGINFO, MEGABYTE, \
                        AllowAsync, RightNow, unixTimeToFormatStr, \
                        secondsToHumanTime, MAGIC_BYTES,\
                        bytesToHumanSize, secondsToHumanTime
from BitTornado.download_bt1 import BT1Download, defaults, get_response
from BitTornado.RawServer import RawServer, UPnP_ERROR
from random import seed
from socket import error as socketerror
from BitTornado.bencode import bencode
from BitTornado.natpunch import UPnP_test
from threading import Event
from os.path import abspath
from sys import argv, stdout
import sys
import shutil
from sha import sha
from time import strftime, sleep
import types
from BitTornado.clock import clock
from BitTornado import createPeerID, version
from BitTornado.ConfigDir import ConfigDir
from BitTornado.download_bt1 import defaults, download
from BitTornado.ConfigDir import ConfigDir


# Totally should've used a decorator for the custom funcs... 
   

class TorrentDownloadManager(object):
   
   #############################################################################
   def __init__(self, torrentFile=None, savePath=None, doDisable=False):
      self.torrent = torrentFile
      self.torrentDNE = False
      self.cacheDir = os.path.join(ARMORY_HOME_DIR, 'bittorrentcache')
      self.doneObj = Event()
      self.customCallbacks = {}
      self.minSecondsBetweenUpdates = 1
      self.lastUpdate = 0
      self.disabled = doDisable
      self.satoshiDir = BTC_HOME_DIR

      # These need to exist even if setup hasn't been called
      self.lastStats     = {}
      self.startTime     = None
      self.finishTime    = None
      self.dlFailed      = False
      self.bt1dow        = None
      self.response      = None
      self.torrentSize   = None
      self.torrentName   = None
      self.savePath      = None
      self.savePath_temp = None
      
      self.nHashFailures = 0
      self.killAfterNHashFails = 100
      

   #############################################################################
   def setupTorrent(self, torrentFile, savePath=None):

      # Some things to reset on every setup operation
      self.lastStats  = {}
      self.startTime  = None
      self.finishTime = None
      self.dlFailed   = False
      self.bt1dow     = None
      self.response    = None
      self.torrentSize = None
      self.torrentName = None
      self.savePath    = None
      self.savePath_temp = None

      # Set torrent file, bail if it doesn't exist
      self.torrent = torrentFile
      self.torrentDNE = False

      if not self.torrent or not os.path.exists(self.torrent):
         LOGERROR('Attempted to setup TDM with non-existent torrent:')
         if self.torrent:
            LOGERROR('Torrent path:  %s', self.torrent)
         self.torrentDNE = True
         return

      self.lastUpdate = RightNow()

      # Get some info about the torrent
      if not self.torrentDNE:
         self.response = get_response(self.torrent, '', self.errorFunc)
         self.torrentSize = self.response['info']['length']
         self.torrentName = self.response['info']['name']
         LOGINFO('Torrent name is: %s' %  self.torrentName)
         LOGINFO('Torrent size is: %0.2f MB' %  (self.torrentSize/float(MEGABYTE)))


         self.savePath = savePath
         if self.savePath is None:
            self.savePath = os.path.join(BTC_HOME_DIR, self.torrentName)
         self.savePath_temp = self.savePath + '.partial'

   #############################################################################
   def setSatoshiDir(self, btcDir):
      self.satoshiDir = btcDir

   #############################################################################
   def isInitialized(self):
      return (self.torrent is not None)

   #############################################################################
   def torrentIsMissing(self):
      return self.torrentDNE

   #############################################################################
   def fileProgress(self):
      """
      Either the mainsize is the same as the torrent (because it finished and 
      was renamed, or the .partial file is the current state of the DL, and 
      we report its size
      """
      
      mainsize = 0 
      if os.path.exists(self.savePath):
         mainsize = os.path.getsize(self.savePath) 

      tempsize = 0 
      if os.path.exists(self.savePath_temp): 
         tempsize = os.path.getsize(self.savePath_temp)


      if tempsize > 0:
         return (tempsize, self.torrentSize)
      elif mainsize > 0:
         if not mainsize == self.torrentSize:
            LOGERROR('Torrent %s is not the correct size...?', self.torrentName)
            return (0,0)
         else:
            return (mainsize, mainsize)
         
      return (0, self.torrentSize)
      
         

   #############################################################################
   def hasCustomFunc(self, funcName):
      if not funcName in self.customCallbacks:
         return False

      return isinstance(self.customCallbacks[funcName], types.FunctionType)


   #############################################################################
   def setCallback(self, name, func):
      if func is None:
         if name in self.customCallbacks:
            del self.customCallbacks[name]
         return

      self.customCallbacks[name] = func
         
   #############################################################################
   def setSecondsBetweenUpdates(self, newSec):
      self.minSecondsBetweenUpdates = newSec

   #############################################################################
   def isDone(self):
      return self.doneObj.isSet()


   #############################################################################
   def displayFunc(self, dpflag=Event(), 
                         fractionDone=None, 
                         timeEst=None,
                         downRate=None,
                         upRate=None,
                         activity=None,
                         statistics=None,
                         **kws):

      # Use caller-set function if it exists
      if self.hasCustomFunc('displayFunc'):
         self.customCallbacks['displayFunc'](dpflag, fractionDone, timeEst, \
                                            downRate, upRate, activity, \
                                            statistics, **kws)
         return


      pr  = ''
      pr += ('Done: %0.1f%%' % (fractionDone*100)) if fractionDone else ''
      pr += (' (%0.1f kB/s' % (downRate/1024.)) if downRate else ' ('
      pr += (' from %d seeds' % statistics.numSeeds) if statistics else ''
      pr += (' and %d peers' % statistics.numPeers) if statistics else ''
      if timeEst:
         pr += ';  Approx %s remaining' % secondsToHumanTime(timeEst)
      pr += ')'
      LOGINFO(pr)



   #############################################################################
   def statusFunc(self, dpflag=Event(), 
                        fractionDone=None, 
                        timeEst=None,
                        downRate=None,
                        upRate=None,
                        activity=None,
                        statistics=None,
                        **kws):

      # Want to be able to query a few things between status calls
      self.lastStats['fracDone'] = fractionDone
      self.lastStats['timeEst']  = timeEst
      self.lastStats['downRate'] = downRate
      self.lastStats['upRate']   = upRate
      self.lastStats['activity'] = activity
      self.lastStats['numSeeds'] = statistics.numSeeds if statistics else None
      self.lastStats['numPeers'] = statistics.numPeers if statistics else None
      self.lastStats['downTotal']= statistics.downTotal if statistics else None
      self.lastStats['upTotal']  = statistics.upTotal if statistics else None

      try:
         if (RightNow() - self.lastUpdate) < self.minSecondsBetweenUpdates:
            return
   
         self.lastUpdate = RightNow()
   
         self.displayFunc(dpflag, fractionDone, timeEst, downRate, upRate,
                                                activity, statistics, **kws)

      finally:
         # Set this flag to let the caller know it's ready for the next update
         dpflag.set()


   #############################################################################
   def getLastStats(self, name):
      return self.lastStats.get(name)

   #############################################################################
   def isStarted(self):
      return (self.startTime is not None)

   #############################################################################
   def isFailed(self):
      return self.dlFailed

   #############################################################################
   def isFinished(self):
      return (self.finishTime is not None) or self.dlFailed

   #############################################################################
   def isRunning(self):
      return self.isStarted() and not self.isFinished()

   #############################################################################
   def finishedFunc(self):
      """
      This function must rename the ".partial" function to the correct name
      """
      self.finishTime = RightNow()
      LOGINFO('Download finished!')
      
      LOGINFO("Moving file")
      LOGINFO("   From:  %s", self.savePath_temp)
      LOGINFO("     To:  %s", self.savePath)
      shutil.move(self.savePath_temp, self.savePath)

      # Use caller-set function if it exists
      if self.hasCustomFunc('finishedFunc'):
         self.customCallbacks['finishedFunc']()

      if self.bt1dow:
         self.bt1dow.shutdown()



   #############################################################################
   def failedFunc(self, msg=''):
      self.dlFailed = True
      LOGEXCEPT('Download failed! %s', msg)

      # Use caller-set function if it exists
      if self.hasCustomFunc('failedFunc'):
         self.customCallbacks['failedFunc'](msg)
         return

      if self.bt1dow:
         self.bt1dow.shutdown()



   #############################################################################
   def errorFunc(self, errMsg):
      # Use caller-set function if it exists
      if 'failed hash check, re-downloading it' in errMsg:
         self.nHashFailures = self.nHashFailures +1
      
      if self.hasCustomFunc('errorFunc'):
         self.customCallbacks['errorFunc'](errMsg)
         return

      LOGEXCEPT(errMsg)

   #############################################################################
   def excFunc(self, errMsg):
      # Use caller-set function if it exists
      if self.hasCustomFunc('excFunc'):
         self.customCallbacks['excFunc'](errMsg)
         return

      LOGEXCEPT(errMsg)

   #############################################################################
   def chooseFileFunc(self, default, fsize, saveas, thedir):
      # Use caller-set function if it exists
      if self.hasCustomFunc('chooseFileFunc'):
         self.customCallbacks['chooseFileFunc'](default, fsize, saveas, thedir)
         return

      return (default if saveas is None else saveas)


   #############################################################################
   def getTDMState(self):
      if self.nHashFailures >= self.killAfterNHashFails:
         return 'HashFailures'
      
      if self.disabled:
         return 'Disabled'

      if not self.isInitialized():
         return 'Uninitialized'

      if self.torrentDNE:
         return 'TorrentDNE'

      if not self.isStarted():
         return 'ReadyToStart'

      if self.dlFailed:
         return 'DownloadFailed'

      if self.isFinished():
         return 'DownloadFinished'

      return 'Downloading'

   #############################################################################
   def startDownload(self):
      return self.doTheDownloadThing(async=True)

   #############################################################################
   @AllowAsync
   def doTheDownloadThing(self):
      """
      This was copied and modified directly from btdownloadheadless.py 
      """

      if self.disabled:
         LOGERROR('Attempted to start DL but DISABLE_TORRENT is True') 
         return
   
      while 1:

         # Use this var to identify if we've started downloading
         self.startTime = RightNow()


         configdir = ConfigDir(self.cacheDir)
         defaultsToIgnore = ['responsefile', 'url', 'priority']
         configdir.setDefaults(defaults, defaultsToIgnore)
         config = configdir.loadConfig()
         config['responsefile']   = self.torrent
         config['url']            = ''
         config['priority']       = ''
         config['saveas']         = self.savePath_temp
         config['save_options']   = 0
         config['max_uploads']    = 0
         config['max_files_open'] = 25

         configdir.deleteOldCacheData(config['expire_cache_data'])
   
         myid = createPeerID()
         seed(myid)
         
         rawserver = RawServer( self.doneObj, 
                                config['timeout_check_interval'],
                                config['timeout'], 
                                ipv6_enable = config['ipv6_enabled'],
                                failfunc = self.failedFunc, 
                                errorfunc = self.errorFunc)

         upnp_type = UPnP_test(config['upnp_nat_access'])

         while True:
            try:
               listen_port = rawserver.find_and_bind( \
                                 config['minport'], 
                                 config['maxport'],
                                 config['bind'], 
                                 ipv6_socket_style = config['ipv6_binds_v4'],
                                 upnp = upnp_type, 
                                 randomizer = config['random_port'])
               break
            except socketerror, e:
               if upnp_type and e == UPnP_ERROR:
                  LOGWARN('WARNING: COULD NOT FORWARD VIA UPnP')
                  upnp_type = 0
                  continue
               LOGERROR("error: Couldn't listen - " + str(e))
               self.failedFunc()
               return
   
         if not self.response:
            break
   
         infohash = sha(bencode(self.response['info'])).digest()

         LOGINFO('Downloading: %s', self.torrentName)
         curr,tot = [float(a)/MEGABYTE for a in self.fileProgress()]
         if curr == 0:
            LOGINFO('Starting new download')
         elif curr==tot:
            LOGINFO('Torrent already finished!')
            return
         else:
            LOGINFO('Picking up where left off at %0.0f of %0.0f MB' % (curr,tot))
   
         self.bt1dow = BT1Download( self.statusFunc, 
                            self.finishedFunc, 
                            self.errorFunc, 
                            self.excFunc,
                            self.doneObj,
                            config, 
                            self.response, 
                            infohash, 
                            myid, 
                            rawserver, 
                            listen_port,
                            configdir)
         
         if not self.bt1dow.saveAs(self.chooseFileFunc):
            break
   
         if not self.bt1dow.initFiles(old_style = True):
            break

         if not self.bt1dow.startEngine():
            self.bt1dow.shutdown()
            break

         if self.nHashFailures >= self.killAfterNHashFails:
            self.bt1dow.shutdown()
            self.customCallbacks['errorFunc']('hashFail')
            break

         self.bt1dow.startRerequester()
         self.bt1dow.autoStats()
   
         if not self.bt1dow.am_I_finished():
            self.statusFunc(activity = 'Connecting to peers')

         rawserver.listen_forever(self.bt1dow.getPortHandler())
         self.statusFunc(activity = 'Shutting down')
         self.bt1dow.shutdown()
         break

      try:
         rawserver.shutdown()
      except:
         pass

      if not self.isDone():
         self.failedFunc()


# Run this file to test with your target torrent.  Also shows an example
# of overriding methods with other custom methods.  Just about 
# any of the methods of TorrentDownloadManager can be replaced like this
if __name__=="__main__":
   tdm = TorrentDownloadManager()
   tdm.setupTorrent(argv[1], argv[2])

   # Replace full-featured LOGINFOs with simple print message
   def simplePrint( dpflag=Event(), 
                    fractionDone=None, 
                    timeEst=None,
                    downRate=None,
                    upRate=None,
                    activity=None,
                    statistics=None,
                    **kws):
      
      if fractionDone:
         print 'TorrentThread: %0.1f%% done;' % (fractionDone*100),

      if timeEst:
         print ', about %s remaining' %  secondsToHumanTime(timeEst), 

      if activity:
         print ' (%s)'%activity
      else:
         print ''

      sys.stdout.flush()

   # Finish funct will still move file.partial to file, this is everything else
   def notifyFinished():
      print 'TorrentThread: Finished downloading at %s' % unixTimeToFormatStr(RightNow())
      sys.stdout.flush()
      

   tdm.setCallback('displayFunc', simplePrint)
   tdm.setCallback('finishedFunc', notifyFinished)
   tdm.setSecondsBetweenUpdates(1)

   thr = tdm.startDownload(async=True)

   # The above call was asynchronous
   while not thr.isFinished():
      print 'MainThread:    Still downloading;',
      if tdm.getLastStats('downRate'):
         print ' Last dl speed: %0.1f kB/s' % (tdm.getLastStats('downRate')/1024.)
      else: 
         print ''
      sys.stdout.flush()
      sleep(10)
       
   
   print 'Finished downloading!  Exiting...'



