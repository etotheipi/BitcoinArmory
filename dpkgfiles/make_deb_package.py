#! /usr/bin/python

import os
import shutil
import platform
import time
import argparse
import glob
from hashlib import sha256
from subprocess import Popen, PIPE

def execAndWait(cli_str):
   print '*** Executing:', cli_str[:60], '...'
   process = Popen(cli_str, shell=True, stdout=PIPE)
   result = process.communicate()[0]
   retval = process.returncode
   print '*** Finished executing'
   return (result, retval)
   

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

def sha256sum(fname):
    f = open(fname, 'rb')
    with f:
        return '%s' % sha256(f.read()).hexdigest()

def getDepends(deb):
    exclusions = '--no-recommends --no-suggests --no-conflicts --no-breaks --no-replaces --no-enhances --no-pre-depends'
    depends, retval = execAndWait('apt-cache -c etc/apt.conf depends --recurse %s %s | grep Depends | awk \'{print $2}\'' % (exclusions, deb))
    depends = depends.split('\n')
    # return list of non-virtual packages
    return [x for x in depends if x and not x[0] == '<']

def getDefaultPackages():
    desktopPackages = getDepends('ubuntu-desktop')
    # need to read suite from sources.list instead of hardcoding precise
    basePackages, retval = execAndWait('debootstrap --print-debs precise temp.tar.gz 2>/dev/null')
    basePackages = basePackages.split(' ')
    return desktopPackages + basePackages



parser = argparse.ArgumentParser()
parser.add_argument('--chroot', type=str, default='base-reproducible.cow',
        help='name of chroot (including .cow) (defaults base-reproducible.cow)')
parser.add_argument('--bitness', type=int, default=64, help='32-bit or 64-bit'
        + '(32 or 64) (defaults 64)')
parser.add_argument('--static', action='store_true', help='boolean for static'
        + ' build (defaults false)')
parser.add_argument('--depends', action='store_true', help='boolean for whether'
        + ' to include prebuilt dependency deb packages or not (defaults false)')
parser.add_argument('--build-depends', action='store_true', help='boolean for'
        + ' whether to build dependencies or not (defaults false)')
args = parser.parse_args()

arch = {32: 'i386', 64: 'amd64'}[args.bitness]

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
osBits = args.bitness
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
shutil.copytree(origDir, pkgdir, ignore=shutil.ignore_patterns('depends'))

faketimePath = find('libfaketime.so.1', '/usr/lib')
faketimeVars = 'export LD_PRELOAD=%s; export FAKETIME="2013-06-01 00:00:00";' % faketimePath

execAndWait('%s tar -zcf %s.tar.gz %s' % (faketimeVars, pkgdir, pkgdir))
cd(pkgdir)
# piping yes into dh_make causes us to automatically move past the prompt
# to verify that the data is what we expect it to be
execAndWait('%s export DEBFULLNAME="Armory Technologies, Inc."; yes | dh_make -s -e support@bitcoinarmory.com -f ../%s.tar.gz' % (faketimeVars, pkgdir))
for f in dpkgfiles:
   execAndWait('%s cp dpkgfiles/%s debian/%s' % (faketimeVars, f, f))

# Finally, all the magic happens here
execAndWait('%s pdebuild --pbuilder cowbuilder --use-pdebuild-internal --architecture %s --buildresult ../armory-build -- --basepath /var/cache/pbuilder/%s' % (faketimeVars, arch, args.chroot))

