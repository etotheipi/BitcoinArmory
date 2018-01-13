#!/usr/bin/env python
"""Build Armory as a Mac OS X Application."""

import os
from os import path
import sys
import hashlib
import shutil
import glob
import time
import datetime
import optparse
import tarfile
import subprocess
import zipfile

from subprocess import Popen, PIPE
from tempfile import mkstemp

# Set some constants up front
minOSXVer     = '10.8'
pythonVer     = '2.7.14' # NB: ArmoryMac.pro must also be kept up to date!!!
pyMajorVer    = '2.7'
setToolVer    = '38.2.3'
setToolSubdir = '41/80/268fda78a53c2629128f8174d2952c7f902c93ebaa2062b64f27aa101b07'
pipVer        = '9.0.1'
pipSubdir     = '11/b6/abcb525026a4be042b486df43905d6893fb04f05aac21c32c638e939e447'
psutilVer     = '5.4.1'
psutilSubdir  = 'fe/17/0f0bf5792b2dfe6003efc5175c76225f7d3426f88e2bf8d360cfab870cd8'
libpngVer     = '1.6.34'
qtVer         = '4.8.7'  # NB: ArmoryMac.pro must also be kept up to date!!!
                         # Possibly "sipFlags" below too.
sipVer        = '4.19.6' # NB: ArmoryMac.pro must also be kept up to date!!!
pyQtVer       = '4.12.1' # NB: When I'm upgraded, SIP usually has to be upgraded too.

# Used only if compiling a version that supports armoryd
twistedVer    = '17.9.0'
twistedSubdir = 'a2/37/298f9547606c45d75aa9792369302cc63aa4bbcf7b5f607560180dd099d2'

# Various paths and build materials related to Armory.
LOGFILE        = 'build-app.log.txt'
LOGPATH        = path.abspath( path.join(os.getcwd(), LOGFILE))
OBJCDIR        = path.join(os.getcwd(), 'objc_armory')
WORKDIR        = path.join(os.getcwd(), 'workspace')
APPBASE        = path.join(WORKDIR, 'Armory.app') # actually make it local
WORKDLDIR      = path.join(WORKDIR, 'downloads')
WORKUNPACKDIR  = path.join(WORKDIR, 'unpackandbuild')
WORKINSTALLDIR = path.join(WORKDIR, 'install')
ARMORYCODEBASE = path.join(APPBASE, 'Contents/MacOS/py')
PYFRAMEBASE    = path.join(APPBASE, 'Contents/Frameworks/Python.framework/Versions/%s' % pyMajorVer)
PYLIBPREFIX    = path.join(PYFRAMEBASE, 'lib')
PYINCPREFIX    = path.join(PYFRAMEBASE, 'include/python%s' % pyMajorVer)
PYBINARY       = path.join(PYFRAMEBASE, 'Resources/Python.app/Contents/MacOS/Python')
PYSITEPKGS     = path.join(PYLIBPREFIX, 'python%s/site-packages' % pyMajorVer)
MAKEFLAGS      = '-j4'

# Autotools needs some TLC to make Python happy.
CONFIGFLAGS = '--with-macosx-version-min=%s LIBS=\"-L%s\" PYTHON=\"%s\" PYTHON_LDFLAGS=\"-L%s\" PYTHON_CPPFLAGS=\"-I%s\" PYTHON_EXTRA_LIBS=\"-u _PyMac_Error %s/Python\"' % (minOSXVer, PYLIBPREFIX, PYBINARY, PYLIBPREFIX, PYINCPREFIX, PYFRAMEBASE)

# Susceptible to build failures. Would fix, but prereqs are going away. Leave
# alone since it'll be gone soon anyway.
QTBUILTFLAG = path.join(WORKUNPACKDIR, 'qt/qt_install_success.txt')

# If no arguments specified, then do the minimal amount of work necessary
# Assume that only one flag is specified.  These should be
parser = optparse.OptionParser(usage="%prog [options]\n")
parser.add_option('--fromscratch',  dest='fromscratch', default=False, action='store_true', help='Remove all prev-downloaded: redownload and rebuild all')
parser.add_option('--rebuildall',   dest='rebuildall',  default=False, action='store_true', help='Remove all prev-built; no redownload, only rebuild')
parser.add_option('--compapponly',  dest='compapponly', default=False, action='store_true', help='Recompile Armory, not the 3rd party code')
parser.add_option('--armoryd',      dest='armoryd',     default=False, action='store_true', help='Add files to allow armoryd to run')
(CLIOPTS, CLIARGS) = parser.parse_args()

