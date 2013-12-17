#!/usr/env python
"""Build Armory as a Mac OS X Application."""

import os
from os import path
import sys
import hashlib
import shutil
import glob
import time
import optparse
import tarfile

from subprocess import Popen, PIPE

# Set some constants up front
LOGFILE    = 'build-app.log.txt'
LOGPATH    = path.abspath( path.join(os.getcwd(), LOGFILE))
ARMORYDIR  = '..'
WORKDIR    = path.join(os.getcwd(), 'workspace')
APPDIR     = path.join(WORKDIR, 'Armory.app') # actually make it local
DLDIR      = path.join(WORKDIR, 'downloads')
UNPACKDIR  = path.join(WORKDIR, 'unpackandbuild')
INSTALLDIR = path.join(WORKDIR, 'install')
PYPREFIX   = path.join(APPDIR, 'Contents/Frameworks/Python.framework/Versions/2.7')
PYSITEPKGS = path.join(PYPREFIX, 'lib/python2.7/site-packages')
MAKEFLAGS  = '-j4'

#pypath_txt_template=""" PYTHON_INCLUDE=%s/include/python2.7/ PYTHON_LIB=%s/lib/python2.7/config/libpython2.7.a PYVER=python2.7 """
pypathData  = 'PYTHON_INCLUDE=%s/include/python2.7/' % PYPREFIX
pypathData += 'PYTHON_LIB=%s/lib/python2.7/config/libpython2.7.a' % PYPREFIX
pypathData += 'PYVER=python2.7'


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
   compile_armory()
   make_ressources()
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

def execAndWait(syscmd, cwd=None):
   try:
      syscmd += ' 2>&1 | tee -a %s' % LOGPATH
      logprint('*'*80)
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
      if path.exists(clonedir):
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
                    "Python-2.7.5.tar.bz2", \
                    "http://python.org/ftp/python/2.7.5/Python-2.7.5.tar.bz2", \
                    "6cfada1a739544a6fa7f2601b500fba02229656b" ] )

distfiles.append( [ 'setuptools', \
                    "setuptools-1.1.4.tar.gz", \
                    "https://pypi.python.org/packages/source/s/setuptools/setuptools-1.1.4.tar.gz", \
                    "b8bf9c2b8a114045598f0e16681d6a63a4d6cdf9" ] )

distfiles.append( [ 'Pip', \
                    "pip-1.4.1.tar.gz", \
                    "https://pypi.python.org/packages/source/p/pip/pip-1.4.1.tar.gz", \
                    "9766254c7909af6d04739b4a7732cc29e9a48cb0" ] )

distfiles.append( [ "psutil", \
                    "psutil-1.0.1.tar.gz", \
                    "http://psutil.googlecode.com/files/psutil-1.0.1.tar.gz", \
                    "3d3abb8b7a5479b7299a8d170ec25179410f24d1" ] )

distfiles.append( [ 'Twisted', \
                    "Twisted-13.1.0.tar.bz2", \
                    "https://pypi.python.org/packages/source/T/Twisted/Twisted-13.1.0.tar.bz2", \
                    "7f6e07b8098b248157ac26378fafa9e018f279a7" ] )

distfiles.append( [ 'libpng', \
                    "libpng-1.5.14.mountain_lion.bottle.tar.gz", \
                    "https://downloads.sf.net/project/machomebrew/Bottles/libpng-1.5.14.mountain_lion.bottle.tar.gz", \
                    "5e7feb640d654df0c2ac072d86e46ce9df9eaeee" ] )

#distfiles.append( [ "Qt", \
                    #"qt-4.8.5.mountain_lion.bottle.2.tar.gz", \
                    #"https://downloads.sf.net/project/machomebrew/Bottles/qt-4.8.5.mountain_lion.bottle.2.tar.gz", \
                    #"b361f521d413409c0e4397f2fc597c965ca44e56" #] )

