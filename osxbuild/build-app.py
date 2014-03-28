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

# Set some constants up front
#swigBinVer = '2.0.12'
pythonVer  = '2.7.5'
setToolVer = '2.1.2'
pipVer     = '1.5.2'
psutilVer  = '1.2.1'
twistedVer = '13.2.0'
libpngVer  = '1.6.8'
qtVer      = '4.8.5'
sipVer     = '4.15.4'
pyQtVer    = '4.10.4'
LOGFILE    = 'build-app.log.txt'
LOGPATH    = path.abspath( path.join(os.getcwd(), LOGFILE))
ARMORYDIR  = '..'
WORKDIR    = path.join(os.getcwd(), 'workspace')
APPDIR     = path.join(WORKDIR, 'Armory.app') # actually make it local
DLDIR      = path.join(WORKDIR, 'downloads')
UNPACKDIR  = path.join(WORKDIR, 'unpackandbuild')
#SWIGDIR    = path.join(UNPACKDIR, 'swig', swigBinVer)
INSTALLDIR = path.join(WORKDIR, 'install')
PYPREFIX   = path.join(APPDIR, 'Contents/Frameworks/Python.framework/Versions/2.7')
PYSITEPKGS = path.join(PYPREFIX, 'lib/python2.7/site-packages')
MAKEFLAGS  = '-j4'

QTBUILTFLAG = path.join(UNPACKDIR, 'qt/qt_install_success.txt')

#pypath_txt_template=""" PYTHON_INCLUDE=%s/include/python2.7/ PYTHON_LIB=%s/lib/python2.7/config/libpython2.7.a PYVER=python2.7 """
pypathData  =   'PYTHON_INCLUDE=%s/include/python2.7/' % PYPREFIX
pypathData += '\nPYTHON_LIB=%s/lib/python2.7/config/libpython2.7.a' % PYPREFIX
pypathData += '\nPYTHON_LIB_DIR=%s/lib/python2.7/config/' % PYPREFIX
pypathData += '\nPYVER=python2.7'

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
      # Skip download Qt-git if downloading Qt, and vice versa
      logprint('\n\n')
      if((pkgname.lower()=='qt-git' and     CLIOPTS.precompiledQt) or \
         (pkgname.lower()=='qt'     and not CLIOPTS.precompiledQt)     ):
         continue
      downloadPkg(pkgname, fname, url, ID)

   logprint("\n\nALL DOWNLOADS COMPLETED.\n\n")
   
   make_empty_app()
   compile_python()
   compile_pip()
   install_libpng()
   install_qt()
   compile_sip()
   compile_pyqt()
   compile_twisted()
   compile_psutil()
   #unzip_swig()
   compile_armory()
   make_resources()
   cleanup_app()
   # Force Finder to update the Icon
   execAndWait("touch " + APPDIR)

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

   # Use tarfile module to pick out the base dir u
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
                    "Python-%s.tar.bz2" % pythonVer, \
                    "http://python.org/ftp/python/%s/Python-%s.tar.bz2" % (pythonVer, pythonVer), \
                    "6cfada1a739544a6fa7f2601b500fba02229656b" ] )

distfiles.append( [ 'setuptools', \
                    "setuptools-%s.tar.gz" % setToolVer, \
                    "https://pypi.python.org/packages/source/s/setuptools/setuptools-%s.tar.gz" % setToolVer, \
                    "6a35e881a3aa2e06a1d5d4e966a9def296ec23e8" ] )

distfiles.append( [ 'Pip', \
                    "pip-%s.tar.gz" % pipVer, \
                    "https://pypi.python.org/packages/source/p/pip/pip-%s.tar.gz" % pipVer, \
                    "4f43a6b04f83b8d83bee702750ff35be2a2b6af1" ] )

distfiles.append( [ "psutil", \
                    "psutil-%s.tar.gz" % psutilVer, \
                    "https://pypi.python.org/packages/source/p/psutil/psutil-%s.tar.gz" % psutilVer, \
                    "c8c1842bf1c63b9068ac25a37f7aae11fcecd57f" ] )