########################################################
# Write the string to both console and log file
def logprint(s):
   print s
   with open(LOGFILE,'a') as f:
      f.write(s if s.endswith('\n') else s+'\n')

# Even if it's already built, we'll always "make install" and then
# set a bunch of environment variables (WORKINSTALLDIR is wiped on every
# run of this script, so all "make install" steps need to be re-run).
# Variables placed out here to make compile-only option feasible.
# Qt5 may require QMAKESPEC to change.
try:
   oldDYLDPath = ':'+os.environ['DYLD_FRAMEWORK_PATH']
except KeyError:
   oldDYLDPath = ''
qtInstDir  = path.join(WORKINSTALLDIR, 'qt')
qtBinDir = path.join(qtInstDir, 'bin')
qtBuildDir = path.join(WORKUNPACKDIR, 'qt-everywhere-opensource-src-%s' % qtVer)
frmpath = path.join(APPBASE, 'Contents/Frameworks')
os.environ['PATH'] = '%s:%s' % (qtBinDir, os.environ['PATH'])
os.environ['DYLD_FRAMEWORK_PATH'] = '%s:%s' % (frmpath, oldDYLDPath)
os.environ['QTDIR'] = qtInstDir
os.environ['QMAKESPEC'] = path.join(os.environ['QTDIR'], 'mkspecs/unsupported/macx-clang-libc++')
logprint('All the following ENV vars are now set:')
for var in ['PATH','DYLD_FRAMEWORK_PATH', 'QTDIR', 'QMAKESPEC']:
   logprint('   %s: \n      %s' % (var, os.environ[var]))

# Build requires a "brew"ed OpenSSL. Need to get the header location.
opensslPath = subprocess.check_output(["brew", "--prefix", "openssl"]).rstrip('\n')
if opensslPath.startswith("Error"):
   print 'ERROR: You must use brew to install OpenSSL. Exiting build process.'
   sys.exit()

########################################################
# Now actually start the download&build process

# Make sure all the dirs exist
def main():

   if path.exists(LOGFILE):
      os.remove(LOGFILE)

   if not CLIOPTS.compapponly:
      delete_prereq_data(CLIOPTS)

   makedir(WORKDIR)
   makedir(WORKDLDIR)
   makedir(WORKUNPACKDIR)
   makedir(WORKINSTALLDIR)

   # Download Armory prerequisites
   for pkgname, fname, url, ID in distfiles:
      logprint('\n\n')
      downloadPkg(pkgname, fname, url, ID)
   logprint("\n\nALL DOWNLOADS COMPLETED.\n\n")

   if not os.path.isdir(APPBASE):
      make_empty_app()
      make_resources()

   if not CLIOPTS.compapponly:
      compile_python()
      compile_pip()
      compile_libpng()
      install_qt()
      compile_sip()
      compile_pyqt()
      compile_psutil()
      if CLIOPTS.armoryd:
         compile_twisted()

   compile_armory()
   compile_objc_library()
   cleanup_app()
   # Force Finder to update the Icon
   execAndWait("touch " + APPBASE)
   make_targz()

   # Show the final app size.
   show_app_size()

################################################################################
def getRightNowStr():
   dateFmt = '%Y-%b-%d %I:%M%p'
   dtobj = datetime.datetime.fromtimestamp(time.time())
   dtstr = u'' + dtobj.strftime(dateFmt).decode('utf-8')
   return dtstr[:-2] + dtstr[-2:].lower()

################################################################################
def execAndWait(syscmd, cwd=None):
   try:
      syscmd += ' 2>&1 | tee -a %s' % LOGPATH
      logprint('*'*80)
      logprint(getRightNowStr())
      logprint('Executing: "%s"' % syscmd)
      logprint('Executing from: "%s"' % (os.getcwd() if cwd is None else cwd))
      proc = Popen(syscmd, shell=True, cwd=cwd)
      while proc.poll() == None:
         time.sleep(0.25)
      logprint('Finished executing: "%s"' % syscmd)
      logprint('Finished executing from: "%s"' % (os.getcwd() if cwd is None else cwd))
      logprint('*'*80)
   except Exception as e:
      logprint('\n' + '-'*80)
      logprint('ERROR: %s' % str(e))
      logprint('-'*80 + '\n')