distfiles.append( [ "Qt", \
                    "qt-everywhere-opensource-src-4.8.5.tar.gz", \
                    "http://download.qt-project.org/official_releases/qt/4.8/4.8.5/qt-everywhere-opensource-src-4.8.5.tar.gz", \
                    "745f9ebf091696c0d5403ce691dc28c039d77b9e" ] )

distfiles.append( [ "Qt-git", \
                    "qt4_git_repo.tar.gz", \
                    'git://gitorious.org/qt/qt.git',
                    '4.8' ] )

distfiles.append( [ "Webkit-for-Qt", \
                    "libWebKitSystemInterfaceMavericks.a", \
                    "http://trac.webkit.org/export/157771/trunk/WebKitLibraries/libWebKitSystemInterfaceMavericks.a", \
                    "fc5ebf85f637f9da9a68692df350e441c8ef5d7e" ] )

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
                    "sip-4.14.6.tar.gz", \
                    "http://download.sf.net/project/pyqt/sip/sip-4.14.6/sip-4.14.6.tar.gz", \
                    'e9dfe98ab1418914c78fd3ac457a4e724aac9821' ] )

distfiles.append( [ "pyqt", \
                    "PyQt-mac-gpl-4.10.1.tar.gz", \
                    "http://downloads.sf.net/project/pyqt/PyQt4/PyQt-4.10.1/PyQt-mac-gpl-4.10.1.tar.gz", \
                    'cf20699c4db8d3031c19dd51df8857bba1a4956b' ] )



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
   dylib = 'libpng15.15.dylib'
   target = path.join(APPDIR, 'Contents/Dependencies', dylib)
   if path.exists(target):
      logprint('libpng already installed.')
   else:
      pngDir = unpack(tarfilesToDL['libpng'])
      src = path.join(pngDir, '1.5.14/lib', dylib)
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
   qtTarFileDL   = path.join(UNPACKDIR, 'qt4_git_repo.tar.gz')
   qtTarFileBld  = path.join(DLDIR, 'qt4_git_repo.tar.gz')

   # If we did a fresh download, it's already uncompressed in DLDir.  Move it
   # to where it should be in the UNPACKDIR
   if path.exists(qtDLDir):
      if path.exists(qtBuildDir):
         removetree(qtBuildDir)
      movepath(qtDLDir, qtBuildDir)


   # If 
   if not path.exists(qtBuildDir):
      if not path.exists(qtTarFileDL):
         raise RuntimeError('*** ERROR: No cloned repo and no tar file...? ***')
      logprint('Unpacking qt repo from tarfile')
      logprint('Remove qt4_git_repo.tar.gz to re-clone HEAD')
      gitdir = unpack(tarfilesToDL['Qt-git'])
   elif not path.exists(qtTarFileDL):
      logprint('Tarring downloaded repo for future use')
      execAndWait('tar -zcf qt4_git_repo.tar.gz qt', cwd=DLDIR)
      movepath(qtTarFileBld, qtTarFileDL)

      #unpack(tarfilesToDL['Qt'])
      webkita = tarfilesToDL['Webkit-for-Qt']
      src = path.join(DLDIR, webkita)
      dst = path.join(qtBuildDir, 'src/3rdparty/webkit/WebKitLibraries', webkita)
      copyfile(src, dst)
      #for patch in ['Qt-p1', 'Qt-p2', 'Qt-p3']:
      #   execAndWait('patch -p1 < ../../downloads/' + tarfilesToDL[patch], cwd=qtBuildDir)
      execAndWait('patch -p1 < ../../../qt-maverick-stability.patch', cwd=qtBuildDir)

   ##### Configure
   command  = './configure -prefix "%s" -system-zlib -confirm-license -opensource ' 
   command += '-nomake demos -nomake examples -nomake docs -cocoa -fast -release '
   command += '-no-qt3support -arch x86_64 -no-3dnow ' 
   command += '-platform unsupported/macx-clang' 
   execAndWait(command % qtInstDir, cwd=qtBuildDir)

   ##### Make
   execAndWait('make %s' % MAKEFLAGS, cwd=qtBuildDir)

   ##### Make Install
   execAndWait('make install', cwd=qtBuildDir)

   newcwd = path.join(APPDIR, 'Contents/Frameworks')
   #os.chdir(path.join(APPDIR, 'Contents/Frameworks'))
   for f in ['QtCore', 'QtGui', 'QtXml']:
      src = path.join(qtInstDir, 'lib', f+'.framework')
      dst = path.join(APPDIR, 'Contents/Frameworks', f+'.framework')
      if path.exists(dst):
         removetree(dst)
      copytree(src, dst)

   #os.chdir(olddir)
   qtBinDir = path.join(APPDIR, 'qt/bin')
   fname = path.join(qtBinDir, 'qt.conf')
   with open(fname, 'w') as f:
      f.write('[Paths]\nPrefix = %s' % qtdir)

   # Put Qt stuff on the path
   os.environ['PATH'] = '%s:%s' % (qtBinDir, os.environ['PATH'])

   try:
      old = ':'+os.environ['DYLD_FRAMEWORK_PATH']
   except KeyError:
      old = ''

   os.environ['DYLD_FRAMEWORK_PATH'] = '%s:%s' % (path.join(APPDIR, 'Contents/Frameworks'), old)
   os.environ['QTDIR'] = qtdir
   os.environ['QMAKESPEC'] = path.join(os.environ['QTDIR'], 'mkspecs/macx-g++')
   logprint('All the following ENV vars are now set:')
   for var in ['PATH','DYLD_FRAMEWORK_PATH', 'QTDIR', 'QMAKESPEC']:
      logprint('   %s: \n      %s' % (var, os.environ[var]))



