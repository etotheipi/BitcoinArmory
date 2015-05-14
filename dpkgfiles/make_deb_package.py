#! /usr/bin/python

import os
import shutil
import platform
import time
import argparse
from hashlib import sha256
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

def sha256sum(fname):
    f = open(fname, 'rb')
    with f:
        return '%s' % sha256(f.read()).hexdigest()



parser = argparse.ArgumentParser()
parser.add_argument('chroot', help='name of chroot (including .cow)')
parser.add_argument('bitness', type=int, help='32-bit or 64-bit (32 or 64)')
parser.add_argument('static', type=int, help='boolean for static build (0 or 1)')
parser.add_argument('depends', type=int, help='boolean for whether to include'
        + 'prebuilt dependency deb packages or not (0 or 1)')
parser.add_argument('build_depends', metavar='build-depends', type=int, help='boolean for whether to'
        + 'build dependencies or not (0 or 1)')
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
shutil.copytree(origDir, pkgdir)

faketimePath = find('libfaketime.so.1', '/usr/lib')
faketimeVars = 'export LD_PRELOAD=%s; export FAKETIME="2013-06-01 00:00:00";' % faketimePath

execAndWait('%s tar -zcf %s.tar.gz %s' % (faketimeVars, pkgdir, pkgdir))
cd(pkgdir)
execAndWait('%s export DEBFULLNAME="Armory Technologies, Inc."; dh_make -s -e support@bitcoinarmory.com -f ../%s.tar.gz' % (faketimeVars, pkgdir))
for f in dpkgfiles:
   execAndWait('%s cp dpkgfiles/%s debian/%s' % (faketimeVars, f, f))

# Finally, all the magic happens here
execAndWait('%s pdebuild --pbuilder cowbuilder --use-pdebuild-internal --architecture %s --buildresult ../armory-build -- --basepath /var/cache/pbuilder/%s' % (faketimeVars, arch, args.chroot))

