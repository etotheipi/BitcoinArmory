#!/usr/env python
"""Build Armory as a Mac OS X Application."""

import os
import sys
import hashlib
import shutil
import glob

# Name of app
appname = "Armory.app"

# Where will this script do its work?
workdir = os.path.join(os.getcwd(), "workspace")

# Option to make to build in parallel
parallel = "-j7"

# Enable debugging ???
# os.environ['CFLAGS'] = '-g -O1'
# os.environ['CXXFLAGS'] = '-g -O1'

# List of all files needed to download.  Each item is
# (Name, filename, url, sha-1 or None)
distfiles = [
    ['Python', "Python-2.7.5.tar.bz2" , "http://python.org/ftp/python/2.7.5/Python-2.7.5.tar.bz2", "6cfada1a739544a6fa7f2601b500fba02229656b"],
    ['setuptools', "setuptools-1.1.4.tar.gz", "https://pypi.python.org/packages/source/s/setuptools/setuptools-1.1.4.tar.gz", "b8bf9c2b8a114045598f0e16681d6a63a4d6cdf9"],
    ['Pip', "pip-1.4.1.tar.gz", "https://pypi.python.org/packages/source/p/pip/pip-1.4.1.tar.gz", "9766254c7909af6d04739b4a7732cc29e9a48cb0"],
    ["psutil", "psutil-1.0.1.tar.gz", "http://psutil.googlecode.com/files/psutil-1.0.1.tar.gz", None],
    ['Twisted', "Twisted-13.1.0.tar.bz2", "https://pypi.python.org/packages/source/T/Twisted/Twisted-13.1.0.tar.bz2", "7f6e07b8098b248157ac26378fafa9e018f279a7"],
    ['libpng', "libpng-1.5.14.mountain_lion.bottle.tar.gz", "https://downloads.sf.net/project/machomebrew/Bottles/libpng-1.5.14.mountain_lion.bottle.tar.gz", "5e7feb640d654df0c2ac072d86e46ce9df9eaeee"],
    ["Qt", "qt-4.8.5.mountain_lion.bottle.2.tar.gz", "https://downloads.sf.net/project/machomebrew/Bottles/qt-4.8.5.mountain_lion.bottle.2.tar.gz", "b361f521d413409c0e4397f2fc597c965ca44e56"],
    ["sip", "sip-4.14.6.tar.gz", "http://download.sf.net/project/pyqt/sip/sip-4.14.6/sip-4.14.6.tar.gz", 'e9dfe98ab1418914c78fd3ac457a4e724aac9821'],
    ["pyqt", "PyQt-mac-gpl-4.10.1.tar.gz", "http://downloads.sf.net/project/pyqt/PyQt4/PyQt-4.10.1/PyQt-mac-gpl-4.10.1.tar.gz", 'cf20699c4db8d3031c19dd51df8857bba1a4956b'],
]

pypath_txt_template="""PYTHON_INCLUDE=%s/include/python2.7/
PYTHON_LIB=%s/lib/python2.7/config/libpython2.7.a
PYVER=python2.7
"""

#Where Homebrew stores stuff.  Not needed, but can save downloading time.
homebrew_cache = "/Library/Caches/Homebrew"

# Python's prefix inside the App (for installing stuff)
pyprefix = os.path.join(workdir, appname, "Contents/Frameworks/Python.framework/Versions/2.7/")
pysitepackages = os.path.join(pyprefix, "lib/python2.7/site-packages")

# Subdirectories under workdir
dl = 'downloads'

# Now repack the information in distfiles
tarfile = {}
for d in distfiles:
    tarfile[d[0]] = d[1]

qtconf = """
[Paths]
Prefix = %s
"""
    
def main():
    makedir(workdir)
    os.chdir(workdir)
    download_all()
    makedir('build')
    makedir('tmp')
    make_empty_app()
    compile_python()
    compile_pip()
    install_libpng()
    install_qt()
    compile_sip()
    compile_pyqt()
    # Strangely pip and easy_install fail to install psutil the right place, and place it in
    # /usr/local (!).  Try avoing pip.
    #pip_install("twisted", "twisted")
    #pip_install("psutil", "psutil")
    compile_twisted()
    compile_psutil()
    compile_armory()
    make_ressources()
    cleanup_app()

