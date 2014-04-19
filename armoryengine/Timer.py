################################################################################
#
# Copyright (C) 2011-2014, Armory Technologies, Inc.                          
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
from armoryengine.ArmoryUtils import LOGWARN, RightNow, LOGERROR
   
class Timer(object):
   
   ################################################################################
   #  
   #  Keep track of lots of different timers:
   #
   #     Key:    timerName  
   #     Value:  [cumulTime, numStart, lastStart, isRunning]
   #
   timerMap = {}
   
   def startTimer(self, timerName):
      if not self.timerMap.has_key(timerName):
         self.timerMap[timerName] = [0, 0, 0, False]
      timerEntry = self.timerMap[timerName]
      timerEntry[1] += 1
      timerEntry[2]  = RightNow()
      timerEntry[3]  = True
   
   def stopTimer(self, timerName):
      if not self.timerMap.has_key(timerName):
         LOGWARN('Requested stop timer that does not exist! (%s)' % timerName)
         return
      if not self.timerMap[timerName][3]:
         LOGWARN('Requested stop timer that is not running! (%s)' % timerName)
         return
      timerEntry = self.timerMap[timerName]
      timerEntry[0] += RightNow() - timerEntry[2]
      timerEntry[2]  = 0
      timerEntry[3]  = False
   
   def resetTimer(self, timerName):
      if not self.timerMap.has_key(timerName):
         LOGERROR('Requested reset timer that does not exist! (%s)' % timerName)
      # Even if it didn't exist, it will be created now
      self.timerMap[timerName] = [0, 0, 0, False]
   
   def readTimer(self, timerName):
      if not self.timerMap.has_key(timerName):
         LOGERROR('Requested read timer that does not exist! (%s)' % timerName)
         return
      timerEntry = self.timerMap[timerName]
      return timerEntry[0] + (RightNow() - timerEntry[2])
   
   def printTimings(self):
      print 'Timings:  '.ljust(30), 
      print 'nCall'.rjust(13),
      print 'cumulTime'.rjust(13),
      print 'avgTime'.rjust(13)
      print '-'*70
      for tname,quad in self.timerMap.iteritems():
         print ('%s' % tname).ljust(30), 
         print ('%d' % quad[1]).rjust(13),
         print ('%0.6f' % quad[0]).rjust(13),
         avg = quad[0]/quad[1]
         print ('%0.6f' % avg).rjust(13)
      print '-'*70
   
   def saveTimingsCSV(self, fname):
      f = open(fname, 'w')
      f.write( 'TimerName,')
      f.write( 'nCall,')
      f.write( 'cumulTime,')
      f.write( 'avgTime\n\n')
      for tname,quad in self.timerMap.iteritems():
         f.write('%s,' % tname)
         f.write('%d,' % quad[1])
         f.write('%0.6f,' % quad[0])
         avg = quad[0]/quad[1]
         f.write('%0.6f\n' % avg)
      f.write('\n\nNote: timings may be incorrect if errors '
                         'were triggered in the timed functions')
      print 'Saved timings to file: %s' % fname

   def __init__(selfparams):  # @NoSelf
      pass
   

def TimeThisFunction(func):
   timer = Timer()
   def inner(*args, **kwargs):
      timer.startTimer(func.__name__)
      ret = func(*args, **kwargs)
      timer.stopTimer(func.__name__)
      return ret
   return inner
