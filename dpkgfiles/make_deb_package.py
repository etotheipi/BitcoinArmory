#! /usr/bin/python

import os
import shutil
import platform
import time
import argparse
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

# http://stackoverflow.com/questions/1724693/find-a-file-in-python
def find(name, path):
   for root, dirs, files in os.walk(path):
      if name in files:
         return os.path.join(root, name)



parser = argparse.ArgumentParser()
parser.add_argument('chroot', help='name of chroot (including .cow)')
parser.add_argument('static', type=int, help='boolean for static build (0 or 1)')
parser.add_argument('build_depends', metavar='build-depends', type=int, help='boolean for whether to'
        + 'build dependencies or not (0 or 1)')
args = parser.parse_args()

if pwd().split('/')[-1]=='dpkgfiles':
   cd('..')

if not os.path.exists('./armoryengine/ArmoryUtils.py') or \
   not os.path.exists('./ArmoryQt.py'):
   print '***ERROR: Must run this script from the root Armory directory!'
   exit(1)

# Must get current Armory version from armoryengine.py
# I desperately need a better way to store/read/increment version numbers
vstr = ''
with open('armoryengine/ArmoryUtils.py') as f:
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
pkgdir_ = 'armory_%s' % (vstr,)

if not vstr:
   print '***ERROR: Could not deduce version from ArmoryUtils.py. '
   print '          There is no good reason for this to happen.  Ever! :('
   exit(1)

# Copy the correct control file (for 32-bit or 64-bit OS)
osBits = platform.architecture()[0][:2]
staticStr = ''
if args.static:
   staticStr = 'static'
shutil.copy('dpkgfiles/control%s' % (osBits), 'dpkgfiles/control')

# Copy the correct rules file (for static or non-static build)
shutil.copy('dpkgfiles/rules%s.template' % (staticStr), 'dpkgfiles/rules')

dpkgfiles = ['control', 'copyright', 'postinst', 'postrm', 'rules']


# Start pseudo-bash-script
origDir = pwd().split('/')[-1]
execAndWait('python update_version.py')
execAndWait('make clean')
cd('..')
execAndWait('rm -rf %s' % pkgdir)
execAndWait('rm -f %s*' % pkgdir)
execAndWait('rm -f %s*' % pkgdir_)
shutil.copytree(origDir, pkgdir)

faketimePath = find('libfaketime.so.1', '/usr/lib')
faketimeVars = 'export LD_PRELOAD=%s; export FAKETIME="2013-06-01 00:00:00";' % faketimePath

execAndWait('%s tar -zcf %s.tar.gz %s' % (faketimeVars, pkgdir, pkgdir))
cd(pkgdir)
execAndWait('%s export DEBFULLNAME="Armory Technologies, Inc."; dh_make -s -e support@bitcoinarmory.com -f ../%s.tar.gz' % (faketimeVars, pkgdir))
for f in dpkgfiles:
   execAndWait('%s cp dpkgfiles/%s debian/%s' % (faketimeVars, f, f))

# Finally, all the magic happens here
execAndWait('%s pdebuild --pbuilder cowbuilder --use-pdebuild-internal --buildresult ../armory-build -- --basepath /var/cache/pbuilder/%s' % (faketimeVars, args.chroot))
if args.build_depends:
    # Build all the dependencies
    cd('..')
    execAndWait('mkdir armory-build-depends')
    cd('armory-build-depends')
    depends = ['http://archive.ubuntu.com/ubuntu/pool/main/t/twisted/twisted_13.2.0-1ubuntu1.dsc', 'http://archive.ubuntu.com/ubuntu/pool/main/p/python-qt4/python-qt4_4.11.2+dfsg-1.dsc', 'http://archive.ubuntu.com/ubuntu/pool/main/s/sip4/sip4_4.16.3+dfsg-1.dsc', 'http://archive.ubuntu.com/ubuntu/pool/main/p/pyasn1/pyasn1_0.1.7-1ubuntu2.dsc', 'http://archive.ubuntu.com/ubuntu/pool/main/q/qt4-x11/qt4-x11_4.8.6+git49-gbc62005+dfsg-1ubuntu1.dsc', 'http://archive.ubuntu.com/ubuntu/pool/main/p/python-psutil/python-psutil_2.1.1-1.dsc', 'http://archive.ubuntu.com/ubuntu/pool/universe/d/dpkg-sig/dpkg-sig_0.13.1+nmu2.dsc', 'http://archive.ubuntu.com/ubuntu/pool/main/q/qt-assistant-compat/qt-assistant-compat_4.6.3-6.dsc', 'http://archive.ubuntu.com/ubuntu/pool/main/q/qtwebkit-source/qtwebkit-source_2.3.2-0ubuntu7.dsc']
    for url in depends:
        execAndWait('dget -x ' + url)
    for d in dir()[1]:
        cd(d)
        execAndWait('pdebuild --pbuilder cowbuilder --use-pdebuild-internal --buildresult .. -- --basepath /var/cache/pbuilder/%s' % args.chroot)
        cd('..')