# Download deb packages of dependencies for offline bundle
if args.depends:
    cd('dpkgfiles')
    execAndWait('mkdir packages')
    cd('packages')
    # apt/dpkg require a lot of specific directories/files to function
    execAndWait('mkdir parts')
    execAndWait('mkdir -p var/lib/apt/lists/partial')
    execAndWait('mkdir -p var/cache/apt/archives/partial')
    execAndWait('mkdir -p var/lib/dpkg')
    execAndWait('touch var/lib/dpkg/status')
    # remove any debs left over from last time, because this is just our
    # temporary working directory
    execAndWait('rm -f *.deb')

    depends = ['swig', 'libqtcore4', 'python-qt4', 'python-twisted',
            'python-psutil']
    result, retval = execAndWait('apt-get -c etc/apt.conf update')
    if retval != 0:
       print 'apt-get update returned error %d' % retval
       exit(1)
    recursiveDepends = []
    for deb in depends:
       recursiveDepends += getDepends(deb)
    defaultPackages = getDefaultPackages()
    recursiveDepends = [x for x in recursiveDepends if x not in defaultPackages]
    # Ensure recursiveDepends only has each package once
    recursiveDepends = list(set(recursiveDepends))
    for deb in recursiveDepends:
        result, retval = execAndWait('apt-get -c etc/apt.conf download %s:%s' % (deb, arch))
        if retval != 0:
           print 'apt-get download returned error %d' % retval
           exit(1)
    
    print 'All dependency debs were downloaded'
    packageDir = pwd()
    cd('../../..')
    execAndWait('mkdir armory-offline-debs')
    cd('armory-offline-debs')
    # clear out all packages except for those of the arch we aren't building
    # because we will be copying over those that are all and those that are
    # of the arch we are building
    execAndWait('rm -f *{all,%s}.deb' % arch)
    for f in glob.glob(os.path.join(packageDir, '*.deb')):
       shutil.copy(f, '.')
    cd('..')
    execAndWait('rm -rf OfflineBundle')
    execAndWait('mkdir OfflineBundle')
    execAndWait('cp armory-build/armory-build %s-1_%s.deb OfflineBundle' % (pkgdir_, arch))
    # we just want to copy over the all packages and those for the arch we
    # are building
    execAndWait('cp armory-offline-debs/*{all,%s}.deb OfflineBundle' % arch)
    execAndWait('tar -zcvf %s_offline_ubuntu-%s.tar.gz OfflineBundle' % (pkgdir_, args.bitness))

# Build dependencies from source
if args.build_depends:
    # Build all the dependencies
    cd('..')
    execAndWait('mkdir armory-build-depends')
    cd('armory-build-depends')
    twistedURL = 'http://archive.ubuntu.com/ubuntu/pool/main/t/twisted/twisted_13.2.0-1ubuntu1.dsc'
    pythonQt4URL = 'http://archive.ubuntu.com/ubuntu/pool/main/p/python-qt4/python-qt4_4.11.2+dfsg-1.dsc'
    sip4URL = 'http://archive.ubuntu.com/ubuntu/pool/main/s/sip4/sip4_4.16.3+dfsg-1.dsc'
    pyasn1URL = 'http://archive.ubuntu.com/ubuntu/pool/main/p/pyasn1/pyasn1_0.1.7-1ubuntu2.dsc'
    qt4X11URL = 'http://archive.ubuntu.com/ubuntu/pool/main/q/qt4-x11/qt4-x11_4.8.6+git49-gbc62005+dfsg-1ubuntu1.dsc'
    pythonPsutilURL = 'http://archive.ubuntu.com/ubuntu/pool/main/p/python-psutil/python-psutil_2.1.1-1.dsc'
    dpkgSigURL = 'http://archive.ubuntu.com/ubuntu/pool/universe/d/dpkg-sig/dpkg-sig_0.13.1+nmu2.dsc'
    qtAssistantCompatURL = 'http://archive.ubuntu.com/ubuntu/pool/main/q/qt-assistant-compat/qt-assistant-compat_4.6.3-6.dsc'
    qtwebkitSourceURL = 'http://archive.ubuntu.com/ubuntu/pool/main/q/qtwebkit-source/qtwebkit-source_2.3.2-0ubuntu7.dsc'
    depends = [
            twistedURL, pythonQt4URL, sip4URL, pyasn1URL, qt4X11URL,
            pythonPsutilURL, dpkgSigURL, qtAssistantCompatURL, qtwebkitSourceURL
            ]
    for url in depends:
        execAndWait('dget -x ' + url)
    for d in dir()[1]:
        cd(d)
        execAndWait('pdebuild --pbuilder cowbuilder --use-pdebuild-internal --buildresult .. -- --basepath /var/cache/pbuilder/%s' % args.chroot)
        cd('..')
