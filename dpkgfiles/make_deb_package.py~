#! /usr/bin/python

import os
import shutil
import platform
import time
from subprocess import Popen, PIPE

def execAndWait(cli_str):
   print '*** Executing:', cli_str[:60], '...'
   process = Popen(cli_str, shell=True)
   while process.poll() == None:
      time.sleep(0.5)
   print '*** Finished executing'
   

def dir(path='.'):
   allpaths = os.listdir(path)
   fileList = filter(lambda a: os.path.isfile(a), allpaths)
   dirList  = filter(lambda a: os.path.isdir(a), allpaths)
   return [fileList, dirList]

def cd(path):
   os.chdir(path)

def pwd():
   return os.getcwd()



if pwd().split('/')[-1]=='dpkgfiles':
   cd('..')

if not os.path.exists('./armoryengine.py') or \
   not os.path.exists('./ArmoryQt.py'):
   print '***ERROR: Must run this script from the root Armory directory!'
   exit(1)


# Must get current Armory version from armoryengine.py
# I desperately need a better way to store/read/increment version numbers
vstr = ''
with open('armoryengine.py') as f:
   for line in f.readlines():
      if line.startswith('BTCARMORY_VERSION'):
         vstr = line[line.index('(')+1:line.index(')')]
         vquad = tuple([int(v) for v in vstr.replace(' ','').split(',')])
         print vquad, len(vquad)
         vstr = '%d.%02d' % vquad[:2]
         if (vquad[2] > 0 or vquad[3] > 0):
            vstr += '.%d' % vquad[2]
         if vquad[3] > 0:
            vstr += '.%d' % vquad[3]
         break


pkgdir = 'armory-%s' % (vstr,)

if not vstr:
   print '***ERROR: Could not deduce version from armoryengine.py. '
   print '          There is no good reason for this to happen.  Ever! :('
   exit(1)

# Copy the correct control file (for 32-bit or 64-bit OS)
osBits = platform.architecture()[0][:2]
shutil.copy('dpkgfiles/control%s' % (osBits), 'dpkgfiles/control')
dpkgfiles = ['control', 'copyright', 'postinst', 'postrm']


# Start pseudo-bash-script
origDir = pwd().split('/')[-1]
execAndWait('make clean')
cd('..')
execAndWait('rm -rf %s' % pkgdir)
execAndWait('rm -f %s*' % pkgdir)
shutil.copytree(origDir, pkgdir)
execAndWait('tar -zcf %s.tar.gz %s' % (pkgdir, pkgdir))
cd(pkgdir)
execAndWait('export DEBFULLNAME="Alan C. Reiner"; dh_make -s -e alan.reiner@gmail.com -f ../%s.tar.gz' % pkgdir)
for f in dpkgfiles:
   shutil.copy('dpkgfiles/%s' % f, 'debian/%s' % f)

# Finally, all the magic happens here
execAndWait('dpkg-buildpackage -rfakeroot')