################################################################################
def makedir(dirname):
   if not path.isdir(dirname):
      logprint( "Creating directory: %s" % dirname)
      os.mkdir(dirname)

################################################################################
def movepath(pathname, newpath):
   if path.exists(pathname):
      logprint('Moving directory tree: \nFrom "%s"\nTo   "%s"' % (pathname, newpath))
      shutil.move(pathname, newpath)

################################################################################
def removetree(pathname):
   if path.exists(pathname):
      logprint('Removing directory tree: %s' % pathname)
      shutil.rmtree(pathname)

################################################################################
def removefile(pathname):
   if path.exists(pathname):
      logprint('Removing file: %s' % pathname)
      os.remove(pathname)

################################################################################
def copytree(pathname, newpath):
   if path.exists(pathname):
      logprint('Copying directory tree: \nFrom "%s"\nTo   "%s"' % (pathname, newpath))
      shutil.copytree(pathname, newpath)

################################################################################
def copyfile(src, dst):
   logprint('Copying file:  "%s" --> "%s"' % (src,dst))
   shutil.copy(src,dst)

################################################################################
def check_sha(filename, sha):
   logprint("Checking %s" % filename)
   check = hashlib.sha1()
   with open(filename,'rb') as f:
      check.update(f.read())
   digest = check.hexdigest()

   if sha is None:
      logprint("SHA-1 =", digest)
      return digest
   elif sha==digest:
      logprint("SHA-1 matches: OK")
      return True
   else:
      logprint("SHA-1 does not match!")
      return False

################################################################################
def getTarUnpackPath(tarName, inDir=None):
   """
   NOTE: THIS FUNCTION IS NOT RELIABLE.  It only works if the tar file would
         extract a single directory with all contents in that dir.  If it
         unpacks more than one file or directory, the output will be incomplete.
   """
   tarPath = tarName
   if inDir is not None:
      tarPath = path.join(inDir, tarName)

   # HACK 1: XZ support was added to tarfile.open() in Python 3.3. Can't use for
   # now, so we'll have to apply a hack to get around this. In addition, the
   # builder must have the xz binary on their build machine, otherwise the
   # following error will appear: "tar: Error opening archive: Child process
   # exited with status 254Child process exited with status 254"
   # HACK 2: AFAIK, it's not possible to peek inside ZIP files and get the
   # resultant directory. Just be lazy and hard-code it.
   if tarName == "Python-%s.tar.xz" % pythonVer:
      theDir = "Python-%s" % pythonVer
   elif tarName == "libpng-%s.tar.xz" % libpngVer:
      theDir = "libpng-%s" % libpngVer
   elif tarName == "setuptools-%s.zip" % setToolVer:
      theDir = "setuptools-%s" % setToolVer
   else:
      tar = tarfile.open(tarPath,'r')
      theDir = tar.next().name.split('/')[0]
      tar.close()
   return theDir

################################################################################
def unpack(tarName, fromDir=WORKDLDIR, toDir=WORKUNPACKDIR, overwrite=False):
   """
   This is not a versatile function. It expects tar or zip files with a single
   unpack directory. I will expand this function as necessary if we
   need tar/zip files that aren't a single bundled dir.
   """
   if fromDir is not None:
      tardl = path.join(fromDir, tarName)

   if not path.exists(toDir):
      os.mkdir(toDir)

   # Use tarfile module to pick out the base dir.
   extractPath = getTarUnpackPath(tarName, fromDir)
   extractPath = path.join(toDir, extractPath)
   if path.exists(extractPath):
      if overwrite:
         removetree(path.join(toDir, extractPath))
      else:
         return extractPath

   flistBefore = set(os.listdir(toDir))
   if tarName.endswith('tar.gz') or tarName.endswith('tgz'):
      execAndWait('tar -zxf %s -C %s' % (tardl, toDir))
   elif tarName.endswith('tar.bz2') or tarName.endswith('tbz'):
      execAndWait('tar -jxf %s -C %s' % (tardl, toDir))
   elif tarName.endswith('tar.xz'):
      execAndWait('tar -Jxf %s -C %s' % (tardl, toDir))
   elif tarName.endswith('zip'):
      zip_ref = zipfile.ZipFile(tardl, 'r')
      zip_ref.extractall(toDir)
      zip_ref.close()
   else:
      raise RuntimeError('Not a recognized tar name')
   newStuff = []
   for objPath in os.listdir(toDir):
      if not objPath in flistBefore:
         newStuff.append(path.join(toDir, objPath))

   logprint('Unpacked: %s' % tardl)
   for objPath in newStuff:
      logprint('  ' + objPath)

   if len(newStuff) > 1:
      logprint('*** ERROR:  tarfile unpacked more than one object! ***' )

   return newStuff[0] if len(newStuff)==1 else newStuff

