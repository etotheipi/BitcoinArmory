###############################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
###############################################################################

import threading
import time

from ArmoryLog import *


class PyBackgroundThread(threading.Thread):
   """
   Wraps a function in a threading.Thread object which will run
   that function in a separate thread.  Calling self.start() will
   return immediately, but will start running that function in
   separate thread.  You can check its progress later by using
   self.isRunning() or self.isFinished().  If the function returns
   a value, use self.getOutput().  Use self.getElapsedSeconds()
   to find out how long it took.
   """

   def __init__(self, *args, **kwargs):
      threading.Thread.__init__(self)

      self.output     = None
      self.startedAt  = UNINITIALIZED
      self.finishedAt = UNINITIALIZED
      self.errorThrown = None
      self.passAsync = None
      self.setDaemon(True)

      if len(args)==0:
         self.func  = lambda: ()
      else:
         if hasattr(args[0], '__call__'):
            self.setThreadFunction(args[0], *args[1:], **kwargs)
         else:
            raise TypeError('PyBkgdThread ctor arg1 must be a function')

   def setThreadFunction(self, thefunc, *args, **kwargs):
      def funcPartial():
         return thefunc(*args, **kwargs)
      self.func = funcPartial

   def setDaemon(self, yesno):
      if self.isStarted():
         LOGERROR('Must set daemon property before starting thread')
      else:
         super(PyBackgroundThread, self).setDaemon(yesno)

   def isFinished(self):
      return not (self.finishedAt==UNINITIALIZED)

   def isStarted(self):
      return not (self.startedAt==UNINITIALIZED)

   def isRunning(self):
      return (self.isStarted() and not self.isFinished())

   def getElapsedSeconds(self):
      if self.isFinished():
         return self.finishedAt - self.startedAt
      else:
         LOGERROR('Thread is not finished yet!')
         return None

   def getOutput(self):
      if not self.isFinished():
         if self.isRunning():
            LOGERROR('Cannot get output while thread is running')
         else:
            LOGERROR('Thread was never .start()ed')
         return None

      return self.output

   def didThrowError(self):
      return (self.errorThrown is not None)

   def raiseLastError(self):
      if self.errorThrown is None:
         return
      raise self.errorThrown

   def getErrorType(self):
      if self.errorThrown is None:
         return None
      return type(self.errorThrown)

   def getErrorMsg(self):
      if self.errorThrown is None:
         return ''
      return self.errorThrown.args[0]


   def start(self):
      # The prefunc is blocking.  Probably preparing something
      # that needs to be in place before we start the thread
      self.startedAt = time.time()
      super(PyBackgroundThread, self).start()

   def run(self):
      # This should not be called manually.  Only call start()
      try:
         self.output = self.func()
      except Exception as e:
         LOGEXCEPT('Error in pybkgdthread: %s', str(e))
         self.errorThrown = e
      self.finishedAt = time.time()

      if not self.passAsync: return
      if hasattr(self.passAsync, '__call__'):
         self.passAsync()

   def reset(self):
      self.output = None
      self.startedAt  = UNINITIALIZED
      self.finishedAt = UNINITIALIZED
      self.errorThrown = None

   def restart(self):
      self.reset()
      self.start()


# Define a decorator that allows the function to be called asynchronously
def AllowAsync(func):
   def wrappedFunc(*args, **kwargs):
      if not 'async' in kwargs or kwargs['async']==False:
         # Run the function normally
         if 'async' in kwargs:
            del kwargs['async']
         return func(*args, **kwargs)
      else:
         # Run the function as a background thread
         passAsync = kwargs['async']
         del kwargs['async']

         thr = PyBackgroundThread(func, *args, **kwargs)
         thr.passAsync = passAsync
         thr.start()
         return thr

   return wrappedFunc


