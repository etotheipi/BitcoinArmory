# Setup MSVS 2013 Environment for building Armory in Windows

### ***You must use 64-bit packages!***

## List of packages needed

The latest versions of all packages might be different by the time your are reading this, and it tends to be safe to use newer versions, but we know these versions work. You *must* use python 2.x and Python-Qt4, **do not** use python3.x or Python-Qt5.  
To just build the _CppBlockUtils.pyd so you can run ArmoryQt.py, you can omit py2exe and NSIS, and any steps related to them (such as making sure stuff is in your PATH).

[Microsoft Visual Studio Express 2013 for Windows Desktop with Update 3](http://www.microsoft.com/en-us/download/confirmation.aspx?id=43733)

[SWIG 3.0.2 (Do not install! See below)](http://www.swig.org/download.html)

[Python 2.7.8](https://www.python.org/downloads/release/python-278/)

[Python psutil - 2.1.3](https://pypi.python.org/pypi?:action=display&name=psutil#downloads)

[Python-Qt4 4.11.2](http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.2/PyQt4-4.11.2-gpl-Py2.7-Qt4.8.6-x64.exe)

[py2exe [Only Farhod's modified version supports Unicode]](http://sourceforge.net/projects/py2exe/files/py2exe/)

[pywin32 - 2.19](http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win-amd64-py2.7.exe/download)

[NSIS (3.0+)](http://nsis.sourceforge.net/Download)

## Extra steps besides just installing everything

 - To accommodate systems with multiple versions of python, some tweaks were made to distinguish between them.

    - `C:\Python27\python.exe` was copied and renamed to `C:\Python27\python64.exe`

    - `C:\Python27_64\Lib\site-packages\PyQt4\pyrcc4.exe` is referenced by a build script even though default python installation does not have the **_64**.  Either rename the base directory or modify *BitcoinArmory/cppForSwig/BitcoinArmory_SwigDLL/build_installer_64.bat* to reference the correct path.

 - Make sure the following folders are in your PATH (environment variable):

    - `C:\Python27\`
    - `C:\Program Files (x86)\NSIS\`
    - `C:\Python27_64\Lib\site-packages\PyQt4\`


 - py2exe chokes on zope because its directory does does not contain a __init__.py.  Make sure the following file exists (and is empty):

    - `C:\Python27\Lib\site-packages\zope\__init__.py`


 - Swig is not installed like the other packages.  Unpack swig directory into *cppForSwig* and rename it to *swigwin*.  The following path should be valid:  `BitcoinArmory/cppForSwig/swigwin/swig.exe`