################################################################################
def downloadPkg(pkgname, fname, url, ID, toDir=WORKDLDIR):
   myfile = path.join(toDir, fname)
   doDL = True

   if path.exists(myfile):
      if check_sha(myfile, ID):
         logprint("File already exists: %s" % myfile)
         doDL = False
      else:
         removefile(myfile)
         logprint("File exists but wrong hash. Redownload %s" % myfile)

   # Start the download if needed
   if doDL:
         logprint('Downloading from %s' % url)
         execAndWait('curl -OL "%s"' % url, cwd=toDir)

# List of all files needed to download.  Each item is
# (Name, filename, url, sha-1 or None)
distfiles = []
distfiles.append( [ 'Python', \
                    "Python-%s.tar.xz" % pythonVer, \
                    "http://python.org/ftp/python/%s/Python-%s.tar.xz" % (pythonVer, pythonVer), \
                    "cf146474fc988b4b6b53fdd81b71c2815873b469" ] )

distfiles.append( [ 'setuptools', \
                    "setuptools-%s.zip" % setToolVer, \
                    "https://pypi.python.org/packages/%s/setuptools-%s.zip" % (setToolSubdir, setToolVer), \
                    "a1044deb1f2c42f037003f02704557fb4ee55694" ] )

distfiles.append( [ 'Pip', \
                    "pip-%s.tar.gz" % pipVer, \
                    "https://pypi.python.org/packages/%s/pip-%s.tar.gz" % (pipSubdir, pipVer), \
                    "57ff41e99cb01b6a1c2b0999161589b726f0ec8b" ] )

distfiles.append( [ "psutil", \
                    "psutil-%s.tar.gz" % psutilVer, \
                    "https://pypi.python.org/packages/%s/psutil-%s.tar.gz" % (psutilSubdir, psutilVer), \
                    "6305bc320d7b9d37967e5e004e2404beefa71a34" ] )

distfiles.append( [ 'libpng', \
                    "libpng-%s.tar.xz" % libpngVer, \
                    "https://sourceforge.net/projects/libpng/files/libpng16/%s/libpng-%s.tar.xz" % (libpngVer, libpngVer), \
                    "45de4ec996ffcc3e18037e7c128abe95f4d0292a" ] )

# When we upgrade to Qt5....
#distfiles.append( [ "Qt", \
#                    "qt-everywhere-opensource-src-5.2.1.tar.gz", \
#                    "http://download.qt-project.org/official_releases/qt/5.2/5.2.1/single/qt-everywhere-opensource-src-5.2.1.tar.gz", \
#                    "31a5cf175bb94dbde3b52780d3be802cbeb19d65" ] )

distfiles.append( [ "Qt", \
                    "qt-everywhere-opensource-src-%s.tar.gz" % qtVer, \
                    "http://download.qt-project.org/official_releases/qt/4.8/%s/qt-everywhere-opensource-src-%s.tar.gz" % (qtVer, qtVer), \
                    "76aef40335c0701e5be7bb3a9101df5d22fe3666" ] )

distfiles.append( [ "sip", \
                    "sip-%s.tar.gz" % sipVer, \
                    "https://sourceforge.net/projects/pyqt/files/sip/sip-%s/sip-%s.tar.gz" % (sipVer, sipVer), \
                    '61ff744c67642f10a352f3e076cbe89c79e6387b' ] )

# When we upgrade to Qt5....
#distfiles.append( [ "pyqt", \
#                    "PyQt-gpl-5.2.tar.gz", \
#                    "http://downloads.sf.net/project/pyqt/PyQt5/PyQt-5.2/PyQt-gpl-5.2.tar.gz", \
#                    'a1c232d34ab268587c127ad3097c725ee1a70cf0' ] )