distfiles.append( [ 'Twisted', \
                    "Twisted-%s.tar.bz2" % twistedVer, \
                    "https://pypi.python.org/packages/source/T/Twisted/Twisted-%s.tar.bz2" % twistedVer, \
                    "e1d43645fd3d84dc2867f36b60d2e469a71eb01d" ] )

# Other lines rely on the given version. Patch this up later.
distfiles.append( [ 'libpng', \
                    "libpng-%s.mavericks.bottle.tar.gz" % libpngVer, \
                    "https://downloads.sf.net/project/machomebrew/Bottles/libpng-%s.mavericks.bottle.tar.gz" % libpngVer, \
                    "666d5ba290d72b0cfa13366232eb0ffcc701d21f" ] )

#distfiles.append( [ "Qt", \
                    #"qt-4.8.5.mountain_lion.bottle.2.tar.gz", \
                    #"https://downloads.sf.net/project/machomebrew/Bottles/qt-4.8.5.mountain_lion.bottle.2.tar.gz", \
                    #"b361f521d413409c0e4397f2fc597c965ca44e56" #] )

#distfiles.append( [ "Qt", \
#                    "qt-everywhere-opensource-src-5.2.1.tar.gz", \
#                    "http://download.qt-project.org/official_releases/qt/5.2/5.2.1/single/qt-everywhere-opensource-src-5.2.1.tar.gz", \
#                    "31a5cf175bb94dbde3b52780d3be802cbeb19d65" ] )

# Pre-packaged source not used for now. Use Git instead.
distfiles.append( [ "Qt", \
                    "qt-everywhere-opensource-src-%s.tar.gz" % qtVer, \
                    "http://download.qt-project.org/official_releases/qt/4.8/%s/qt-everywhere-opensource-src-%s.tar.gz" % (qtVer, qtVer), \
                    "745f9ebf091696c0d5403ce691dc28c039d77b9e" ] )

#distfiles.append( [ "Qt-git", \
#                    "qt5_git_repo.tar.gz", \
#                    'git://gitorious.org/qt/qt5.git',
#                    'stable' ] )

distfiles.append( [ "Qt-git", \
                    "qt4_git_repo.tar.gz", \
                    'git://gitorious.org/qt/qt.git',
                    '4.8' ] )

distfiles.append( [ "Webkit-for-Qt", \
                    "libWebKitSystemInterfaceMavericks.a", \
                    "http://trac.webkit.org/export/162166/trunk/WebKitLibraries/libWebKitSystemInterfaceMavericks.a", \
                    "bb071fb69cad0cec1f2ecb082ee34f44bd76ac93" ] )

#distfiles.append( [ "Qt-p1", \
                    #"Ie9a72e3b.patch", \
                    #'https://gist.github.com/cliffrowley/f526019bb3182c237836/raw/459bfcfe340baa306eed81720b0734f4bede94d7/Ie9a72e3b.patch', \
                    #'829a8e9644c143be11c03ee7b2b9c8b042708b41' #] )

#distfiles.append( [ 'Qt-p2', \
                    #'qt-4.8-libcpp.diff', \
                    #'https://gist.github.com/cliffrowley/7380124/raw/ff6c681b282bbc1fe4a58e2f0c37905062ebd58b/qt-4.8-libcpp.diff', \
                    #'4215caf4b8c84236f85093a1f0d24739a1c5ccfd' #] )

#distfiles.append( [ 'Qt-p3', \
                    #'qt-4.8-libcpp-configure.diff', \
                    #'https://gist.github.com/cliffrowley/93ce53b9dd8d8bb65530/raw/d3f6a6f039c5826df04fcfa56569394ea5069b9e/qt-4.8-libcpp-configure.diff', \
                    #'a0b5189097937410113f22b78579c4eac940def9' #] )