def makedir(dir):
    "Creates a subdirectory if it is not there."
    if not os.path.isdir(dir):
        print "Creating directory", dir
        os.mkdir(dir)

def download_all():
    "Download all distribution files - or grab them from Homebrew."
    makedir(dl)
    for n, f, u, s in distfiles:
        myfile = os.path.join(dl, f)
        hbfile = os.path.join(homebrew_cache, f)
        if os.path.exists(myfile):
            # Already there, check sha1
            check_sha(myfile, s)
        elif os.path.exists(hbfile):
            print "Found %s in Homebrew." % (f,)
            check_sha(hbfile, s)
            os.symlink(hbfile, myfile)
        else:
            system("cd '%s' && curl -OL '%s'" % (dl, u))
            check_sha(myfile, s)
    print "\n\nALL DOWNLOADS COMPLETED.\n\n"

def check_sha(f, sha):
    print "Checking", f,
    check = hashlib.sha1()
    check.update(open(f).read())
    digest = check.hexdigest()
    if sha is None:
        print "SHA-1 =", digest
    elif sha == digest:
        print "OK"
    else:
        raise RuntimeError("SHA Checksum failed for "+f)

def make_empty_app():
    "Make the empty .app bundle structure"
    makedir(appname)
    makedir(appname+"/Contents")
    makedir(appname+"/Contents/MacOS")
    makedir(appname+"/Contents/MacOS/py")
    makedir(appname+"/Contents/Frameworks")
    makedir(appname+"/Contents/Resources")
    makedir(appname+"/Contents/Dependencies")

def compile_python():
    "Install Python inside the app."
    #unpack("Python-2.7.5.tar.bz2", "Python-2.7.5")
    unpack(tarfile['Python'])
    os.chdir("build/Python-2.7.5")
    if os.path.exists('libpython2.7.a'):
        print "Python already compiled."
    else:
        # Configure and compile Python
        system("./configure --enable-ipv6 --prefix=%s --enable-framework='%s' > ../../python_configure.log"
               % (os.path.join(workdir, "tmp"),
                  os.path.join(workdir, appname, "Contents", "Frameworks")))
        system("make %s > ../../python_make.log 2>&1" % (parallel,))
    #Install Python into App.
    pyexe = "%s/%s/Contents/MacOS/Python" % (workdir, appname)
    if os.path.exists(pyexe):
        print "Python is already installed in the App"
    else:
        system("make install PYTHONAPPSDIR=%s > ../../python_install.log 2>&1"
               % (os.path.join(workdir, 'tmp'),))
        system("cp -p '%s/tmp/Build Applet.app/Contents/MacOS/Python' %s/%s/Contents/MacOS"
               % (workdir, workdir, appname))
    os.chdir("../..")
    # Make the new Python the default one
    os.environ['PATH'] = "%s:%s" % (os.path.join(workdir, appname, 
                                      "Contents/Frameworks/Python.framework/Versions/2.7/bin"),
                                    os.environ['PATH'])
    print "PATH is now", os.environ['PATH']
    
def unpack(tarfile, target=None):
    if target is None:
        if tarfile.endswith('.tar.gz'):
            target = tarfile[:-7]
        elif tarfile.endswith('.tar.bz2'):
            target = tarfile[:-8]
        else:
            raise RuntimeError("Cannot get basename of "+tarfile)
    if not os.path.exists(os.path.join("build", target)):
        system("cd build && tar xfz "+os.path.join('..', 'downloads', tarfile))

def system(cmd):
    print "SYSTEM:", cmd
    x = os.system(cmd)
    if x:
        raise RuntimeError("Command failed: "+cmd)

def compile_pip():
    "Installs pip in the newly built Python."
    pipexe = os.path.join(workdir, appname, 
                          "Contents/Frameworks/Python.framework/Versions/2.7/bin/pip")
    if os.path.exists(pipexe):
        print "Pip already installed"
    else:
        cmd = "python -s setup.py --no-user-cfg install --force --verbose"
        print "Installing setuptools."
        unpack(tarfile['setuptools'])
        system("cd build/setuptools-1.1.4 && ( %s > ../../setuptools-install.log 2>&1 ) " % (cmd,))
        print "Installing pip."
        unpack(tarfile['Pip'])
        system("cd build/pip-1.4.1 && ( %s > ../../pip-install.log 2>&1 ) " % (cmd,))