distfiles.append( [ "pyqt", \
                    "PyQt4_gpl_mac-%s.tar.gz" % pyQtVer, \
                    "https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-%s/PyQt4_gpl_mac-%s.tar.gz" % (pyQtVer, pyQtVer), \
                    '028f3fc979428687e8e8fd78288b41f1b5735a7c' ] )

distfiles.append( [ 'Twisted', \
                    "Twisted-%s.tar.bz2" % twistedVer, \
                    "https://files.pythonhosted.org/packages/%s/Twisted-%s.tar.bz2" % (twistedSubdir, twistedVer), \
                    "a218e69ab51b5c6b632043f91aed98bc92083a90" ] )

# Now repack the information in distfiles
tarfilesToDL = {}
for d in distfiles:
   tarfilesToDL[d[0]] = d[1]

########################################################
def make_empty_app():
   'Make the empty .app bundle structure'
   makedir(APPBASE)
   makedir(path.join(APPBASE,'Contents'))
   makedir(path.join(APPBASE,'Contents/MacOS'))
   makedir(path.join(APPBASE,'Contents/MacOS/py'))
   makedir(path.join(APPBASE,'Contents/Frameworks'))
   makedir(path.join(APPBASE,'Contents/Resources'))
   makedir(path.join(APPBASE,'Contents/Dependencies'))

########################################################
def compile_python():
   logprint('Installing python')
   bldPath = unpack(tarfilesToDL['Python'])

   # ./configure - Force Python to link against a brew-ed version of OpenSSL
   # due to Python not liking the ancient (0.9.8) version of OpenSSL Apple
   # includes with OS X.
   # Note that there's something weird going on with the linker flags, even when
   # adding custom OpenSSL paths the official way (modding Modules/Setup.dist).
   # To get around this, manually specify the linker flags (both -L *and* -l)
   # under LDFLAGS. (CFLAGS and CPPFLAGS probably not needed but it works, so
   # leave it alone for now....)
   logprint('Modify Python modules setup files.')
   logprint('OpenSSL path = %s' % opensslPath)
   modSetupFile = path.join(bldPath, 'Modules/Setup.dist')
   with open(modSetupFile) as origFile:
      setupText = origFile.read()
   setupText = setupText.replace("#SSL=/usr/local/ssl", "SSL=%s" % opensslPath, 1)
   setupText = setupText.replace("#_ssl _ssl.c \\", "_ssl _ssl.c \\", 1)
   setupText = setupText.replace("#	-DUSE_SSL -I$(SSL)/include -I$(SSL)/include/openssl \\", "	-DUSE_SSL -I$(SSL)/include -I$(SSL)/include/openssl \\", 1)
   setupText = setupText.replace("#	-L$(SSL)/lib -lssl -lcrypto", "	-L$(SSL)/lib -lssl -lcrypto", 1)
   with open(modSetupFile, "w") as origFile:
      origFile.write(setupText)

   frameDir = path.join(APPBASE, 'Contents/Frameworks')
   execAndWait('./configure CFLAGS=-I%s/include CPPFLAGS=-I%s/include LDFLAGS=\"-L%s/lib -lssl -lcrypto\" --enable-ipv6 --prefix=%s --enable-framework="%s"' % \
                                             (opensslPath, opensslPath, opensslPath, WORKINSTALLDIR, frameDir), cwd=bldPath)

   # make
   execAndWait('make %s' % MAKEFLAGS, cwd=bldPath)
   execAndWait('make install PYTHONAPPSDIR=%s' % WORKINSTALLDIR, cwd=bldPath)

   # Update $PATH var
   newPath = path.join(PYFRAMEBASE, 'bin')
   os.environ['PATH'] = '%s:%s' % (newPath, os.environ['PATH'])
   logprint('PATH is now %s' % os.environ['PATH'])

########################################################
def compile_pip():
   logprint('Installing pip and setuptools')
   pipexe = path.join(PYFRAMEBASE, 'bin/pip')
   if path.exists(pipexe):
      logprint('Pip already installed')
   else:
      command = 'python -s setup.py --no-user-cfg install --force --verbose'

      # Unpack and build setuptools
      logprint('Installing setuptools.')
      setupDir = unpack(tarfilesToDL['setuptools'])
      execAndWait(command, cwd=setupDir)

      # Unpack and build pip
      logprint('Installing pip.')
      pipDir   = unpack(tarfilesToDL['Pip'])
      execAndWait(command, cwd=pipDir)