################################################################################
def install_qt():
   if CLIOPTS.precompiledQt:
      logprint('Unpacking precompiled Qt.')
      qtdir = unpack(tarfilesToDL['Qt'])
      # not sure what else to do with precompiled version, yet
   else:
      compile_qt()
      
      
      
      

   

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
      system('make', cwd=sipPath)
      system('make install', cwd=sipPath)
      
################################################################################
def compile_pyqt():
   logprint('Install pyqt (needed by pyqt).')
   if path.exists(path.join(PYSITEPKGS, 'PyQt4')):
      logprint('Pyqt is already installed.')
   else:
      pyqtPath = unpack(tarfilesToDL['pyqt'])
      #os.chdir('build/PyQt-mac-gpl-4.10.1')
      incDir = path.join(PYPREFIX, 'include')
      execAndWait('python ./configure-ng.py --confirm-license --sip-incdir="%s"' % incDir, cwd=pyqtPath)
      execAndWait('make %s' % MAKEFLAGS, cwd=pyqtPath)
      execAndWait('make install', cwd=pyqtPath)

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
      system("pip install %s > pip-%s.log 2>&1" % (package, package))
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
   pypathpath = path.join('cppForSwig/pypaths.txt')
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
def make_ressources():
   "Populate the Resources folder."
   cont = path.join(APPDIR, 'Contents')
   icnsArm = path.join(cont,  'MacOS/py/usr/share/armory/img/armory_icon_fullres.icns')
   icnsRes  = path.join(cont,  'Resources/Icon.icns')
   copyfile('Info.plist', cont)
   copyfile(icnsArm, icnsRes)
   #system("cd '%s' && cp ../MacOS/py/usr/share/armory/img/armory_icon_fullres.icns Icon.icns" % (res,))
   
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
   out,err = execAndWait('du -hs "%s"' % APPDIR)
   

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
         removefile(path.join(prevQtDir, 'configured-success.txt'))
         removefile(path.join(prevQtDir, 'make-success.txt'))
         removefile(path.join(prevQtDir, 'make-install-success.txt'))
      
   
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

      



if __name__ == "__main__":
   main()   