def install_libpng():
    target = os.path.join(workdir, appname, "Contents", "Dependencies", 
                          "libpng15.15.dylib")
    if os.path.exists(target):
        print "libpng already installed."
    else:
        print "Unpacking libpng."
        system("cd %s/tmp && tar xfz %s" 
               % (workdir, 
                  os.path.join('..', 'downloads', tarfile['libpng'])))
        print "Copying dylib into application"
        system("cp -p %s %s" 
               % (workdir + "/tmp/libpng/1.5.14/lib/libpng15.15.dylib", target))

def install_qt():
    if os.path.exists(os.path.join(workdir, appname, "Contents", "Dependencies", "qt")):
        print "Qt already installed."
    else:
        print "Unpacking Qt into application."
        system("cd %s/Contents/Dependencies && tar xfz %s" 
               % (appname, os.path.join('..', '..', '..', 'downloads', tarfile['Qt'])))
        print "Softlinking inside application"
        files = os.listdir(appname+"/Contents/Dependencies/qt/4.8.5/lib")
        olddir = os.getcwd()
        os.chdir(os.path.join(appname, "Contents", "Frameworks"))
        for f in ['QtCore', 'QtGui', 'QtXml']:
            system("ln -sf ../Dependencies/qt/4.8.5/lib/%s.framework" % (f,))
        os.chdir(olddir)
        fname = os.path.join(workdir, appname, "Contents/Dependencies/qt/4.8.5/bin/qt.conf")
        f = open(fname, "w")
        f.write(qtconf % (os.path.join(workdir, appname, "Contents/Dependencies/qt/4.8.5/"),))
        f.close()
    # Put Qt stuff on the path
    os.environ['PATH'] = "%s:%s" % (os.path.join(workdir, appname, 
                                      "Contents/Dependencies/qt/4.8.5/bin"),
                                    os.environ['PATH'])
    #print "PATH is now", os.environ['PATH']
    try:
        old = ":"+os.environ['DYLD_FRAMEWORK_PATH']
    except KeyError:
        old = ""
    os.environ['DYLD_FRAMEWORK_PATH'] = "%s:%s" % (os.path.join(workdir, appname, 
                                                                "Contents/Frameworks"), old)
    #print "DYLD_FRAMEWORK_PATH is now", os.environ['DYLD_FRAMEWORK_PATH']
    os.environ['QTDIR'] = os.path.join(workdir, appname, "Contents/Dependencies/qt/4.8.5/")
    os.environ['QMAKESPEC'] = os.path.join(os.environ['QTDIR'], "mkspecs/macx-g++")
    
def compile_sip():
    "Install sip (needed by pyqt)."
    unpack(tarfile['sip'])
    if os.path.exists(os.path.join(pysitepackages, "sip.so")):
        print "Sip is already installed."
    else:
        print "Installing sip."
        os.chdir("build/sip-4.14.6")
        system("python configure.py --destdir='%s' --bindir='%s/bin' --incdir='%s/include' --sipdir='%s/share/sip' > ../../sip-configure.log" 
               % (pysitepackages, pyprefix, pyprefix, pyprefix))
        system("make > ../../sip-make.log")
        system("make install >  ../../sip.make-install.log")
        os.chdir("../..")
        
def compile_pyqt():
    "Install pyqt (needed by pyqt)."
    unpack(tarfile['pyqt'])
    if os.path.exists(os.path.join(pysitepackages, "PyQt4")):
        print "Pyqt is already installed."
    else:
        print "Installing pyqt."
        os.chdir("build/PyQt-mac-gpl-4.10.1")
        system("python ./configure-ng.py --confirm-license --sip-incdir='%s' > ../../pyqt-configure.log 2>&1" 
               % (os.path.join(pyprefix, 'include')))
        system("make %s > ../../pyqt-make.log 2>&1" % (parallel,))
        system("make install >  ../../pyqt.make-install.log 2>&1")
        os.chdir("../..")

def pip_install(package, lookfor):
    """Install package with pip.

    For some reason this appears to be broken.  Pip installs psutil in /usr/local instead of
    inside the app.  Strange.  Do not use!
    """
    if os.path.exists(os.path.join(pysitepackages, lookfor)):
        print package, "already installed"
    else: 
        print "Installing %s using pip." % (package,)
        system("pip install %s > pip-%s.log 2>&1" % (package, package))