########################################################
def compile_libpng():
   logprint('Installing libpng')
   dylib = 'libpng16.16.dylib'
   target = path.join(APPBASE, 'Contents/Dependencies', dylib)
   if path.exists(target):
      logprint('libpng already installed.')
   else:
      pngDir = unpack(tarfilesToDL['libpng'])
      command = './configure'
      execAndWait(command, cwd=pngDir)
      command = 'make %s' % MAKEFLAGS
      execAndWait(command, cwd=pngDir)
      src = path.join(pngDir, '.libs', dylib)
      copyfile(src, target)

########################################################
def compile_qt():
   logprint('Compiling Qt')

   # Already cloned to the qtDLDir, then tar it and move the dir to
   # qtBuildDir. Then we will build inside the qtBuildDir, using qtInstDir
   # as the prefix.
   qtDLDir    = path.join(WORKDLDIR, 'qt')
   qtBuildDir = path.join(WORKUNPACKDIR, 'qt-everywhere-opensource-src-%s' % qtVer)
   qtInstDir  = path.join(WORKINSTALLDIR, 'qt')
   qtTarFile   = path.join(WORKDLDIR, 'qt-everywhere-opensource-src-%s.tar.gz' % qtVer)

   # If we did a fresh download, it's already uncompressed in DLDir. Move it
   # to where it should be in the WORKUNPACKDIR
   if path.exists(qtDLDir):
      if path.exists(qtBuildDir):
         removetree(qtBuildDir)
      movepath(qtDLDir, qtBuildDir)

   # If it's not in the bld dir, unpack it from the tar file.
   # If it's not in the tar file, either, we have a problem.
   if not path.exists(qtBuildDir):
      if not path.exists(qtTarFile):
         raise RuntimeError('*** ERROR: No cloned repo and no tar file...? ***')
      logprint('Unpacking Qt from tarfile')
      qtBuildDir = unpack(tarfilesToDL['Qt'])

   # Qt Patches
   # Partial bug fixes for modal windows.
   execAndWait('patch -p1 < %s' % path.join(os.getcwd(), 'QTBUG-37699.patch'), cwd=qtBuildDir)
   # Completed bug fixes for modal windows.
   execAndWait('patch -p1 < %s' % path.join(os.getcwd(), 'QTBUG-40585.patch'), cwd=qtBuildDir)
   # This API is deprecated.
   execAndWait('patch -p1 < %s' % path.join(os.getcwd(), 'qpaintengine_mac.patch'), cwd=qtBuildDir)
   # macOS 10.13 errors on unused code.
   execAndWait('patch -p1 < %s' % path.join(os.getcwd(), 'qt_cocoa_helpers_mac.patch'), cwd=qtBuildDir)

   # Configure Qt. http://wiki.phisys.com/index.php/Compiling_Phi has an example
   # that can be checked for ideas.
   # NB: -no-phonon, despite supposedly being Windows-only, is required when
   #     building under OS X 10.12, otherwise compilation fails.
   # NB: To be safe, force compilation against a brew-ed version of OpenSSL, not
   #     the ancient version provided by Apple.
   # NB: Qt5 apparently requires the "-c++11" flag, which isn't in Qt4.
   #     "-platform macx-clang-libc++" will also probably be required.
   command  = './configure -prefix "%s" -system-zlib -confirm-license '
   command += ' -opensource -nomake demos -nomake examples -nomake docs -cocoa '
   command += '-fast -release -no-webkit -no-javascript-jit -nomake tools '
   command += '-nomake tests -no-qt3support -arch x86_64 -no-3dnow -no-phonon '
   command += '-I %s/include -L %s/lib -platform unsupported/macx-clang-libc++'
   execAndWait(command % (qtInstDir, opensslPath, opensslPath), cwd=qtBuildDir)

   # Make
   execAndWait('make %s' % MAKEFLAGS, cwd=qtBuildDir)

