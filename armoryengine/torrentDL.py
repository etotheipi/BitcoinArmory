import sys
import os

sys.path.append('..')

from ArmoryUtils import ARMORY_HOME_DIR, BTC_HOME_DIR, LOGEXCEPT, \
                        LOGERROR, LOGWARN, LOGINFO, AllowAsync, RightNow
from BitTornado.download_bt1 import BT1Download, defaults, parse_params, get_response
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
from time import strftime
import types
from BitTornado.clock import clock
from BitTornado import createPeerID, version
from BitTornado.ConfigDir import ConfigDir
from BitTornado.download_bt1 import defaults, download
from BitTornado.ConfigDir import ConfigDir

   

class torrentDownloader(object):
   
   #############################################################################
   def __init__(self, torrentFile, savePath):
      self.setup(torrentFile, savePath)
      

   #############################################################################
   def setup(self, torrentFile, savePath, minSecondsBetweenUpdates=1):

      self.savePath = savePath
      if self.savePath is None:
         self.savePath = os.path.join(BTC_HOME_DIR, 'bootstrap.dat')

      self.savePath_temp = self.savePath + '.partial'

      self.torrent = torrentFile
      self.cacheDir = os.path.join(ARMORY_HOME_DIR, 'bittorrentcache')
      self.doneObj = Event()

      self.customCallbacks = {}

      self.minSecondsBetweenUpdates = minSecondsBetweenUpdates
      self.lastUpdate = RightNow()

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
   def statusFunc(self, dpflag=Event(), 
                        fractionDone=None, 
                        timeEst=None,
                        downRate=None,
                        upRate=None,
                        activity=None,
                        statistics=None,
                        **kws):
      """
      This function must always end with dpflag.set()
      """

      try:

         if (RightNow() - self.lastUpdate) < self.minSecondsBetweenUpdates:
            return
   
         self.lastUpdate = RightNow()
   
         # Use caller-set function if it exists
         if self.hasCustomFunc('statusFunc'):
            self.customCallbacks['statusFunc'](dpflag, fractionDone, timeEst, \
                                               downRate, upRate, activity, \
                                               statistics, **kws)
            return
   
         if activity:
            print 'Doing: %s' % activity
   
         if None in [fractionDone, timeEst, downRate, upRate]:
            print 'No information to display'
         else:
            print 'Done: %0.1f; TimeLeft: %0.1f, (DL,UL) = (%0.1f, %0.1f)' % \
                                 ( fractionDone*100, timeEst, downRate, upRate)

      finally:
         dpflag.set()

   #############################################################################
   def finishedFunc(self):
      """
      This function must rename the ".partial" function to the correct name
      """
      # Use caller-set function if it exists
      if self.hasCustomFunc('finishedFunc'):
         self.customCallbacks['finishedFunc']()
         return

      shutil.move(self.savePath_temp, self.savePath)

      LOGINFO('Download finished!')

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
   
         response = get_response(  config['responsefile'], 
                                   config['url'], 
                                   self.errorFunc)

         if not response:
            break
   
         infohash = sha(bencode(response['info'])).digest()
   
         dow = BT1Download( self.statusFunc, 
                            self.finishedFunc, 
                            self.errorFunc, 
                            self.excFunc,
                            self.doneObj,
                            config, 
                            response, 
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


if __name__=="__main__":
   dlobj = torrentDownloader(argv[1], argv[2])

   def simplePrint( dpflag=Event(), 
                    fractionDone=None, 
                    timeEst=None,
                    downRate=None,
                    upRate=None,
                    activity=None,
                    statistics=None,
                    **kws):
      if fractionDone:
         print '%s: %0.1f%%' % (str(activity), fractionDone*100,)

   dlobj.setCallback('statusFunc', simplePrint)
   dlobj.setSecondsBetweenUpdates(5)

   dlobj.startDownload()




