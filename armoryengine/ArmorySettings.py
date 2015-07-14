###############################################################################
#                                                                             #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                          #
# Distributed under the GNU Affero General Public License (AGPL v3)           #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                        #
#                                                                             #
###############################################################################

import os

from ArmoryUtils import *

class SettingsFile(object):
   """
   This class could be replaced by the built-in QSettings in PyQt, except
   that older versions of PyQt do not support the QSettings (or at least
   I never figured it out).  Easy enough to do it here

   All settings must populated with a simple datatype -- non-simple
   datatypes should be broken down into pieces that are simple:  numbers
   and strings, or lists/tuples of them.

   Will write all the settings to file.  Each line will look like:
         SingleValueSetting1 | 3824.8
         SingleValueSetting2 | this is a string
         Tuple Or List Obj 1 | 12 $ 43 $ 13 $ 33
         Tuple Or List Obj 2 | str1 $ another str
   """

   ############################################################################
   def __init__(self, path=None):
      self.settingsPath = path or getSettingsPath()
      self.settingsMap = {}
      LOGINFO('Using settings file: %s', self.settingsPath)
      if os.path.exists(self.settingsPath):
         self.loadSettingsFile(path)

   ############################################################################
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      for k,v in self.settingsMap.iteritems():
         print indstr + indent + k.ljust(15), v

   ############################################################################
   def hasSetting(self, name):
      return self.settingsMap.has_key(name)

   ############################################################################
   def set(self, name, value):
      if isinstance(value, tuple):
         self.settingsMap[name] = list(value)
      else:
         self.settingsMap[name] = value
      self.writeSettingsFile()

   ############################################################################
   def extend(self, name, value):
      """ Adds/converts setting to list, appends value to the end of it """
      if not self.settingsMap.has_key(name):
         if isinstance(value, list):
            self.set(name, value)
         else:
            self.set(name, [value])
      else:
         origVal = self.get(name, expectList=True)
         if isinstance(value, list):
            origVal.extend(value)
         else:
            origVal.append(value)
         self.settingsMap[name] = origVal
      self.writeSettingsFile()

   ############################################################################
   def get(self, name, expectList=False):
      if not self.hasSetting(name) or self.settingsMap[name]=='':
         return ([] if expectList else '')
      else:
         val = self.settingsMap[name]
         if expectList:
            if isinstance(val, list):
               return val
            else:
               return [val]
         else:
            return val

   ############################################################################
   def getAllSettings(self):
      return self.settingsMap

   ############################################################################
   def getSettingOrSetDefault(self, name, defaultVal, expectList=False):
      output = defaultVal
      if self.hasSetting(name):
         output = self.get(name)
      else:
         self.set(name, defaultVal)

      return output

   ############################################################################
   def delete(self, name):
      if self.hasSetting(name):
         del self.settingsMap[name]
      self.writeSettingsFile()

   ############################################################################
   def writeSettingsFile(self, path=None):
      if not path:
         path = self.settingsPath
      f = open(path, 'w')
      for key,val in self.settingsMap.iteritems():
         try:
            # Skip anything that throws an exception
            valStr = ''
            if   isinstance(val, basestring):
               valStr = val
            elif isinstance(val, int) or \
                 isinstance(val, float) or \
                 isinstance(val, long):
               valStr = str(val)
            elif isinstance(val, list) or \
                 isinstance(val, tuple):
               valStr = ' $  '.join([str(v) for v in val])
            f.write(key.ljust(36))
            f.write(' | ')
            f.write(toBytes(valStr))
            f.write('\n')
         except Exception as e:
            LOGEXCEPT('Invalid entry in SettingsFile... skipping')
      f.close()


   ############################################################################
   def loadSettingsFile(self, path=None):
      if not path:
         path = self.settingsPath

      if not os.path.exists(path):
         raise FileExistsError('Settings file DNE:' + path)

      f = open(path, 'rb')
      sdata = f.read()
      f.close()

      # Automatically convert settings to numeric if possible
      def castVal(v):
         v = v.strip()
         a,b = v.isdigit(), v.replace('.','').isdigit()
         if a:
            return int(v)
         elif b:
            return float(v)
         else:
            if v.lower()=='true':
               return True
            elif v.lower()=='false':
               return False
            else:
               return toUnicode(v)


      sdata = [line.strip() for line in sdata.split('\n')]
      for line in sdata:
         if len(line.strip())==0:
            continue

         try:
            key,vals = line.split('|')
            valList = [castVal(v) for v in vals.split('$')]
            if len(valList)==1:
               self.settingsMap[key.strip()] = valList[0]
            else:
               self.settingsMap[key.strip()] = valList
         except Exception as e:
            LOGEXCEPT('Invalid setting in %s (skipping...)', path)


