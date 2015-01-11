#!/usr/env python
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

from subprocess import Popen, PIPE
from tempfile import mkstemp

# Set some constants up front
#swigBinVer = '2.0.12'
minOSXVer    = '10.7'
osxName      = 'Yosemite'
pythonVer    = '2.7.9'  # NB: ArmoryMac.pro must also be kept up to date!!!
pyMajorVer   = '2.7'
setToolVer   = '10.2.1'
pipVer       = '6.0.3'
psutilVer    = '2.1.3'
zopeVer      = '4.1.1'
twistedVer   = '14.0.2'
libpngVer    = '1.6.15'
qtVer        = '4.8.7'  # NB: ArmoryMac.pro must also be kept up to date!!!
                        # Possibly "sipFlags" below too.
sipVer       = '4.16.5' # NB: ArmoryMac.pro must also be kept up to date!!!
pyQtVer      = '4.11.3' # NB: When I'm upgraded, SIP usually has to be upgraded too.
webkitRev    = '175335'
appNopeVer   = '0.1.0'
LOGFILE      = 'build-app.log.txt'
LOGPATH      = path.abspath( path.join(os.getcwd(), LOGFILE))
ARMORYDIR    = '..'
OBJCDIR      = path.join(os.getcwd(), 'objc_armory')
WORKDIR      = path.join(os.getcwd(), 'workspace')
APPDIR       = path.join(WORKDIR, 'Armory.app') # actually make it local
DLDIR        = path.join(WORKDIR, 'downloads')
UNPACKDIR    = path.join(WORKDIR, 'unpackandbuild')
#SWIGDIR      = path.join(UNPACKDIR, 'swig', swigBinVer)
INSTALLDIR   = path.join(WORKDIR, 'install')
PYPREFIX     = path.join(APPDIR, 'Contents/Frameworks/Python.framework/Versions/%s' % pyMajorVer)
PYSITEPKGS   = path.join(PYPREFIX, 'lib/python%s/site-packages' % pyMajorVer)
MAKEFLAGS    = '-j4'

QTBUILTFLAG = path.join(UNPACKDIR, 'qt/qt_install_success.txt')

#pypath_txt_template=""" PYTHON_INCLUDE=%s/include/python2.7/ PYTHON_LIB=%s/lib/python2.7/config/libpython2.7.a PYVER=python2.7 """
pypathData  =   'PYTHON_INCLUDE=%s/include/python%s/' % (PYPREFIX, pyMajorVer)
pypathData += '\nPYTHON_LIB=%s/lib/python%s/config/libpython%s.a' % (PYPREFIX, pyMajorVer, pyMajorVer)
pypathData += '\nPYTHON_LIB_DIR=%s/lib/python%s/config/' % (PYPREFIX, pyMajorVer)
pypathData += '\nPYVER=python%s' % pyMajorVer

# If no arguments specified, then do the minimal amount of work necessary
# Assume that only one flag is specified.  These should be 
parser = optparse.OptionParser(usage="%prog [options]\n")
parser.add_option('--fromscratch',  dest='fromscratch',  default=False, action='store_true', help='Remove all prev-downloaded: redownload and rebuild all')
parser.add_option('--rebuildall',   dest='rebuildall',   default=False, action='store_true', help='Remove all prev-built; no redownload, only rebuild')
parser.add_option('--qtcheckout',   dest='qtcheckout',   default='4.8', type='str',          help='Specify commit to checkout, after a pull')
parser.add_option('--qtupdate',     dest='qtupdate',     default=False, action='store_true', help='Rebuild only qt libraries, if already built')
parser.add_option('--qtrebuild',    dest='qtrebuild',    default=False, action='store_true', help='Rebuild only qt libraries, if already built')
parser.add_option('--precompiledQt',dest='precompiledQt',default=False, action='store_true', help='Download and use a precompiled version of Qt')
(CLIOPTS, CLIARGS) = parser.parse_args()

################################################################################
# Now actually start the download&build process
   
