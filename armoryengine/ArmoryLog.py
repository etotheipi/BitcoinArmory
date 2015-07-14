###############################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
###############################################################################

import logging
import sys
import traceback

from ArmoryOptions import *


# Want to get the line in which an error was triggered, but by wrapping
# the logger function (as I will below), the displayed "file:linenum"
# references the logger function, not the function that called it.
# So I use traceback to find the file and line number two up in the
# stack trace, and return that to be displayed instead of default
# [Is this a hack?  Yes and no.  I see no other way to do this]
def _getCallerLine():
   stkTwoUp = traceback.extract_stack()[-3]
   filename,method = stkTwoUp[0], stkTwoUp[1]
   return '%s:%d' % (os.path.basename(filename),method)

def _getLogger():
   return logging.getLogger('')

def _logexcept_override(type, value, tback):
   strList = traceback.format_exception(type,value,tback)
   LOGERROR(''.join(strList))

def _chopLogFile(filename, size):
   if not os.path.exists(filename):
      print 'Log file doesn\'t exist [yet]'
      return

   logFile = open(filename, 'r')
   logFile.seek(0,2) # move the cursor to the end of the file
   currentSize = logFile.tell()
   if currentSize > size:
      # this makes sure we don't get stuck reading an entire file
      # that is bigger than the available memory.
      # Also have to avoid cutting off the first line if truncating the file.
      if currentSize > size+MEGABYTE:
         logFile.seek(-(size+MEGABYTE), 2)
      else:
         logFile.seek(0,0)
      logLines = logFile.readlines()
      logFile.close()

      nBytes,nLines = 0,0;
      for line in logLines[::-1]:
         nBytes += len(line)
         nLines += 1
         if nBytes>size:
            break

      logFile = open(filename, 'w')
      for line in logLines[-nLines:]:
         logFile.write(line)
      logFile.close()

class _stringAggregator(object):
   def __init__(self):
      self.theStr = ''
   def getStr(self):
      return self.theStr
   def write(self, theStr):
      self.theStr += theStr


# When there's an error in the logging function, it's impossible to find!
# These wrappers will print the full stack so that it's possible to find
# which line triggered the error
def LOGDEBUG(msg, *a):
   try:
      logger = _getLogger()
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = _getCallerLine() + ' - '
      logger.debug(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

def LOGINFO(msg, *a):
   try:
      logger = _getLogger()
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = _getCallerLine() + ' - '
      logger.info(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

def LOGWARN(msg, *a):
   try:
      logger = _getLogger()
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = _getCallerLine() + ' - '
      logger.warning(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

def LOGERROR(msg, *a):
   try:
      logger = _getLogger()
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = _getCallerLine() + ' - '
      logger.error(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

def LOGCRIT(msg, *a):
   try:
      logger = _getLogger()
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = _getCallerLine() + ' - '
      logger.critical(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

def LOGEXCEPT(msg, *a):
   try:
      logger = _getLogger()
      logstr = msg if len(a)==0 else (msg%a)
      callerStr = _getCallerLine() + ' - '
      logger.exception(callerStr + logstr)
   except TypeError:
      traceback.print_stack()
      raise

# A method to redirect pprint() calls to the log file
# Need a way to take a pprint-able object, and redirect its output to file
# Do this by swapping out sys.stdout temporarily, execute theObj.pprint()
# then set sys.stdout back to the original.
def LOGPPRINT(theObj, loglevel=logging.DEBUG):
   sys.stdout = _stringAggregator()
   theObj.pprint()
   printedStr = sys.stdout.getStr()
   sys.stdout = sys.__stdout__
   stkOneUp = traceback.extract_stack()[-2]
   filename,method = stkOneUp[0], stkOneUp[1]
   methodStr  = '(PPRINT from %s:%d)\n' % (filename,method)
   logger = _getLogger()
   logger.log(loglevel, methodStr + printedStr)

# For super-debug mode, we'll write out raw data
def LOGRAWDATA(rawStr, loglevel=logging.DEBUG):
   from ArmoryUtils import prettyHex, binary_to_hex, isLikelyDataType
   dtype = isLikelyDataType(rawStr)
   stkOneUp = traceback.extract_stack()[-2]
   filename,method = stkOneUp[0], stkOneUp[1]
   methodStr  = '(PPRINT from %s:%d)\n' % (filename,method)
   pstr = rawStr[:]
   if dtype==DATATYPE.Binary:
      pstr = binary_to_hex(rawStr)
      pstr = prettyHex(pstr, indent='  ', withAddr=False)
   elif dtype==DATATYPE.Hex:
      pstr = prettyHex(pstr, indent='  ', withAddr=False)
   else:
      pstr = '   ' + '\n   '.join(pstr.split('\n'))

   logger = _getLogger()
   logger.log(loglevel, methodStr + pstr)


#########  INITIALIZE LOGGING UTILITIES  ##########
#
# Setup logging to write INFO+ to file, and WARNING+ to console
# In debug mode, will write DEBUG+ to file and INFO+ to console
#

def initializeLog():
   logger = _getLogger()
   consoleThreshold = logging.WARNING
   fileThreshold = logging.INFO

   if getLogDisableFlag():
      print 'Logging is disabled'
      logger.disabled = True
      consoleThreshold  += 100
      fileThreshold     += 100

   if getDebugFlag() or getNetLogFlag() or getMultiThreadDebugFlag():
      # Drop it all one level: console will see INFO, file will see DEBUG
      consoleThreshold  -= 20
      fileThreshold     -= 20

   fileFormatter  = logging.Formatter(
      '%(asctime)s (%(levelname)s) -- %(message)s', datefmt='%Y-%m-%d %H:%M')
   fileHandler = logging.FileHandler(getArmoryLogFile())
   fileHandler.setLevel(fileThreshold)
   fileHandler.setFormatter(fileFormatter)
   logger.addHandler(fileHandler)

   consoleFormatter = logging.Formatter('(%(levelname)s) %(message)s')
   consoleHandler = logging.StreamHandler()
   consoleHandler.setLevel(consoleThreshold)
   consoleHandler.setFormatter( consoleFormatter )
   logger.addHandler(consoleHandler)
   sys.excepthook = _logexcept_override

   # cut the log to 1 MB
   _chopLogFile(getArmoryLogFile(), MEGABYTE)

