################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from ArmoryUtils import *
import os
from jasvet import readSigBlock
from copy import deepcopy


################################################################################
# NOTE:  These methods DO NOT verify signatures.  It is assumed that the 
#        signature verification already happened, and these methods were only
#        called if the signatures were good.  They can be called on blocks
#        of text WITH OR WITHOUT the signature block data (either pass it 
#        the signed block, or just whats inside the block).

SIGNED_BLOCK_HEAD = '-----BEGIN BITCOIN SIGNED MESSAGE-----'
SIGNED_BLOCK_TAIL = '-----BEGIN BITCOIN SIGNATURE-----'

################################################################################
################################################################################
class changelogParser(object):
   """
   Returns a list of list of lists representing all version & changelg to the
   stop version (or all versions, if 0)
   
   
   changeLog == 
      [
         [ '0.88.1', 'December 27, 2013',
            [
               [ 'Auto-run Bitcoind', 'This version will now run ...'],
               [ 'Mac/OSX Version',   'Binaries now available on ...'],
               [ 'Signed installers', 'All binaries are now sign ...']  
            ]
         ]
         [ '0.87', 'April 18, 2013',
            [ 
               [ 'QR Codes',          'QR codes added everywhere ...'],
               [ 'Export History',    'Export tx history to CSV  ...']  
            ]
         ]
         ...
      ]

   """


   #############################################################################
   def __init__(self, filename='', filetext=''):
      self.changelog = []
      if not filename and not filetext:
         return

      if filename and os.path.exists(filename):
         f = open(filename, 'r')
         filetext = f.read()
         f.close()

      self.parseChangelogText(filetext)
      
      

   #############################################################################
   def parseChangelogFile(self, filename):
      if not os.path.exists(filename):
         LOGERROR('File does not exist: %s', filename)
   
      f = open(filename,'r')
      verdata = f.read()
      f.close()
   
      return self.parseVersionsText(verdata)
      
      
   
   #############################################################################
   def parseChangelogText(self, fileText):
   
      self.changelog = []

      if fileText is None:
         return None

   
      try:
         if SIGNED_BLOCK_HEAD in fileText:
            fileText = readSigBlock(fileText)[1]
      
         versionLines = [line.strip() for line in fileText.split('\n')][::-1]
         
            
         if len(versionLines)==0:
            return None
      
         # All lines have been stripped already
         while len(versionLines) > 0:
            line = versionLines.pop()
      
            if line.startswith('#') or len(line)==0:
               continue
   
      
            if line.startswith('VERSION') and len(line.split())==2:
               self.changelog.append([line.split(' ')[-1], '', []])
            elif line.upper().startswith('RELEASED'):
               self.changelog[-1][1] = line[8:].strip()
            elif line.startswith('-'):
               featureTitle = line[2:]
               self.changelog[-1][2].append([featureTitle, ''])
            else:
               curr = self.changelog[-1][2][-1][-1]
               self.changelog[-1][2][-1][-1] += ('' if len(curr)==0 else ' ') + line
   
            return self.getChangelog()
      except:
         LOGEXCEPT('Failed to parse changelog')
         return None
   

   #############################################################################
   def getChangelog(self, stopAtVersion=0, dontStartBefore=UINT32_MAX):
      output = []
      for ver in self.changelog:
         verInt = getVersionInt(readVersionString(ver[0]))

         if verInt > dontStartBefore:
            continue

         if verInt <= stopAtVersion:
            break

         output.append(ver[:])

      return output