distfiles.append( [ "sip", \
                    "sip-%s.tar.gz" % sipVer, \
                    "http://sourceforge.net/projects/pyqt/files/sip/sip-%s/sip-%s.tar.gz" % (sipVer, sipVer), \
                    'a5f6342dbb3cdc1fb61440ee8acb805f5fec3c41' ] )

# Other lines rely on the given version. Patch this up later.
distfiles.append( [ "pyqt", \
                    "PyQt-mac-gpl-%s.tar.gz" % pyQtVer, \
                    "http://downloads.sf.net/project/pyqt/PyQt4/PyQt-%s/PyQt-mac-gpl-%s.tar.gz" % (pyQtVer, pyQtVer), \
                    'ba5465f92fb43c9f0a5b948fa25df5045f160bf0' ] )

#distfiles.append( [ "pyqt", \
#                    "PyQt-gpl-5.2.tar.gz", \
#                    "http://downloads.sf.net/project/pyqt/PyQt5/PyQt-5.2/PyQt-gpl-5.2.tar.gz", \
#                    'a1c232d34ab268587c127ad3097c725ee1a70cf0' ] )

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
   pyexe = path.join(APPDIR, 'Contents/MacOS/Python')

   # make install
   srcDir = path.join(INSTALLDIR, 'Build Applet.app/Contents/MacOS/Python')
   dstDir = path.join(APPDIR, 'Contents/MacOS')
   execAndWait('make install PYTHONAPPSDIR=%s' % INSTALLDIR, cwd=bldPath)
   execAndWait('cp -p "%s" %s' % (srcDir, dstDir), cwd=bldPath)

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
   qtBuildDir = path.join(UNPACKDIR, 'qt')
   qtInstDir  = path.join(INSTALLDIR, 'qt')
   qtTarFile   = path.join(DLDIR, 'qt4_git_repo.tar.gz')
#   qtTarFile   = path.join(DLDIR, 'qt5_git_repo.tar.gz')

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
      logprint('Unpacking qt repo from tarfile')
      logprint('Remove qt4_git_repo.tar.gz to re-clone HEAD')
#      logprint('Remove qt5_git_repo.tar.gz to re-clone HEAD')
      gitdir = unpack(tarfilesToDL['Qt-git'])
   elif not path.exists(qtTarFile):
      logprint('Tarring downloaded repo for future use')
      execAndWait('tar -zcf %s qt' % qtTarFile, cwd=UNPACKDIR)

   # Webkit-for-Qt is not a tar archive, it's actually just a single .a file
   webkita = tarfilesToDL['Webkit-for-Qt']
   src = path.join(DLDIR, webkita)
   dst = path.join(qtBuildDir, 'src/3rdparty/webkit/WebKitLibraries', webkita)
   copyfile(src, dst)
   #for patch in ['Qt-p1', 'Qt-p2', 'Qt-p3']:
   #   execAndWait('patch -p1 < ../../downloads/' + tarfilesToDL[patch], cwd=qtBuildDir)
   #execAndWait('patch -p1 < ../../../qt-maverick-stability.patch', cwd=qtBuildDir)

   ##### Configure
   command  = './configure -prefix "%s" -system-zlib -confirm-license -opensource ' 
   command += '-nomake demos -nomake examples -nomake docs -cocoa -fast -release '
   command += '-no-qt3support -arch x86_64 -no-3dnow ' 
   command += '-platform unsupported/macx-clang' 
   execAndWait(command % qtInstDir, cwd=qtBuildDir)

   ##### Make
   execAndWait('make %s' % MAKEFLAGS, cwd=qtBuildDir)

   ##### Make Install
   # This will actually happen outside this function, since the INSTALLDIR
   # Gets wiped every build