def compile_twisted():
    "Installs twisted in Python."
    if glob.glob(pysitepackages+"/Twisted*"):
        print "Twisted already installed"
    else:
        cmd = "python -s setup.py --no-user-cfg install --force --verbose"
        print "Installing Twisted."
        unpack(tarfile['Twisted'])
        system("cd build/Twisted-13.1.0 && ( %s > ../../twisted-install.log 2>&1 ) " % (cmd,))

def compile_psutil():
    "Installs psutil in Python."
    if glob.glob(pysitepackages+"/psutil*"):
        print "Psutil already installed"
    else:
        cmd = "python -s setup.py --no-user-cfg install --force --verbose"
        print "Installing Psutil."
        unpack(tarfile['psutil'])
        system("cd build/psutil-1.0.1 && ( %s > ../../psutil-install.log 2>&1 ) " % (cmd,))

def compile_armory():
    "Compiles and installs the main part of Armory."
    # Always compile - even if already in app
    os.chdir('..') # Leave workspace directory.
    pypath_txt = "../cppForSwig/pypaths.txt"
    print "\n\nNOW COMPILING AND INSTALLING ARMORY.\n"
    print "Writing", pypath_txt
    f = open(pypath_txt, "w")
    f.write(pypath_txt_template % (pyprefix, pyprefix))
    f.close()
    system("cd .. && make all")
    system("cd .. && make DESTDIR='%s' install" 
           % (os.path.join(workdir, appname, "Contents/MacOS/py"),))
    appscript = os.path.join(workdir, appname, "Contents/MacOS/Armory")
    system("cp Armory-script.sh '%s'" % (appscript,))
    system("chmod +x '%s'" % (appscript,))

def make_ressources():
    "Populate the Resources folder."
    cont = os.path.join(workdir, appname, 'Contents')
    res = os.path.join(cont, 'Resources')
    system("cp Info.plist '%s'" % (cont,))
    system("cd '%s' && cp ../MacOS/py/usr/share/armory/img/armory_icon_fullres.icns Icon.icns" % (res,))
    
def cleanup_app():
    "Try to remove as much unnecessary junk as possible."
    show_app_size()
    print "Removing Python test-suite."
    testdir = os.path.join(pyprefix, "lib/python2.7/test")
    if os.path.exists(testdir):
        shutil.rmtree(testdir)
    print "Removing .pyo and unneeded .py files."
    remove_python_files(pyprefix)
    remove_python_files(os.path.join(workdir, appname, 'Contents/MacOS/py'))
    show_app_size()
    print "Removing unneeded Qt frameworks."
    keep = ['QtCore.framework', 'QtGui.framework', 'QtXml.framework']
    qtdir = os.path.join(workdir, appname, "Contents/Dependencies/qt/4.8.5")
    dir =  os.path.join(qtdir, 'lib')
    for f in os.listdir(dir):
        if f not in keep:
            pathname = os.path.join(dir, f)
            if os.path.isdir(pathname):
                shutil.rmtree(pathname)
            else:
                os.remove(pathname)
    for f in os.listdir(qtdir):
        if f.endswith('.app') or f == 'tests':
            shutil.rmtree(os.path.join(qtdir,f))
    show_app_size()

def show_app_size():
    "Show the size of the app."
    print "Size of application: ",
    sys.stdout.flush()
    os.system("cd workspace && du -hs '%s'" % (appname,))

def remove_python_files(top):
    "Remove .pyo files and any .py files where the .pyc file exists."
    n_pyo = 0
    n_py_rem = 0
    n_py_kept = 0
    for (dirname, dirs, files) in os.walk(top):
        for f in files:
            prename, ext = os.path.splitext(f)
            if ext == '.pyo':
                os.remove(os.path.join(dirname, f))
                n_pyo += 1
            elif ext == '.py':
                if (f + 'c') in files:
                    os.remove(os.path.join(dirname, f))
                    n_py_rem += 1
                else:
                    n_py_kept += 1
    print "Removed %i .pyo files." % (n_pyo,)
    print "Removes %i .py files (kept %i)." % (n_py_rem, n_py_kept)
        
main()