########################################################
def install_qt():
      logprint('Installing Qt')
      if not path.exists(QTBUILTFLAG):
         compile_qt()
         execAndWait('touch %s' % QTBUILTFLAG)
      else:
         logprint('QT already compiled.  Skipping compile step.')

      qtconf = path.join(qtBinDir, 'qt.conf')
      execAndWait('make install', cwd=qtBuildDir)

      newcwd = path.join(APPBASE, 'Contents/Frameworks')

      for mod in ['QtCore', 'QtGui', 'QtNetwork']:
         src = path.join(qtInstDir, 'lib', mod+'.framework')
         dst = path.join(APPBASE, 'Contents/Frameworks', mod+'.framework')
         if path.exists(dst):
            removetree(dst)
         copytree(src, dst)

      if not os.path.exists(qtBinDir):
         os.makedirs(qtBinDir)
      with open(qtconf, 'w') as f:
         f.write('[Paths]\nPrefix = %s' % qtInstDir)

########################################################
def compile_sip():
   logprint('Installing sip')
   if path.exists(path.join(PYSITEPKGS, 'sip.so')):
      logprint('Sip is already installed.')
   else:
      sipPath = unpack(tarfilesToDL['sip'])
      command  = 'python configure.py'
      command += ' --destdir="%s"' % PYSITEPKGS
      command += ' --bindir="%s/bin"' % PYFRAMEBASE
      command += ' --incdir="%s/include"' % PYFRAMEBASE
      command += ' --sipdir="%s/share/sip"' % PYFRAMEBASE
      command += ' --deployment-target=%s' % minOSXVer
      execAndWait(command, cwd=sipPath)
      execAndWait('make %s' % MAKEFLAGS, cwd=sipPath)

   # Must run "make install" again even if it was previously built (since
   # the APPBASE and WORKINSTALLDIR are wiped every time the script is run)
   execAndWait('make install', cwd=sipPath)

########################################################
def compile_pyqt():
   logprint('Installing PyQt4')
   #logprint('Install PyQt5')
   #if path.exists(path.join(PYSITEPKGS, 'PyQt5')):
   if path.exists(path.join(PYSITEPKGS, 'PyQt4')):
      logprint('PyQt4 is already installed.')
   else:
      pyqtPath = unpack(tarfilesToDL['pyqt'])
      incDir = path.join(PYFRAMEBASE, 'include')
      execAndWait('python ./configure-ng.py --confirm-license --sip-incdir="%s"' % incDir, cwd=pyqtPath)
      execAndWait('make %s' % MAKEFLAGS, cwd=pyqtPath)

   # Need to add pyrcc4 to the PATH
   execAndWait('make install', cwd=pyqtPath)
   pyrccPath = path.join(WORKUNPACKDIR, 'PyQt_mac_gpl-%s/pyrcc' % pyQtVer)
   os.environ['PATH'] = '%s:%s' % (pyrccPath, os.environ['PATH'])

########################################################
def compile_psutil():
   logprint('Installing psutil')

   if glob.glob(PYSITEPKGS + '/psutil*'):
      logprint('Psutil already installed')
   else:
      command = 'python -s setup.py --no-user-cfg install --force --verbose'
      psPath = unpack(tarfilesToDL['psutil'])
      execAndWait(command, cwd=psPath)

########################################################
def compile_twisted():
   logprint('Installing python-twisted')

   if glob.glob(PYSITEPKGS + '/Twisted*'):
      logprint('Twisted already installed')
   else:
      command = "python -s setup.py --no-user-cfg install --force --verbose"
      twpath = unpack(tarfilesToDL['Twisted'])
      execAndWait(command, cwd=twpath)

########################################################
def compile_armory():
   logprint('Compiling and installing Armory')
   # Always compile - even if already in app
   armoryAppScript = path.join(APPBASE, 'Contents/MacOS/Armory')
   armorydAppScript = path.join(APPBASE, 'Contents/MacOS/armoryd')
   armoryDB = path.join(APPBASE, 'Contents/MacOS/ArmoryDB')
   currentDir = os.getcwd()
   os.chdir("..")
   execAndWait('python update_version.py')
   os.chdir(currentDir)
   execAndWait('./autogen.sh', cwd='..')
   execAndWait('./configure %s' % CONFIGFLAGS, cwd='..')
   execAndWait('make clean', cwd='..')
   execAndWait('make DESTDIR="%s" install %s' % (ARMORYCODEBASE, MAKEFLAGS), cwd='..')
   copyfile('Armory-script.sh', armoryAppScript)
   copyfile('armoryd-script.sh', armorydAppScript)
   execAndWait('chmod +x "%s"' % armoryAppScript)
   execAndWait('chmod +x "%s"' % armorydAppScript)
   execAndWait('chmod +x "%s"' % armoryDB) # ArmoryDB copied over by Makefile

