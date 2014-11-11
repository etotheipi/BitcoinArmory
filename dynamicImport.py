import os
import sys
from armoryengine.ArmoryUtils import LOGEXCEPT
from zipfile import ZipFile
ZIP_EXTENSION = '.zip'
PY_EXTENSION = '.py'
SIG_EXTENSION = '.sig'
SOURCE_DIR_KEY = 'SourceDir'
SIG_DATA_KEY = 'SigData'
FILENAME_KEY = 'Filename'
SOURCE_CODE_KEY = 'SourceCode'


def getZipContents(filePath):
   zipFile = ZipFile(filePath)
   zipContents = []
   for fileName in zipFile.namelist():
      zipContents.append(zipFile.read(fileName))
   return ''.join(zipContents)

def getModuleList(inDir):
   moduleMap = {}
   if not os.path.exists(inDir):
      return moduleMap

   
   for fileName in os.listdir(inDir):

      if not fileName.endswith(ZIP_EXTENSION) and not fileName.endswith(PY_EXTENSION) and not fileName.endswith(SIG_EXTENSION):
         continue

      try:
         modName = fileName.split('.')[0]
         filePath = os.path.join(inDir, fileName)

         if not modName in moduleMap:
            moduleMap[modName] = {}
            
         if fileName.endswith(ZIP_EXTENSION):
            moduleMap[modName][SOURCE_CODE_KEY] = getZipContents(filePath)
            moduleMap[modName][SOURCE_DIR_KEY]  = inDir
            moduleMap[modName][FILENAME_KEY]   = fileName
         elif fileName.endswith(PY_EXTENSION):
            with open(filePath, 'r') as f:
               fileData = f.read()
            moduleMap[modName][SOURCE_CODE_KEY] = fileData
            moduleMap[modName][SOURCE_DIR_KEY]  = inDir
            moduleMap[modName][FILENAME_KEY]   = fileName
         elif fileName.endswith(SIG_EXTENSION):
            with open(filePath, 'r') as f:
               fileData = f.read()
            moduleMap[modName][SIG_DATA_KEY]  = fileData
      except:
         LOGEXCEPT('Loading plugin %s failed.  Skipping' % filePath)
         
      
   return moduleMap
      

def dynamicImport(inDir, moduleName, injectLocals=None):
   """
   We import from an arbitrary directory, we need to add the dir
   to sys.path, but we want to prevent any shenanigans by an imported
   module that messes with sys.path (perhaps maliciously, but trying
   to import a malicious module without allowing malicious behavior
   is probably impossible--make sure you're using safe code and then
   assume the module is safe). 

   Either way, we're going to assume that the dynamically-imported
   modules are really simple and have no reason to mess with sys.path.
   We will revisit this later if it becomes a barrier to being useful
   """
   if injectLocals is None:
      injectLocals = {}

   pluginPath = os.path.join(inDir, moduleName+'.py')  
   if not os.path.exists(pluginPath):
      return None

   # Join using a character that would be invalid in a pathname
   prevSysPath = '\x00'.join(sys.path)
   sys.path.append(inDir)


   modTemp = __import__(moduleName)
   modTemp.__dict__.update(injectLocals)

   # Assume that sys.path was unmodified by the module
   sys.path = sys.path[:-1]
   currSysPath = '\x00'.join(sys.path)
   if not currSysPath==prevSysPath:
      print '***ERROR: Dynamically imported module messed with sys.path!'
      print '        : Make sure your module does not modify sys.path'
      exit(1)
   
   return modTemp

