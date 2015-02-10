################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import os
import sys
from armoryengine.ArmoryUtils import *
from zipfile import ZipFile
from CppBlockUtils import SecureBinaryData, CryptoECDSA
PY_EXTENSION = '.py'
ZIP_EXTENSION = '.zip'
SIG_EXTENSION = '.sig'
INNER_ZIP_FILENAME = 'inner.zip'
PROPERTIES_FILENAME = 'properties.txt'
SIGNATURE_FILENAME = 'signature.txt'

MODULE_PATH_KEY = 'ModulePath'
MODULE_ZIP_STATUS_KEY = 'ModulZipStatus'

MODULE_ZIP_STATUS = enum("Valid", 'Invalid', 'Unsigned')


# Module structure:
# moduleName.zip (outer zip file):
#    inner.zip (inner zip file with the same name)
#       moduleName.py (python module file
#       <resources> (some files that are resources for the module)
#    properties.txt (signature properties like valid date range)
#    signature.txt (signature of the inner zip file)
def verifyZipSignature(outerZipFilePath):
   result = MODULE_ZIP_STATUS.Invalid
   try:
      dataToSign = None
      signature = None
      outerZipFile = ZipFile(outerZipFilePath)
      # look for a zip file in the name list.
      # There should only be 2 files in this zip:
      #    The inner zip file and the sig file
      if len(outerZipFile.namelist()) == 3:
         dataToSign = sha256(sha256(outerZipFile.read(INNER_ZIP_FILENAME)) +
                      sha256(outerZipFile.read(PROPERTIES_FILENAME)))
         signature = outerZipFile.read(SIGNATURE_FILENAME)
               
      if dataToSign and signature:
         """
         Signature file contains multiple lines, of the form "key=value\n"
         The last line is the hex-encoded signature, which is over the 
         source code + everything in the sig file up to the last line.
         The key-value lines may contain properties such as signature 
         validity times/expiration, contact info of author, etc.
         """
         dataToSignSBD = SecureBinaryData(dataToSign)
         sigSBD = SecureBinaryData(hex_to_binary(signature.strip()))
         publicKeySBD = SecureBinaryData(hex_to_binary(ARMORY_INFO_SIGN_PUBLICKEY))
         result = MODULE_ZIP_STATUS.Valid if CryptoECDSA().VerifyData(dataToSignSBD, sigSBD, publicKeySBD) else \
                  MODULE_ZIP_STATUS.Unsigned
   except:
      # if anything goes wrong an invalid zip file indicator will get returned 
      pass
   return result

# TODO - Write this method - currently this just a place holder
#   with comments on how to implement the required functionality
def signZipFile(zipFilePath, propertiesDictionary=None):
   if propertiesDictionary:
      # Create an empty properties file
      pass
   # if it's a string treat it like a file name and open it
   # else if ti's a dictionary save it to a file and use that.
   
   # Read the contents of the Zip File and the properties file
   zipFileData = None
   propertiesFileData = None
   dataToSign = sha256(sha256(zipFileData) + sha256(propertiesFileData))
   dataToSignSBD = SecureBinaryData(dataToSign)
   # get the privKeySBD
   privKeySBD = None
   signature = CryptoECDSA().SignData(dataToSignSBD, privKeySBD, ENABLE_DETSIGN)
   # Write the Signature to signature.txt
   # rename the source Zip file to inner.zip
   # Create a new Zip File with the original name of the source zip file
   # add to the zip file  inner.zip, properties.txt, and signature.txt


def getModuleList(zipDir):
   moduleMap = {}
   if os.path.exists(zipDir):
      for fileName in os.listdir(zipDir):
         if fileName.endswith(ZIP_EXTENSION):
            try:
               moduleName = fileName.split('.')[0]
               if not moduleName in moduleMap:
                  moduleMap[moduleName] = {}
               moduleZipPath = os.path.join(zipDir, fileName)

               moduleMap[moduleName][MODULE_ZIP_STATUS_KEY] = verifyZipSignature(moduleZipPath)
               moduleMap[moduleName][MODULE_PATH_KEY] = moduleZipPath

            except:
               moduleMap[moduleName][MODULE_PATH_KEY] = MODULE_ZIP_STATUS.Invalid
               LOGEXCEPT('Exception while loading plugin %s.' % moduleName)
   return moduleMap
      

def importModule(modulesDir, moduleName, injectLocals=None):
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

   pluginPath = os.path.join(modulesDir, moduleName+'.py')  
   if not os.path.exists(pluginPath):
      return None

   # Join using a character that would be invalid in a pathname
   prevSysPath = '\x00'.join(sys.path)
   sys.path.append(modulesDir)


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

############################################################################
def getModuleListNoZip(inDir):
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
      

############################################################################
def dynamicImportNoZip(inDir, moduleName, injectLocals=None):
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
   