########################################################
def compile_objc_library():
   logprint('Compiling and installing the Armory Objective-C shared library')

   # Execute SIP to create the Python/Obj-C++ glue code, use qmake to create the
   # Makefile, and make the shared library. Be sure to keep the SIP flags in
   # sync with generate_sip_module_code() from PyQt's configure-ng.py.
   sipFlags = '-w -x VendorID -t WS_MACX -t Qt_4_8_7 -x Py_v3 -B Qt_5_0_0 -o ' \
              '-P -g -c . -I ../workspace/unpackandbuild/PyQt4_gpl_mac-%s/sip' % pyQtVer
   execAndWait('../workspace/unpackandbuild/sip-%s/sipgen/sip %s ./ArmoryMac.sip' % (sipVer, sipFlags), cwd=OBJCDIR)
   execAndWait('../workspace/unpackandbuild/qt-everywhere-opensource-src-%s/bin/qmake ArmoryMac.pro' % qtVer, cwd=OBJCDIR)

   # For some reason, qmake mangles LFLAGS when LFLAGS is built. The exact cause
   # is unknown but probably has to do with a conf file included in
   # mkspecs/unsupported/macx-clang-libc++/qmake.conf. Patch the output for now.
   execAndWait('patch -p0 < %s' % path.join(os.getcwd(), 'qmake_LFLAGS.patch'), cwd=OBJCDIR)
   execAndWait('make %s' % MAKEFLAGS, cwd=OBJCDIR)


########################################################
def make_resources():
   "Populate the Resources folder."
   cont = path.join(APPBASE, 'Contents')
   copyfile('Info.plist', cont)

   icnsArm = '../img/armory_icon_fullres.icns'
   icnsRes  = path.join(cont,  'Resources/Icon.icns')
   copyfile(icnsArm, icnsRes)

########################################################
def cleanup_app():
   "Try to remove as much unnecessary junk as possible."
   print "Removing Python test-suite."
   testdir = path.join(PYFRAMEBASE, "lib/python%s/test" % pyMajorVer)
   if path.exists(testdir):
      removetree(testdir)

   print "Removing .pyo and .pyc files."
   remove_python_files(ARMORYCODEBASE)

########################################################
def make_targz():
   ver = getVersionStr()
   execAndWait('tar -zcf ../armory_%s_osx.tar.gz Armory.app' % ver, cwd=WORKDIR)

########################################################
def getVersionStr():
   with open('../armoryengine/ArmoryUtils.py') as f:
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
            return vstr


########################################################
def show_app_size():
   # Macs are very peculiar about getting the sizes of things from the terminal.
   # Some commands (e.g., "find") are also really slow when piped around. The
   # following command is fast *and* accurate. Don't touch without good reasons!
   "Show the size of the app."
   execAndWait('ls -lR %s | grep -v \'^d\' | awk \'{total += $5} END ' \
               '{print \"Total size of Armory:\", total, \"bytes\"}\'' % APPBASE)
   sys.stdout.flush()

########################################################
def remove_python_files(top):
   """Remove .pyo and .pyc files."""
   n_pyo = 0
   n_pyc = 0

   for (dirname, dirs, files) in os.walk(top):
      for f in files:
         prename, ext = path.splitext(f)
         if ext == '.pyo':
            removefile(path.join(dirname, f))
            n_pyo += 1
         elif ext == '.pyc':
            removefile(path.join(dirname, f))
            n_pyc += 1

   logprint("Removed %i .pyo and %i .pyc files." % (n_pyo, n_pyc))

########################################################
def delete_prereq_data(opts):
   # If we ran this before, we should have a qt dir here
   prevQtDir = path.join(WORKUNPACKDIR, 'qt')

   # Always remove previously-built application files
   removetree(APPBASE)
   removetree(WORKINSTALLDIR)

   # When building from scratch
   if opts.fromscratch:
      removetree(WORKUNPACKDIR) # Clear all unpacked tar files
      removetree(WORKDLDIR) # Clear even the downloaded files
   elif opts.rebuildall:
      removetree(WORKUNPACKDIR)
   else:
      logprint('Using all packages previously downloaded and built')

########################################################
if __name__ == "__main__":
   main()