# Make sure all the dirs exist
def main():
   
   if path.exists(LOGFILE):
      os.remove(LOGFILE)

   delete_prev_data(CLIOPTS)

   makedir(WORKDIR)
   makedir(DLDIR)
   makedir(UNPACKDIR)
   makedir(INSTALLDIR)
      
   # For git repos, the "ID" is branch name.  Otherwise, its' the md5sum 
   for pkgname, fname, url, ID in distfiles:
      logprint('\n\n')
      # Skip download of Qt-git if downloading Qt, and vice versa.
      #if((pkgname.lower()=='qt-git' and     CLIOPTS.precompiledQt) or \
      #   (pkgname.lower()=='qt'     and not CLIOPTS.precompiledQt)     ):
      #   continue
      downloadPkg(pkgname, fname, url, ID)

   logprint("\n\nALL DOWNLOADS COMPLETED.\n\n")
   
   make_empty_app()
   compile_python()
   compile_pip()
   install_libpng()
   install_qt()
   compile_sip()
   compile_pyqt()
   compile_zope()
   compile_twisted()
   compile_psutil()
   #compile_appnope() # Disable App Nap. Done already in Mac manifest.
   #unzip_swig()
   compile_armory()
   compile_objc_library()
   make_resources()
   cleanup_app()
   # Force Finder to update the Icon
   execAndWait("touch " + APPDIR)
   make_targz()

################################################################################
# Write the string to both console and log file
def logprint(s):
   print s
   with open(LOGFILE,'a') as f:
      f.write(s if s.endswith('\n') else s+'\n')

################################################################################
"""
# While this worked well to capture the output, buffering made it impossible
# to write the data to stdout in real time (it woud all buffer up to the end
def execAndWait(syscmd, cwd=None):
   try:
      logprint('*'*80)
      logprint('Executing: "%s"' % syscmd)
      proc = Popen(syscmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True, cwd=cwd)
      while proc.poll() == None:
         time.sleep(0.25)
   
   except Exception as e:
      logprint('\n' + '-'*80)
      logprint('ERROR: %s' % str(e))
      logprint('-'*80 + '\n')
   finally:
      out,err = proc.communicate()
      logprint('STDOUT:')
      logprint(out if len(out.strip()) > 0 else "<NO OUTPUT>")
      logprint('STDERR:')
      logprint(err if len(err.strip()) > 0 else "<NO OUTPUT>")
      logprint('*'*80)
      return [out,err]
"""

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

   # HACK: XZ support was added to tarfile.open() in Python 3.3. Can't use for
   # now, so we'll have to apply a hack to get around this. In addition, the
   # builder must have the xz binary on their build machine, otherwise the
   # following error will appear: "tar: Error opening archive: Child process
   # exited with status 254Child process exited with status 254"
   if tarName == "Python-%s.tar.xz" % pythonVer:
      theDir = "Python-%s" % pythonVer
   else:
      tar = tarfile.open(tarPath,'r')
      theDir = tar.next().name.split('/')[0]
      tar.close()
   return theDir

