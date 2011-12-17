from armoryengine import *
import CppBlockUtils as Cpp
import armoryengine 

print 'Loading wallets...'
wltPaths = []
for f in os.listdir(ARMORY_HOME_DIR):
   fullPath = os.path.join(ARMORY_HOME_DIR, f)
   if os.path.isfile(fullPath) and not fullPath.endswith('backup.wallet'):
      openfile = open(fullPath, 'r')
      first8 = openfile.read(8) 
      openfile.close()
      if first8=='\xbaWALLET\x00':
         wltPaths.append(fullPath)

for fpath in wltPaths:
   wltLoad = PyBtcWallet().readWalletFile(fpath)
   wltID = wltLoad.wltUniqueIDB58
   print 'Read wallet:', wltID, 'version:', wltLoad.version
   oldPath = wltLoad.walletPath
   print 'Will upgrade version to:', oldPath, PYBTCWALLET_VERSION

   fileparts = os.path.splitext(oldPath)
   oldBackup = fileparts[0] + 'backup' + fileparts[1]
   tempPath = oldPath + '.new_version'

   print 'Forking wallet...'
   wltLoad.version = PYBTCWALLET_VERSION
   wltLoad.writeFreshWalletFile(tempPath)

   os.remove(oldPath)
   os.remove(oldBackup)
   shutil.move(tempPath, oldPath)






