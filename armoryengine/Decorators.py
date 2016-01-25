################################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.                         
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

from armoryengine.ArmoryUtils import send_email, LOGERROR, LOGRAWDATA,\
   CLI_OPTIONS
import functools
import sys
from threading import Lock
import traceback

# Following this pattern to allow arguments to be passed to this decorator:
# http://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
def EmailOutput(send_from, server, password, send_to, subject='Armory Output'):
   def ActualEmailOutputDecorator(func):
      @functools.wraps(func)  # Pull in certain "helper" data from dec'd func
      def wrapper(*args, **kwargs):
         ret = func(*args, **kwargs)  # Run dec'd func before sending e-mail
         if ret and send_from and server and password and send_to:
            send_email(send_from, server, password, send_to, subject, ret)
         return ret
      return wrapper

   return ActualEmailOutputDecorator


# Windows does not handle extensions very well in QFileDialog.getSaveFileName
# When double extensions (e.g. .sigcollect.tx) are used windows will return duplicates.
# 
# This decorator removes just the longest repeating extension
# Examples:
#     filename.a.b.c.a.b.c will reduce to filename.a.b.c
#     filename.a.b.b.a.b.b will reduce to filename.a.b
def RemoveRepeatingExtensions(func):
   @functools.wraps(func)  # Pull in certain "helper" data from dec'd func
   def inner(*args, **kwargs):
      rv = func(*args, **kwargs)
      segs = rv.split('.')
      isDupExt = lambda s, n : s[-n*2:-n] == s[-n:]
      # Try the maximum amount of repeating extensions first.
      for i in range(1, len(segs)/2 + 1)[::-1]:
         if isDupExt(segs, i):
            while isDupExt(segs, i):
               segs = segs[:-i]
      return '.'.join(segs)
   return inner


# A decorator meant for the JSON RPC functions. It's important to both log
# errors on the server and notify the client that an error occurred. This
# decorator sets up a standardized way to catch errors that occur in a function
# and report them. The drawback is that any decorated functs that do their own
# try/catches won't have access to this functionality since those errors will
# have been caught.
def catchErrsForJSON(func):
   @functools.wraps(func)  # Pull in certain "helper" data from dec'd func
   def inner(*args, **kwargs):
      jsonPrefix = "jsonrpc_"
      rv = None
      errTB = None
      errFrame = None
      errDepth = 0

      # Just call the funct. If no errs are thrown, or if errs are caught before
      # returning, we'll get through this. Otherwise, get the error info and
      # place it in the log.
      try:
         rv = func(*args, **kwargs)

      except:
         # get the error info and ignore the 1st frame (i.e., this funct).
         (errType, errVal, errTB) = sys.exc_info()
         errFrame = errTB.tb_frame.f_back

         # Save basic info on the trace.
         rv = {}
         errStr = 'An error occurred in %s' % func.__name__[len(jsonPrefix):]
         errTypeStr = 'Error Type = \'%s\'' % errType.__name__
         errValStr = 'Error Value = \'%s\'' % errVal
         rv['Error'] = errStr
         rv['Error Type'] = errType.__name__
         rv['Error Value'] = str(errVal) # If type has no val, this'll be blank
         LOGRAWDATA(errStr)
         LOGRAWDATA(errTypeStr)
         LOGRAWDATA(errValStr)
         #LOGERROR(errStr)
         #LOGERROR(errTypeStr)
         #LOGERROR(errValStr)

         traceback.print_exc(None if CLI_OPTIONS.doDebug else 10)


      finally:
         # Delete circular references and return the error dict.
         if errTB:
            del errTB 
            del errFrame  # Not totally sure this is necessary. Just in case....
         return rv
   return inner

#Makes sure only a single thread is running the method at a given time,
#using threading.Lock() 
def singleEntrantMethod(func):
   @functools.wraps(func)  # Pull in certain "helper" data from dec'd func
   def inner(self, *args, **kwargs):
      #if self doesn't have attribute mutex, give it one
      try:
         self.mutex.acquire()
      except AttributeError:
         self.mutex = Lock()
         self.mutex.acquire()
      try:
         rt = func(self, *args, **kwargs)
      except:
         raise
      finally:
         self.mutex.release()
      return rt
   return inner
