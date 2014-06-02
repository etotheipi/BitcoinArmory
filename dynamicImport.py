import os


def getModuleList(inDir):
   moduleMap = {}
   if not os.path.exists(inDir):
      return moduleMap

   
   for fn in os.listdir(inDir):
      if not fn.endswith('.py') and not fn.endswith('.sig'):
         continue

      modName = os.path.splitext(fn)[0]
      fullfn = os.path.join(inDir, fn)
      with open(fullfn, 'r') as f:
         fileData = f.read()

      if not modName in moduleMap:
         moduleMap[modName] = {}
      
      
