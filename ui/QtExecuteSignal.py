##############################################################################
#                                                                            #
# Copyright (C) 2017, goatpig                                                #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtCore import SIGNAL
from threading import Thread
from time import sleep

##############################################################################
class QtExecuteSignal(object):
   
   ###########################################################################
   def __init__(self, mainWnd):
      self.mainWnd = mainWnd
      
      self.mainWnd.connect(\
         self.mainWnd, SIGNAL("executeSignal"), self.methodSlot)
      
      self.waiting = {}
      
   ###########################################################################
   def executeMethod(self, _callable, *args):
      self.mainWnd.emit(SIGNAL("executeSignal"), _callable, *args)
      
   ###########################################################################
   def methodSlot(self, _callable, *args):
      _callable(*args)

   ###########################################################################
   def callLater(self, delay, _callable, *_args):
      
      #if a given method is already waiting on delayed execution, update the
      #args and return
      if _callable in self.waiting:
         self.waiting[_callable] = _args
         return
      
      self.waiting[_callable] = _args
      thr = Thread(target=self.callLaterThread, args=(delay, _callable) + _args)
      thr.start()
      
   ###########################################################################
   def callLaterThread(self, delay, _callable, *args):
      sleep(delay)
      self.waiting.pop(_callable, None)
      self.executeMethod(_callable, *args)