# Download deb packages of dependencies for offline bundle
if args.depends:
    cd('..')
    execAndWait('mkdir armory-offline-debs')
    cd('armory-offline-debs')
    libqt4Designer = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/q/qt4-x11/libqt4-designer_4.8.1-0ubuntu4.8_%s.deb' % arch,
            'sha256sumamd64': '6bcfdd045a042ca67598da09b149f8a538da06f988b253ee8ad77ebb2c25c684',
            'sha256sumi386': '3187602fe2caffe8b99ec25afea31e3124fb0b673776e2c6fc7ecf34a9472550'
    }
    libqt4Help = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/q/qt4-x11/libqt4-help_4.8.1-0ubuntu4.8_%s.deb' % arch,
            'sha256sumamd64': '0750806746c700214aa0ec9919e54a3e79040b1ba69dcffd9ddf064fd8d7896b',
            'sha256sumi386': '2f62648fe1b6e7598c45cfb937eb732e3d8c9fade9515a3bc774971c212b0e93'
    }
    libqt4Scripttools = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/q/qt4-x11/libqt4-scripttools_4.8.1-0ubuntu4.8_%s.deb' % arch,
            'sha256sumamd64': 'a2f7979ed82127074f23097969396e77e27d078ceb2ded9f04f2f643d4569a4e',
            'sha256sumi386': 'c3e5745afa9a11689498782f77b7e7a60989edced28120ee63822c246ffe6b72'
    }
    libqt4Test = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/q/qt4-x11/libqt4-test_4.8.1-0ubuntu4.8_%s.deb' % arch,
            'sha256sumamd64': '28a2c091958c674045d5a0db0be2517e272b70ee597b08ad7d00e442e7052653',
            'sha256sumi386': '9b9af35d6f2cf0c7a83bff7e509b5451aa6764be23a5679f7ddbd8cd31f90986'
    }
    libqtassistantclient4 = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/q/qt-assistant-compat/libqtassistantclient4_4.6.3-3ubuntu2_%s.deb' % arch,
            'sha256sumamd64': '7eefa219cf83ab2eaa2feb84c25a29b9708aa461a7cea581b14a7a1a20d243b4',
            'sha256sumi386': 'dc7e4828bb4468ebf8694acf886c63a253be65bf65df07fd507fe5bb6a040953'
    }
    libqtwebkit4 = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/q/qtwebkit-source/libqtwebkit4_2.2.1-1ubuntu4_%s.deb' % arch,
            'sha256sumamd64': 'f34556c72a69cbd5b9153b8a74cecdafa43029d916fb64504783fdef8b8a7e83',
            'sha256sumi386': '288a47e75800969c28bdcd384821985c3d105ac61a912199125b1400d9f383e0'
    }
    pythonPsutil = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/universe/p/python-psutil/python-psutil_0.4.1-1ubuntu1_%s.deb' % arch,
            'sha256sumamd64': '73c2534493ce3aa366d93a70b1758b5f39325f63057b0085135f102c3520b194',
            'sha256sumi386': 'aa32bc47812e58b74477242fe87a4156c3f7a71d72a4b88a93e437a951f8d085'
    }
    pythonPyasn1 = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/p/pyasn1/python-pyasn1_0.0.11a-1ubuntu1_all.deb',
            'sha256sumamd64': '89cf843ccce0845b69716f8612422af8b4e566d128c407031cb0560f237f5dc8',
            'sha256sumi386': '89cf843ccce0845b69716f8612422af8b4e566d128c407031cb0560f237f5dc8'
    }
    pythonQt4 = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/p/python-qt4/python-qt4_4.9.1-2ubuntu1_%s.deb' % arch,
            'sha256sumamd64': '0c828a4a9da29f2dd7954af47dc2376075a28eb6179c644bd6f59cc85317109e',
            'sha256sumi386': 'b764bed5f987c9512a38569838876be8d1b46a91c487b56f075a049c147b7de2'
    }
    pythonSip = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/s/sip4/python-sip_4.13.2-1_%s.deb' % arch,
            'sha256sumamd64': '76d8184c8e2ed97f1520cc9478c80143b603bcefd7b538652b784ab02dbd4b07',
            'sha256sumi386': '4051a770745e18953a993409eedb23b8cce2d1cba67105e52da1717f4dd533fc'
    }
    pythonTwisted = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/t/twisted/python-twisted_11.1.0-1ubuntu2_all.deb',
            'sha256sumamd64': '680b6e4b5d1267c8d055c845129c379f9ab47f1c5e0d589266b5432317c627c7',
            'sha256sumi386': '680b6e4b5d1267c8d055c845129c379f9ab47f1c5e0d589266b5432317c627c7'
    }
    pythonTwistedConch = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/t/twisted-conch/python-twisted-conch_11.1.0-1_all.deb',
            'sha256sumamd64': '222edf6328c8a6de721a47e1743f0a552dc18b582ffb5592e35a46c1b92a301e',
            'sha256sumi386': '222edf6328c8a6de721a47e1743f0a552dc18b582ffb5592e35a46c1b92a301e'
    }
    pythonTwistedLore = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/t/twisted-lore/python-twisted-lore_11.1.0-1_all.deb',
            'sha256sumamd64': '1a6412eb813f1043df25a29ac586385baa672b8b8d0b2d1463c76ae85ee3a7f3',
            'sha256sumi386': '1a6412eb813f1043df25a29ac586385baa672b8b8d0b2d1463c76ae85ee3a7f3'
    }
    pythonTwistedMail = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/t/twisted-mail/python-twisted-mail_11.1.0-1_all.deb',
            'sha256sumamd64': '9ec78d0a31f1e7a6abb0b768da4cb17b7488e9213d682dc49da63f101783fb21',
            'sha256sumi386': '9ec78d0a31f1e7a6abb0b768da4cb17b7488e9213d682dc49da63f101783fb21'
    }
    pythonTwistedNews = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/t/twisted-news/python-twisted-news_11.1.0-1_all.deb',
            'sha256sumamd64': '1f54c0051aeb62941d156a739c7d72ac824c64121da57148aba25f5eac4520b7',
            'sha256sumi386': '1f54c0051aeb62941d156a739c7d72ac824c64121da57148aba25f5eac4520b7'
    }
    pythonTwistedRunner = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/t/twisted-runner/python-twisted-runner_11.1.0-1_%s.deb' % arch,
            'sha256sumamd64': '7ccdb539b0a9b7b7f0d50c4c64ba253d7b3f93a96404d1f2c445d8d2057916f7',
            'sha256sumi386': '7ccdb539b0a9b7b7f0d50c4c64ba253d7b3f93a96404d1f2c445d8d2057916f7'
    }
    pythonTwistedWords = {
            'url': 'http://mirrors.kernel.org/ubuntu/pool/main/t/twisted-words/python-twisted-words_11.1.0-1_all.deb',
            'sha256sumamd64': 'e6a740c4937db0940e109636c773d8dc2049faaa856001480a501c1fcca7d8c8',
            'sha256sumi386': 'e6a740c4937db0940e109636c773d8dc2049faaa856001480a501c1fcca7d8c8'
    }
    depends = [libqt4Designer, libqt4Help, libqt4Scripttools, libqt4Test,
            libqtassistantclient4, libqtwebkit4, pythonPsutil, pythonPyasn1,
            pythonQt4, pythonSip, pythonTwisted, pythonTwistedConch,
            pythonTwistedLore, pythonTwistedMail, pythonTwistedNews,
            pythonTwistedRunner, pythonTwistedWords]
    for deb in depends:
        fname = deb['url'].rsplit('/', 1)[1]
        execAndWait('rm %s' % fname)
        execAndWait('wget %s' % deb['url'])
        if sha256sum(fname) == deb['sha256sum%s' % arch]:
            print '%s was downloaded and verified successfully' % fname
        else:
            execAndWait('rm %s' % fname)
            print '%s was not verified successfully' % fname
            print 'Exiting due to verification error'
            exit(1)
    print 'All dependency debs were successfully downloaded and verified'
    cd('..')
    execAndWait('mkdir OfflineBundle')
    execAndWait('cp armory-build/armory-build %s-1_%s.deb OfflineBundle' % (pkgdir_, arch))
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