################################################################################
################################################################################
class downloadLinkParser(object):
   """ 
   Parse files with the following format:
   
   -----BEGIN BITCOIN SIGNED MESSAGE-----
   # Armory for Windows
   Armory 0.91 Windows XP        32     http://url/armory_0.91_xp32.exe  3afb9881c32
   Armory 0.91 Windows XP        64     http://url/armory_0.91_xp64.exe  8993ab127cf
   Armory 0.91 Windows Vista,7,8 32,64  http://url/armory_0.91.exe       7f3b9964aa3
   
   # Offline Bundles
   ArmoryOffline 0.88 Ubuntu 10.04  32  http://url/offbundle-32.tar.gz   641382c93b9
   ArmoryOffline 0.88 Ubuntu 12.10  32  http://url/offbundle-64.tar.gz   5541af39c84

   # Windows 32-bit Satoshi (Bitcoin-Qt/bitcoind)
   Satoshi 0.9.0 Windows XP,Vista,7,8 32,64 http://btc.org/win0.9.0.exe  118372a9ff3
   Satoshi 0.9.0 Ubuntu  10.04              http://btc.org/win0.9.0.deb  2aa3f763c3b

   -----BEGIN BITCOIN SIGNATURE-----
   ac389861cff8a989ae57ae67af43cb3716ca189aa178cff893179531
   -----END BITCOIN SIGNATURE-----


   This will return a heavily-nested dictionary that will be easy to look up
   after we have reduced the current OS to the right set of keys (we will 
   create a function that takes the output of 
      platform.system(),
      platform.mac_ver(),
      platform.linux_distribution(), and
      platform.win32_ver()
   and returns a sequence of keys we can use to look up the correct version

   self.downloadMap['Armory']['0.91']['Windows']['Vista']['64'] -->
                           ['http://url/armory_0.91.exe', '7f3b9964aa3']

   Actually use "getDownloadLink 

   """

   #############################################################################
   def __init__(self, filename='', filetext=''):
      self.downloadMap = {}
      if not filename and not filetext:
         return

      if filename and os.path.exists(filename):
         f = open(filename, 'r')
         self.parseDownloadList(f.read())
         f.close()
      elif filetext:
         self.parseDownloadList(filetext)

   

   #############################################################################
   def parseDownloadList(self, fileText):
      self.downloadMap = {}

      if fileText is None:
         return {}
   
      def insertLink(mapObj, urlAndHash, keyList):
         if len(keyList)>1:
            if not keyList[0] in mapObj:
               mapObj[keyList[0]] = {}
            insertLink(mapObj[keyList[0]], urlAndHash, keyList[1:])
         else:
            mapObj[keyList[0]] = urlAndHash
   

      try:
         if SIGNED_BLOCK_HEAD in fileText:
            fileText = readSigBlock(fileText)[1]
   
   
         dlLines = [line.strip() for line in fileText.split('\n')][::-1]
      
         while len(dlLines) > 0:
      
            line = dlLines.pop()
      
            if line.startswith('#') or len(line)==0:
               continue
      
            lineLists  = [pc.split(',') for pc in line.split()[:-2]]
            urlAndHash = line.split()[-2:]
      
            APPLIST, VERLIST, OSLIST, SUBOSLIST, BITLIST = range(5)
   
            for app in lineLists[APPLIST]:
               for ver in lineLists[VERLIST]:
                  for opsys in lineLists[OSLIST]:
                     for subOS in lineLists[SUBOSLIST]:
                        for nbit in lineLists[BITLIST]:
                           insertLink(self.downloadMap, 
                                      urlAndHash, 
                                      [app, ver, opsys, subOS, nbit])
      
      
         return self.getNestedDownloadMap()
      except:
         LOGEXCEPT('Failed to parse downloads')
         return None
      
         
   #############################################################################
   def printDownloadMap(self):

      def recursePrint(theObj, indent=0):
         if not isinstance(theObj, dict):
            print ' '*indent + str(theObj)
         else:
            for key,val in theObj.iteritems():
               print ' '*indent + key + ':'
               recursePrint(theObj[key], indent+5)

      recursePrint(self.downloadMap)
         
   #############################################################################
   def getDownloadLink(self, *keyList):

      def recurseGet(theMap, keyList):
         if len(keyList)==0:
            return None
      
         if not isinstance(theMap, dict):
            return None
      
         if len(keyList)>1:
            if not keyList[0] in theMap:
               return None
            return recurseGet(theMap[keyList[0]], keyList[1:])
         else:
            return theMap[keyList[0]]

      if len(keyList)==0:
         return None
   
      return recurseGet(self.downloadMap, keyList)
   
   
   #############################################################################
   def getNestedDownloadMap(self):
      return deepcopy(self.downloadMap)
      
   
   
################################################################################
################################################################################
class notificationParser(object):
   """
   # PRIORITY VALUES:
   #    Test announce:          1024
   #    General Announcment:    2048
   #    Important non-critical: 3072
   #    Critical/security sens: 4096
   # 
   # Unique ID must be first, and signals that this is a new notification
   
   UNIQUEID:   873fbc11
   VERSION:    0
   STARTTIME:  0
   EXPIRES:    1500111222
   CANCELID:   []
   MINVERSION: 0.87.2
   MAXVERSION: 0.88.1
   PRIORITY:   4096
   NOTIFYSEND: False
   NOTIFYRECV: True
   SHORTDESCR: Until further notice, require 30 confirmations for incoming transactions.
   LONGDESCR:
      THIS IS A FAKE ALERT FOR TESTING PURPOSES:
   
      There is some turbulence on the network that may result in some transactions
      being accidentally reversed up to 30 confirmations.  A clever attacker may
      be able to exploit this to scam you.  For incoming transactions from
      parties with no existing trust, please wait at least 30 confirmations before
      considering the coins to be yours.
      *****
   """

   #############################################################################
   def __init__(self, filename='', filetext=''):
      self.notifications = {}
      if not filename and not filetext:
         return

      if filename and os.path.exists(filename):
         f = open(filename, 'r')
         filetext = f.read() 
         f.close()
      
      self.parseNotificationText(filetext)

   
   

   #############################################################################
   def parseNotificationText(self, fileText):
      self.notifications = {}

      if fileText is None:
         return None
   

      try:
         if SIGNED_BLOCK_HEAD in fileText:
            fileText = readSigBlock(fileText)[1]
      
         notifyLines = [line.strip() for line in fileText.split('\n')][::-1]
      
      
         currID = ''
         readLongDescr = False
         longDescrAccum = ''
         
         while len(notifyLines) > 0:
      
            line = notifyLines.pop()
      
            if not readLongDescr and (line.startswith('#') or len(line)==0):
               continue
      
            if line.upper().startswith('UNIQUEID'):
               currID = line.split(':')[-1].strip()
               self.notifications[currID] = {}
            elif line.upper().startswith('LONGDESCR'):
               readLongDescr = True
            elif line.startswith("*****"):
               readLongDescr = False
               self.notifications[currID]['LONGDESCR'] = longDescrAccum
               longDescrAccum = ''
            elif readLongDescr:
               if len(line.strip())==0:
                  longDescrAccum += '<br><br>'
               else:
                  longDescrAccum += line.strip() + ' '
            else:
               key = line.split(':')[ 0].strip().upper()
               val = line.split(':')[-1].strip()
               self.notifications[currID][key] = val
   
         return self.getNotificationMap()
      except:
         LOGEXCEPT('Failed to parse notifications')
         return None
      
   
   #############################################################################
   def getNotificationMap(self):
      return deepcopy(self.notifications)



# kate: indent-width 3; replace-tabs on;
