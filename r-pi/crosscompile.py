# Armory -- Bitcoin Wallet Software
# Copyright (c) 2016, goatpig <moothecowlord@gmail.com>
# Originally written by Alan Reiner  (etotheipi@gmail.com)

import os
import shutil
import subprocess
import time
from sys import argv

CROSSCOMPILEPATH  = 'r-pi/RPI_CROSSCOMPILE'
TOOLS_PATH  = os.path.join(CROSSCOMPILEPATH, 'tools')
PYROOT_PATH = os.path.join(CROSSCOMPILEPATH, 'pyroot')
RPI_REPO    = 'git://github.com/raspberrypi/tools.git'

# The following two files were valid as of Aug. 30, 2016.  You might need to
# update the links below by going to the base FTP dir and looking for the
# latest version numbers to update the links below.  You can view the
# directory listing in your browser:
#
#    https://archive.raspbian.org/raspbian/pool/main/p/python2.7/
#
PY_ARMHF1   = 'https://archive.raspbian.org/raspbian/pool/main/p/python2.7/libpython2.7-dev_2.7.12-2_armhf.deb'
PY_ARMHF2   = 'https://archive.raspbian.org/raspbian/pool/main/p/python2.7/libpython2.7-minimal_2.7.12-2_armhf.deb'

if len(argv)==1 and not os.path.exists(TOOLS_PATH):
   print """ERROR: Must supply "setupcrosscompiler" or path to where it is setup.
   Use one of the following:  

   python %s setupcrosscompiler [setuppath]
   python %s [setuppath]

   If not specified, setuppath is: %s""" % (argv[0], argv[0], TOOLS_PATH)
   exit(1)

SetupPath = TOOLS_PATH
if len(argv)==1:
   DoSetup = False
else:
   DoSetup = argv[1]=='setupcrosscompiler'

if (DoSetup and len(argv)>2) or (not DoSetup and len(argv)>1):
   SetupPath = argv[-1]


def popen(cmdList, cwd=None):
   print '*'*80
   print 'Executing: "%s"' % ' '.join(cmdList)
   if cwd:
      print '         : CWD="%s"'  % cwd
   proc = subprocess.Popen(cmdList, cwd=cwd)
   while proc.poll() is None:
      time.sleep(1)
   print 'Done with: "%s"' % ' '.join(cmdList)
   print '*'*80


if DoSetup:
   if os.path.exists(CROSSCOMPILEPATH):
      shutil.rmtree(CROSSCOMPILEPATH)
   os.makedirs(CROSSCOMPILEPATH)
   os.makedirs(TOOLS_PATH)
   os.makedirs(PYROOT_PATH)

   popen(['git','clone', RPI_REPO], cwd=CROSSCOMPILEPATH)
   popen(['wget', PY_ARMHF1], cwd=PYROOT_PATH)
   popen(['wget', PY_ARMHF2], cwd=PYROOT_PATH)

   deb1 = os.path.join(PYROOT_PATH, os.path.basename(PY_ARMHF1))
   deb2 = os.path.join(PYROOT_PATH, os.path.basename(PY_ARMHF2))
   popen(['dpkg-deb', '-x', deb1, PYROOT_PATH])
   popen(['dpkg-deb', '-x', deb2, PYROOT_PATH])

   exit(0)


verStr = ''
for line in open('armoryengine/ArmoryUtils.py','r').readlines():
   if line.startswith('BTCARMORY_VERSION'):
      c0 = line.find('(')+1
      c1 = line.find(')')
      vquad = [int(istr.strip()) for istr in line[c0:c1].split(',')]
      verStr = '%d.%02d' % tuple(vquad[:2])
      if (vquad[2] > 0 or vquad[3] > 0):
         verStr += '.%d' % vquad[2]
      if vquad[3] > 0:
         verStr += '.%d' % vquad[3]
      break

print 'Armory version:', verStr 
instDir = 'armory_%s_raspbian-armhf' % verStr
targz   = '../' + instDir + '.tar.gz'
if os.path.exists(instDir):
   shutil.rmtree(instDir)
os.makedirs(instDir)

ccbin = 'arm-bcm2708/gcc-linaro-arm-linux-gnueabihf-raspbian-x64/bin/'
cxx  = os.path.abspath(os.path.join(TOOLS_PATH,  ccbin, 'arm-linux-gnueabihf-g++'))
cc   = os.path.abspath(os.path.join(TOOLS_PATH,  ccbin, 'arm-linux-gnueabihf-gcc'))
inc1 = os.path.abspath(os.path.join(PYROOT_PATH, 'usr/include'))
inc2 = os.path.abspath(os.path.join(PYROOT_PATH, 'usr/include/python2.7'))
lib  = os.path.abspath(os.path.join(PYROOT_PATH, 'usr/lib/python2.7/config-arm-linux-gnueabihf'))

print 'Cross-compiler Root:', CROSSCOMPILEPATH
print '   CXX:', cxx
print '   CC: ', cc
print '   INC:', inc1
print '   INC:', inc2
print '   LIB:', lib

popen(['make', 'clean'])
popen(['python', 'update_version.py'])
popen(['make', 'CXX='+cxx, 
               'CC='+cc, 
               'PYVER=python2.7', 
               'PYTHON_INCLUDES=-I%s -I%s' % (inc1,inc2), 
               'PYTHON_LIB=-L'+lib, 
               'STATIC_LINK=1'])

popen(['make', 'install', 'DESTDIR=%s'%instDir])
popen(['tar','-zcf', targz, 'usr'], cwd=instDir)