################################################################################
def unpack(tarName, fromDir=DLDIR, toDir=UNPACKDIR, overwrite=False):
   """
   This is not a versatile function.  It expects tar files with a single 
   unpack directory.  I will expand this function as necessary if we
   need tar files that aren't a single bundled dir.
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
   elif tarName.endswith('tar.xz') or tarName.endswith('xz'):
      execAndWait('tar -Jxf %s -C %s' % (tardl, toDir))
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
def downloadPkg(pkgname, fname, url, ID, toDir=DLDIR):
   myfile = path.join(toDir, fname)
   isGitRepo = url.lower().startswith('git:')
   doDL = True
   if isGitRepo:
      clonename = '.'.join(url.split('/')[-1].split('.')[:-1])
      clonedir = path.join(toDir, clonename) 
      branch = ID[:]  # the ID value is actually the branch name
      if path.exists(clonedir) or path.exists(path.join(DLDIR,fname)):
         doDL=False
   elif path.exists(myfile):
      if check_sha(myfile, ID):
         logprint("File already exists: %s" % myfile)
         doDL = False
      else:
         removefile(myfile)
         logprint("File exists but wrong hash.  Redownload %s" % myfile)
           
   # Start the download if needed
   if doDL:
      if isGitRepo:
         # NB: The "git checkout" line appears to be temporarily broken. As of
         # May 2014, we're passing in "4.8" for Qt. The actual repository is
         # "qt" but the default branch is "4.8", so we're okay. Clean up later?
         logprint('Cloning "%s" to "%s"' % (url, clonedir))
         execAndWait('git clone %s' % url, cwd=toDir)
         execAndWait('git checkout %s' % ID) 
      else:
         logprint('Downloading from %s' % url)
         execAndWait('curl -OL "%s"' % url, cwd=toDir)

# List of all files needed to download.  Each item is
# (Name, filename, url, sha-1 or None)
distfiles = []
distfiles.append( [ 'Python', \
                    "Python-%s.tar.xz" % pythonVer, \
                    "http://python.org/ftp/python/%s/Python-%s.tar.xz" % (pythonVer, pythonVer), \
                    "3172f6e957713c2d9fca462cc16068222fd1b9d3" ] )

distfiles.append( [ 'setuptools', \
                    "setuptools-%s.tar.gz" % setToolVer, \
                    "https://pypi.python.org/packages/source/s/setuptools/setuptools-%s.tar.gz" % setToolVer, \
                    "09da3f767e40d1451cac97af59afd99802c77076" ] )

distfiles.append( [ 'Pip', \
                    "pip-%s.tar.gz" % pipVer, \
                    "https://pypi.python.org/packages/source/p/pip/pip-%s.tar.gz" % pipVer, \
                    "67d4affd83ee2f3514ac1386bee59f10f672517c" ] )

distfiles.append( [ "psutil", \
                    "psutil-%s.tar.gz" % psutilVer, \
                    "https://pypi.python.org/packages/source/p/psutil/psutil-%s.tar.gz" % psutilVer, \
                    "aae4725eb33cf56d4480bc60f50c147870d607ba" ] )

distfiles.append( [ 'Twisted', \
                    "Twisted-%s.tar.bz2" % twistedVer, \
                    "https://pypi.python.org/packages/source/T/Twisted/Twisted-%s.tar.bz2" % twistedVer, \
                    "b908dc0d117a782d2becc83fbb906ba4311f3351" ] )

# Other lines rely on the given version. Patch this up later.
distfiles.append( [ 'libpng', \
                    "libpng-%s.mavericks.bottle.tar.gz" % libpngVer, \
                    "https://downloads.sf.net/project/machomebrew/Bottles/libpng-%s.mavericks.bottle.tar.gz" % libpngVer, \
                    "059d99d0321a8519252ae860667237a838d2a557" ] )

# Skipping Git for now.
#distfiles.append( [ "Qt-git", \
#                    "qt5_git_repo.tar.gz", \
#                    'git://gitorious.org/qt/qt5.git',
#                    'stable' ] )

#distfiles.append( [ "Qt-git", \
#                    "qt4_git_repo.tar.gz", \
#                    'git://gitorious.org/qt/qt.git',
#                    '4.8' ] )

# When we upgrade to Qt5....
#distfiles.append( [ "Qt", \
#                    "qt-everywhere-opensource-src-5.2.1.tar.gz", \
#                    "http://download.qt-project.org/official_releases/qt/5.2/5.2.1/single/qt-everywhere-opensource-src-5.2.1.tar.gz", \
#                    "31a5cf175bb94dbde3b52780d3be802cbeb19d65" ] )

# Pre-packaged source can lag a bit but provides for more consistent user
# support. Use pre-packaged source instead of Git whenever possible.
distfiles.append( [ "Qt", \
                    #"qt-everywhere-opensource-src-%s.tar.gz" % qtVer, \
                    "qt-everywhere-opensource-src-%s-2014-12-22-1.tar.gz" % qtVer, \
                    #"http://download.qt-project.org/official_releases/qt/4.8/%s/qt-everywhere-opensource-src-%s.tar.gz" % (qtVer, qtVer), \
                    "http://download.qt.io/snapshots/qt/4.8/%s/2014-12-22-1/qt-everywhere-opensource-src-%s-2014-12-22-1.tar.gz" % (qtVer, qtVer), \
                    #"745f9ebf091696c0d5403ce691dc28c039d77b9e" ] )
                    "b09249918b4de8125f3d88604a5889ce9fc151b1" ] )

distfiles.append( [ "Webkit-for-Qt", \
                    "libWebKitSystemInterface%s.a" % osxName, \
                    "http://trac.webkit.org/export/%s/trunk/WebKitLibraries/libWebKitSystemInterface%s.a" % (webkitRev, osxName), \
                    "c8db972c03953d0d3ef89c7e67ce4a2e46dd9c36" ] )

distfiles.append( [ "sip", \
                    "sip-%s.tar.gz" % sipVer, \
                    "http://sourceforge.net/projects/pyqt/files/sip/sip-%s/sip-%s.tar.gz" % (sipVer, sipVer), \
                    'd5d7b6765de8634eccf48a250dbd915f01b2a771' ] )

distfiles.append( [ "zope", \
                    "zope.interface-%s.tar.gz" % zopeVer, \
                    "https://pypi.python.org/packages/source/z/zope.interface/zope.interface-%s.tar.gz" % zopeVer, \
                    '20a9284429e29eb8cc63eee5ed686c257c01b1fc' ] )

# When we upgrade to Qt5....
#distfiles.append( [ "pyqt", \
#                    "PyQt-gpl-5.2.tar.gz", \
#                    "http://downloads.sf.net/project/pyqt/PyQt5/PyQt-5.2/PyQt-gpl-5.2.tar.gz", \
#                    'a1c232d34ab268587c127ad3097c725ee1a70cf0' ] )

distfiles.append( [ "pyqt", \
                    "PyQt-mac-gpl-%s.tar.gz" % pyQtVer, \
                    "http://downloads.sf.net/project/pyqt/PyQt4/PyQt-%s/PyQt-mac-gpl-%s.tar.gz" % (pyQtVer, pyQtVer), \
                    '8c53254b38686e5366d74eba81f02f9611f39166' ] )

#distfiles.append( [ 'appnope', \
#                    "appnope-%s.tar.gz" % appNopeVer, \
#                    "https://pypi.python.org/packages/source/a/appnope/appnope-%s.tar.gz" % appNopeVer, \
#                    "838158bf881f3e8538b7bfeff4ad289a6623cdda" ] )

# May roll our own SWIG/PCRE someday. For now, assume the user already has SWIG.
#distfiles.append( [ 'swig', \
#                    "swig-2.0.12.mavericks.bottle.tar.gz", \
#                    "https://downloads.sf.net/project/machomebrew/Bottles/swig-2.0.12.mavericks.bottle.tar.gz", \
#                    "5e429bc6228e8ec1f154ee5eb9497b54b8b765d5" ] )

# Now repack the information in distfiles
tarfilesToDL = {}
for d in distfiles:
   tarfilesToDL[d[0]] = d[1]

################################################################################
def make_empty_app():
   'Make the empty .app bundle structure'
   makedir(APPDIR)
   makedir(path.join(APPDIR,'Contents'))
   makedir(path.join(APPDIR,'Contents/MacOS'))
   makedir(path.join(APPDIR,'Contents/MacOS/py'))
   makedir(path.join(APPDIR,'Contents/Frameworks'))
   makedir(path.join(APPDIR,'Contents/Resources'))
   makedir(path.join(APPDIR,'Contents/Dependencies'))

################################################################################
def compile_python():
   logprint('Installing python.')
   bldPath = unpack(tarfilesToDL['Python'])

   # ./configure
   frameDir = path.join(APPDIR, 'Contents/Frameworks')
   execAndWait('./configure --enable-ipv6 --prefix=%s --enable-framework="%s"' % \
                                             (INSTALLDIR, frameDir), cwd=bldPath)

   # make
   execAndWait('make %s' % MAKEFLAGS, cwd=bldPath)
   # pyexe = path.join(APPDIR, 'Contents/MacOS/Python')
   execAndWait('make install PYTHONAPPSDIR=%s' % INSTALLDIR, cwd=bldPath)

   # Update $PATH var
   newPath = path.join(PYPREFIX, 'bin')
   os.environ['PATH'] = '%s:%s' % (newPath, os.environ['PATH'])
   logprint('PATH is now %s' % os.environ['PATH'])

################################################################################
def compile_pip():
   logprint('Installing setuptools.')
   pipexe = path.join(PYPREFIX, 'bin/pip')
   if path.exists(pipexe):
      logprint('Pip already installed')
   else:
      logprint('Installing pip.')
      command = 'python -s setup.py --no-user-cfg install --force --verbose'

      # Unpack and build setuptools
      setupDir = unpack(tarfilesToDL['setuptools'])
      execAndWait(command, cwd=setupDir)

      # Unpack and build pip
      pipDir   = unpack(tarfilesToDL['Pip'])
      execAndWait(command, cwd=pipDir)

################################################################################
def install_libpng():
   logprint('Installing libpng')
   dylib = 'libpng16.16.dylib'
   target = path.join(APPDIR, 'Contents/Dependencies', dylib)
   if path.exists(target):
      logprint('libpng already installed.')
   else:
      pngDir = unpack(tarfilesToDL['libpng'])
      src = path.join(pngDir, '%s/lib' % libpngVer, dylib)
      copyfile(src, target)

################################################################################
def compile_qt():
   logprint('Compiling Qt')

   # Already cloned to the qtDLDir, then tar it and move the dir to 
   # qtBuildDir.   Then we will build inside the qtBuildDir, using qtInstDir 
   # as the prefix.
   qtDLDir    = path.join(DLDIR, 'qt')
   #qtBuildDir = path.join(UNPACKDIR, 'qt-everywhere-opensource-src-%s' % qtVer)
   qtBuildDir = path.join(UNPACKDIR, 'qt-everywhere-opensource-src-%s-2014-12-22-1' % qtVer)
   qtInstDir  = path.join(INSTALLDIR, 'qt')
   #qtTarFile   = path.join(DLDIR, 'qt-everywhere-opensource-src-%s.tar.gz' % qtVer)
   qtTarFile   = path.join(DLDIR, 'qt-everywhere-opensource-src-%s-2014-12-22-1.tar.gz' % qtVer)
   #qtTarFile   = path.join(DLDIR, 'qt4_git_repo.tar.gz')
   #qtTarFile   = path.join(DLDIR, 'qt5_git_repo.tar.gz')

   # If we did a fresh download, it's already uncompressed in DLDir.  Move it
   # to where it should be in the UNPACKDIR
   if path.exists(qtDLDir):
      if path.exists(qtBuildDir):
         removetree(qtBuildDir)
      movepath(qtDLDir, qtBuildDir)

   # If it's not in the bld dir, unpack it from the tar file
   # If it's not in the tar file, either, we have a problem.  
   if not path.exists(qtBuildDir):
      if not path.exists(qtTarFile):
         raise RuntimeError('*** ERROR: No cloned repo and no tar file...? ***')
      logprint('Unpacking Qt from tarfile')
      qtBuildDir = unpack(tarfilesToDL['Qt'])
      #logprint('Remove qt4_git_repo.tar.gz to re-clone HEAD')
      #logprint('Remove qt5_git_repo.tar.gz to re-clone HEAD')
   elif not path.exists(qtTarFile):
      # Useful only if we're grabbing Qt from Git.
      logprint('Tarring downloaded repo for future use.')
      execAndWait('tar -zcf %s qt' % qtTarFile, cwd=UNPACKDIR)

   # Webkit-for-Qt is not a tar archive. It's actually just a single .a file.
   webkita = tarfilesToDL['Webkit-for-Qt']
   src = path.join(DLDIR, webkita)
   dst = path.join(qtBuildDir, 'src/3rdparty/webkit/WebKitLibraries', webkita)
   copyfile(src, dst)

   # Put Qt patches here.
   # Partial bug fixes for modal windows.
   execAndWait('patch -p0 < %s' % path.join(os.getcwd(), 'QTBUG-37699.patch'), \
               cwd=qtBuildDir)
   # Completed bug fixes for modal windows.
   execAndWait('patch -p0 < %s' % path.join(os.getcwd(), 'QTBUG-40585.patch'), \
               cwd=qtBuildDir)

   # Configure Qt. http://wiki.phisys.com/index.php/Compiling_Phi has an example
   # that can be checked for ideas.
   # NB: Qt5 apparently requires the "-c++11" flag, which isn't in Qt4.
   #     "-platform macx-clang-libc++" will also probably be required.
   command  = './configure -prefix "%s" -system-zlib -confirm-license -opensource ' 
   command += '-nomake demos -nomake examples -nomake docs -cocoa -fast -release '
   command += '-no-qt3support -arch x86_64 -no-3dnow ' 
   command += '-platform unsupported/macx-clang-libc++'
   execAndWait(command % qtInstDir, cwd=qtBuildDir)

   ##### Make
   execAndWait('make %s' % MAKEFLAGS, cwd=qtBuildDir)

   ##### Make Install
   # This will actually happen outside this function, since the INSTALLDIR
   # Gets wiped every build

################################################################################
def install_qt():
      logprint('Installing Qt')
   # We really don't need this arg for now, but maybe it'll be useful later?
   #if CLIOPTS.precompiledQt:
   #   logprint('Unpacking precompiled Qt.')
   #   qtdir = unpack(tarfilesToDL['Qt'])
   #   raise RuntimeError('Using precompiled Qt is not supported yet.')
   #else:
      if not path.exists(QTBUILTFLAG):
         compile_qt()
         execAndWait('touch %s' % QTBUILTFLAG)
      else:
         logprint('QT already compiled.  Skipping compile step.')
      
      # Even if it's already built, we'll always "make install" and then
      # set a bunch of environment variables (INSTALLDIR is wiped on every
      # Run of this script, so all "make install" steps need to be re-run
      qtInstDir  = path.join(INSTALLDIR, 'qt')
      qtBinDir = path.join(qtInstDir, 'bin')
      qtBuildDir = path.join(UNPACKDIR, 'qt-everywhere-opensource-src-%s' % qtVer)

      qtconf = path.join(qtBinDir, 'qt.conf')
      execAndWait('make install', cwd=qtBuildDir)

      newcwd = path.join(APPDIR, 'Contents/Frameworks')

      for mod in ['QtCore', 'QtGui', 'QtNetwork']:
         src = path.join(qtInstDir, 'lib', mod+'.framework')
         dst = path.join(APPDIR, 'Contents/Frameworks', mod+'.framework')
         if path.exists(dst):
            removetree(dst)
         copytree(src, dst)

      with open(qtconf, 'w') as f:
         f.write('[Paths]\nPrefix = %s' % qtInstDir)
   
      try:
         old = ':'+os.environ['DYLD_FRAMEWORK_PATH']
      except KeyError:
         old = ''
   
      # Qt5 may require QMAKESPEC to change.
      frmpath = path.join(APPDIR, 'Contents/Frameworks')
      os.environ['PATH'] = '%s:%s' % (qtBinDir, os.environ['PATH'])
      os.environ['DYLD_FRAMEWORK_PATH'] = '%s:%s' % (frmpath, old)
      os.environ['QTDIR'] = qtInstDir
      os.environ['QMAKESPEC'] = path.join(os.environ['QTDIR'], 'mkspecs/unsupported/macx-clang-libc++')
      logprint('All the following ENV vars are now set:')
      for var in ['PATH','DYLD_FRAMEWORK_PATH', 'QTDIR', 'QMAKESPEC']:
         logprint('   %s: \n      %s' % (var, os.environ[var]))

################################################################################
def compile_sip():
   logprint('Installing sip')
   if path.exists(path.join(PYSITEPKGS, 'sip.so')):
      logprint('Sip is already installed.')
   else:
      sipPath = unpack(tarfilesToDL['sip'])
      command  = 'python configure.py'
      command += ' --destdir="%s"' % PYSITEPKGS
      command += ' --bindir="%s/bin"' % PYPREFIX
      command += ' --incdir="%s/include"' % PYPREFIX
      command += ' --sipdir="%s/share/sip"' % PYPREFIX
      command += ' --deployment-target=%s' % minOSXVer
      execAndWait(command, cwd=sipPath)
      execAndWait('make', cwd=sipPath)

   # Must run "make install" again even if it was previously built (since
   # the APPDIR and INSTALLDIR are wiped every time the script is run)
   execAndWait('make install', cwd=sipPath)

################################################################################
def compile_pyqt():
   logprint('Installing PyQt4')
   #logprint('Install PyQt5')
   #if path.exists(path.join(PYSITEPKGS, 'PyQt5')):
   if path.exists(path.join(PYSITEPKGS, 'PyQt4')):
      logprint('Pyqt is already installed.')
   else:
      pyqtPath = unpack(tarfilesToDL['pyqt'])
      incDir = path.join(PYPREFIX, 'include')
      execAndWait('python ./configure-ng.py --confirm-license --sip-incdir="%s"' % incDir, cwd=pyqtPath)
      execAndWait('make %s' % MAKEFLAGS, cwd=pyqtPath)

   # Need to add pyrcc4 to the PATH
   execAndWait('make install', cwd=pyqtPath)
   pyrccPath = path.join(UNPACKDIR, 'PyQt-mac-gpl-%s/pyrcc' % pyQtVer)
   os.environ['PATH'] = '%s:%s' % (pyrccPath, os.environ['PATH'])

################################################################################
'''
def pip_install(package, lookfor):
   """Install package with pip.

   For some reason this appears to be broken.  Pip installs psutil in /usr/local instead of
   inside the app.  Strange.  Do not use!
   """
   if path.exists(path.join(PYSITEPKGS, lookfor)):
      print package, "already installed"
   else: 
      print "Installing %s using pip." % (package,)
      execAndWait("pip install %s > pip-%s.log 2>&1" % (package, package))
'''

################################################################################
def compile_twisted():
   logprint('Installing python-twisted')

   if glob.glob(PYSITEPKGS + '/Twisted*'):
      logprint('Twisted already installed')
   else:
      command = "python -s setup.py --no-user-cfg install --force --verbose"
      twpath = unpack(tarfilesToDL['Twisted'])
      execAndWait(command, cwd=twpath)

################################################################################
def compile_zope():
   logprint('Installing python-zope')

   if glob.glob(PYSITEPKGS + '/zope*'):
      logprint('zope already installed')
   else:
      command = "python -s setup.py --no-user-cfg install --force --verbose"
      twpath = unpack(tarfilesToDL['zope'])
      execAndWait(command, cwd=twpath)

################################################################################
def compile_psutil():
   logprint('Installing psutil')

   if glob.glob(PYSITEPKGS + '/psutil*'):
      logprint('Psutil already installed')
   else:
      command = 'python -s setup.py --no-user-cfg install --force --verbose'
      psPath = unpack(tarfilesToDL['psutil'])
      execAndWait(command, cwd=psPath)

################################################################################
def compile_appnope():
   logprint('Installing appnope')

   if glob.glob(PYSITEPKGS + '/appnope*'):
      logprint('appnope already installed')
   else:
      command = 'python -s setup.py --no-user-cfg install --force --verbose'
      appnopePath = unpack(tarfilesToDL['appnope'])
      execAndWait(command, cwd=appnopePath)

################################################################################
def compile_armory():
   logprint('Compiling and installing Armory')
   # Always compile - even if already in app
   #os.chdir('..') # Leave workspace directory.
   pypathpath = path.join(ARMORYDIR, 'cppForSwig/pypaths.txt')
   logprint('Writing ' + pypathpath)
   with open(pypathpath, 'w') as f:
      f.write(pypathData)

   armoryAppScript = path.join(APPDIR, 'Contents/MacOS/Armory')
   armorydAppScript = path.join(APPDIR, 'Contents/MacOS/armoryd')
   pydir = path.join(APPDIR, 'Contents/MacOS/py')
   currentDir = os.getcwd()
   os.chdir("..")
   execAndWait('python update_version.py')
   os.chdir(currentDir)
   execAndWait('make all', cwd='..')
   execAndWait('make DESTDIR="%s" install' % pydir, cwd='..')
   copyfile('Armory-script.sh', armoryAppScript)
   copyfile('armoryd-script.sh', armorydAppScript)
   execAndWait('chmod +x "%s"' % armoryAppScript)
   execAndWait('chmod +x "%s"' % armorydAppScript)

################################################################################
def compile_objc_library():
   logprint('Compiling and installing the Armory Objective-C shared library')

   # Execute SIP to create the Python/Obj-C++ glue code, use qmake to create the
   # Makefile, and make the shared library. Be sure to keep the SIP flags in
   # sync with generate_sip_module_code() from PyQt's configure-ng.py.
   sipFlags = '-w -x VendorID -t WS_MACX -t Qt_4_8_6 -x Py_v3 -B Qt_5_0_0 -o ' \
              '-P -g -c . -I ../workspace/unpackandbuild/PyQt-mac-gpl-%s/sip' % pyQtVer
   execAndWait('../workspace/unpackandbuild/sip-%s/sipgen/sip %s ./ArmoryMac.sip' % (sipVer, sipFlags), cwd=OBJCDIR)
   execAndWait('../workspace/unpackandbuild/qt-everywhere-opensource-src-%s/bin/qmake ArmoryMac.pro' % qtVer, cwd=OBJCDIR)
   # For some reason, qmake mangles LFLAGS when LFLAGS is built. The exact cause
   # is unknown but probably has to do with a conf file included in
   # mkspecs/unsupported/macx-clang-libc++/qmake.conf. Patch the output for now.
   execAndWait('patch -p0 < %s' % path.join(os.getcwd(), 'qmake_LFLAGS.patch'), \
               cwd=OBJCDIR)
   execAndWait('make', cwd=OBJCDIR)


################################################################################
def make_resources():
   "Populate the Resources folder."
   cont = path.join(APPDIR, 'Contents')
   copyfile('Info.plist', cont)

   icnsArm = '../img/armory_icon_fullres.icns'
   icnsRes  = path.join(cont,  'Resources/Icon.icns')
   copyfile(icnsArm, icnsRes)
   
################################################################################
#def unzip_swig():
#   '''Unzip the SWIG binary.'''
#   logprint('Unzipping the SWIG binary.')
#   swigDir = unpack(tarfilesToDL['swig'])

################################################################################
def cleanup_app():
   "Try to remove as much unnecessary junk as possible."
   show_app_size()
   print "Removing Python test-suite."
   testdir = path.join(PYPREFIX, "lib/python%s/test" % pyMajorVer)
   if path.exists(testdir):
      removetree(testdir)
   print "Removing .pyo and unneeded .py files."
   remove_python_files(PYPREFIX)
   remove_python_files(path.join(APPDIR, 'Contents/MacOS/py'), False)
   show_app_size()

################################################################################
def make_targz():
   ver = getVersionStr()
   execAndWait('tar -zcf ../armory_%s_osx.tar.gz Armory.app' % ver, cwd=WORKDIR)

################################################################################
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


################################################################################
def show_app_size():
   "Show the size of the app."
   logprint("Size of application: ")
   sys.stdout.flush()
   execAndWait('du -hs "%s"' % APPDIR)

################################################################################
def remove_python_files(top, removePy=True):
   """Remove .pyo files and, if desired, any .py files where the .pyc file
      exists."""
   n_pyo = 0
   n_py_rem = 0
   n_py_kept = 0
   for (dirname, dirs, files) in os.walk(top):
      for f in files:
         prename, ext = path.splitext(f)
         if ext == '.pyo':
            removefile(path.join(dirname, f))
            n_pyo += 1
         elif ext == '.py':
            if removePy:
               if (f + 'c') in files:
                  removefile(path.join(dirname, f))
                  n_py_rem += 1
               else:
                  n_py_kept += 1
            else:
               if (f + 'c') in files:
                  removefile(path.join(dirname, (f + 'c')))
               n_py_kept += 1
   logprint("Removes %i .py files (kept %i)." % (n_py_rem, n_py_kept))

################################################################################
def delete_prev_data(opts):
   # If we ran this before, we should have a qt dir here
   prevQtDir = path.join(UNPACKDIR, 'qt')

   def resetQtRepo():
      if path.exists(prevQtDir):
         makefile = path.join(prevQtDir, 'Makefile')
         if path.exists(makefile):
            execAndWait('make clean', cwd=prevQtDir)
            removefile(makefile)
         removefile(QTBUILTFLAG)
   
   # Always remove previously-built application files
   removetree(APPDIR)
   removetree(INSTALLDIR)
   
   # When building from scratch 
   if opts.fromscratch:
      removetree(UNPACKDIR)  # Clear all unpacked tar files
      removetree(DLDIR)      # Clear even the downloaded files
   elif opts.rebuildall:
      removetree(UNPACKDIR)
   elif not opts.qtcheckout == '4.8':
      resetQtRepo()
      execAndWait('git pull')
      execAndWait('git checkout %s' % opts.qtcheckout)
   elif opts.qtupdate:
      resetQtRepo()
      execAndWait('git pull')
   elif opts.qtrebuild:
      resetQtRepo()
   else:
      logprint('Using all packages previously downloaded and built')

################################################################################
if __name__ == "__main__":
   main()   
