import sys
import os

sys.path.append('..')

from ArmoryUtils import ARMORY_HOME_DIR, BTC_HOME_DIR, LOGEXCEPT, \
                        LOGERROR, LOGWARN, LOGINFO, MEGABYTE, \
                        AllowAsync, RightNow, unixTimeToFormatStr, \
                        secondsToHumanTime
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
   

class torrentDownloader(object):
   
   #############################################################################
   def __init__(self, torrentFile, savePath):
      self.setup(torrentFile, savePath)
      

   #############################################################################
   def setup(self, torrentFile, savePath, minSecondsBetweenUpdates=1):

      self.torrent = torrentFile
      self.cacheDir = os.path.join(ARMORY_HOME_DIR, 'bittorrentcache')
      self.doneObj = Event()

      self.customCallbacks = {}

      self.minSecondsBetweenUpdates = minSecondsBetweenUpdates
      self.lastUpdate = RightNow()

      # Get some info about the torrent
      self.response = get_response(self.torrent, '', self.errorFunc)
      self.torrentSize = self.response['info']['length']
      self.torrentName = self.response['info']['name']
      LOGINFO('Torrent name is: %s' %  self.torrentName)
      LOGINFO('Torrent size is: %0.2f MB' %  (self.torrentSize/float(MEGABYTE)))


      self.savePath = savePath
      if self.savePath is None:
         self.savePath = os.path.join(BTC_HOME_DIR, self.torrentName)
      self.savePath_temp = self.savePath + '.partial'

      self.lastStats = {}


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
   def finishedFunc(self):
      """
      This function must rename the ".partial" function to the correct name
      """
      shutil.move(self.savePath_temp, self.savePath)
      LOGINFO('Download finished!')

      # Use caller-set function if it exists
      if self.hasCustomFunc('finishedFunc'):
         self.customCallbacks['finishedFunc']()
         return


   #############################################################################
   def failedFunc(self, msg=''):
      # Use caller-set function if it exists
      if self.hasCustomFunc('failedFunc'):
         self.customCallbacks['failedFunc'](msg)
         return

      LOGEXCEPT('Download failed! %s', msg)

   #############################################################################
   def errorFunc(self, errMsg):
      # Use caller-set function if it exists
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
   @AllowAsync
   def startDownload(self):
      """
      This was copied and modified directly from btdownloadheadless.py 
      """
      while 1:

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
         else:
            LOGINFO('Picking up where left off at %0.0f of %0.0f MB' % (curr,tot))
   
         dow = BT1Download( self.statusFunc, 
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
         
         if not dow.saveAs(self.chooseFileFunc):
            break
   
         if not dow.initFiles(old_style = True):
            break

         if not dow.startEngine():
            dow.shutdown()
            break

         dow.startRerequester()
         dow.autoStats()
   
         if not dow.am_I_finished():
            self.statusFunc(activity = 'connecting to peers')

         rawserver.listen_forever(dow.getPortHandler())
         self.statusFunc(activity = 'shutting down')
         dow.shutdown()
         break

      try:
         rawserver.shutdown()
      except:
         pass

      if not self.isDone():
         self.failedFunc()


# Run this file to test with your target torrent.  Also shows an example
# of overriding methods with other custom methods.  Just about 
# any of the methods of torrentDownloader can be replaced like this
if __name__=="__main__":
   dlobj = torrentDownloader(argv[1], argv[2])

   # Replace full-featured LOGINFOs with simple print message
   def simplePrint( dpflag=Event(), 
                    fractionDone=None, 
                    timeEst=None,
                    downRate=None,
                    upRate=None,
                    activity=None,
                    statistics=None,
                    **kws):
      
      print 'TorrentThread: %0.1f%% done' % (fractionDone*100),
      if timeEst:
         print ', about %s remaining' %  secondsToHumanTime(timeEst)

   # Finish funct will still move file.partial to file, this is everything else
   def notifyFinished():
      print 'TorrentThread: Finished downloading at %s' % unixTimeToFormatStr(RightNow())
      

   dlobj.setCallback('displayFunc', simplePrint)
   dlobj.setCallback('finishedFunc', notifyFinished)
   dlobj.setSecondsBetweenUpdates(1)

   thr = dlobj.startDownload(async=True)

   # The above call was asynchronous
   while not thr.isFinished():
      print 'MainThread:    Still downloading;',
      if dlobj.getLastStats('downRate'):
         print ' Last dl speed: %0.1f kB/s' % (dlobj.getLastStats('downRate')/1024.)
      sleep(10)
       