################################################################################
def install_qt():
   if CLIOPTS.precompiledQt:
      logprint('Unpacking precompiled Qt.')
      qtdir = unpack(tarfilesToDL['Qt'])
      raise RuntimeError('Using precompiled Qt is not supported, yet')
   else:
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
      qtBuildDir = path.join(UNPACKDIR, 'qt')

      qtconf = path.join(qtBinDir, 'qt.conf')
      execAndWait('make install', cwd=qtBuildDir)

      newcwd = path.join(APPDIR, 'Contents/Frameworks')
      for mod in ['QtCore', 'QtGui', 'QtXml', 'QtNetwork']:
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
   
      frmpath = path.join(APPDIR, 'Contents/Frameworks')
      os.environ['PATH'] = '%s:%s' % (qtBinDir, os.environ['PATH'])
      os.environ['DYLD_FRAMEWORK_PATH'] = '%s:%s' % (frmpath, old)
      os.environ['QTDIR'] = qtInstDir
      os.environ['QMAKESPEC'] = path.join(os.environ['QTDIR'], 'mkspecs/macx-g++')
      logprint('All the following ENV vars are now set:')
      for var in ['PATH','DYLD_FRAMEWORK_PATH', 'QTDIR', 'QMAKESPEC']:
         logprint('   %s: \n      %s' % (var, os.environ[var]))

################################################################################
def compile_sip():
   logprint('Installing sip')
   if path.exists(path.join(PYSITEPKGS, 'sip.so')):
      logprint('Sip is already installed.')
   else:
      #os.chdir('build/sip-4.14.6')
      sipPath = unpack(tarfilesToDL['sip'])
      command  = 'python configure.py'
      command += ' --destdir="%s"' % PYSITEPKGS
      command += ' --bindir="%s/bin"' % PYPREFIX
      command += ' --incdir="%s/include"' % PYPREFIX
      command += ' --sipdir="%s/share/sip"' % PYPREFIX
      execAndWait(command, cwd=sipPath)
      execAndWait('make', cwd=sipPath)

   # Must run "make install" again even if it was previously built (since
   # the APPDIR and INSTALLDIR are wiped every time the script is run)
   execAndWait('make install', cwd=sipPath)
      
################################################################################
def compile_pyqt():
   logprint('Install PyQt4')
#   logprint('Install PyQt5')
#   if path.exists(path.join(PYSITEPKGS, 'PyQt5')):
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
def compile_psutil():
   logprint('Installing psutil')

   if glob.glob(PYSITEPKGS + '/psutil*'):
      logprint('Psutil already installed')
   else:
      command = 'python -s setup.py --no-user-cfg install --force --verbose'
      psPath = unpack(tarfilesToDL['psutil'])
      execAndWait(command, cwd=psPath)

################################################################################
def compile_armory():
   logprint('Compiling and installing Armory')
   # Always compile - even if already in app
   #os.chdir('..') # Leave workspace directory.
   pypathpath = path.join(ARMORYDIR, 'cppForSwig/pypaths.txt')
   logprint('Writing ' + pypathpath)
   with open(pypathpath, 'w') as f:
      f.write(pypathData)

   appscript = path.join(APPDIR, 'Contents/MacOS/Armory')
   pydir = path.join(APPDIR, 'Contents/MacOS/py')
   execAndWait('make all', cwd='..')
   execAndWait('make DESTDIR="%s" install' % pydir, cwd='..')
   copyfile('Armory-script.sh', appscript)
   execAndWait('chmod +x "%s"' % appscript)

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
   testdir = path.join(PYPREFIX, "lib/python2.7/test")
   if path.exists(testdir):
      removetree(testdir)
   print "Removing .pyo and unneeded .py files."
   remove_python_files(PYPREFIX)
   remove_python_files(path.join(APPDIR, 'Contents/MacOS/py'))
   show_app_size()

################################################################################
def show_app_size():
   "Show the size of the app."
   logprint("Size of application: ")
   sys.stdout.flush()
   execAndWait('du -hs "%s"' % APPDIR)

################################################################################
def remove_python_files(top):
   "Remove .pyo files and any .py files where the .pyc file exists."
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
            if (f + 'c') in files:
               removefile(path.join(dirname, f))
               n_py_rem += 1
            else:
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
