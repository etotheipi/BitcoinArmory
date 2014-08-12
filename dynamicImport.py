import os
import sys
from armoryengine.ArmoryUtils import LOGEXCEPT


def getModuleList(inDir):
   moduleMap = {}
   if not os.path.exists(inDir):
      return moduleMap

   
   for fn in os.listdir(inDir):
      if not fn.endswith('.py') and not fn.endswith('.sig'):
         continue

      try:
         modName = fn.split('.')[0]
         fullfn = os.path.join(inDir, fn)
         with open(fullfn, 'r') as f:
            fileData = f.read()

         if not modName in moduleMap:
            moduleMap[modName] = {}
      
         if fn.endswith('.py'):
            moduleMap[modName]['SourceCode'] = fileData
            moduleMap[modName]['SourceDir']  = inDir
            moduleMap[modName]['Filename']   = fn
         elif fn.endswith('.sig'):
            moduleMap[modName]['SigData']  = fileData
      except:
         LOGEXCEPT('Loading plugin %s failed.  Skipping' % fullfn)
         
      
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

