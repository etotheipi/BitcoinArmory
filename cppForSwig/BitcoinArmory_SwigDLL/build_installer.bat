REM This should only be run from cppForSwig\BitcoinArmory_SwigDLL directory
copy ..\libs\Win32\BitcoinArmory_SwigDLL.dll ..\..\_CppBlockUtils.pyd
C:\Python27\Lib\site-packages\PyQt4\pyrcc4.exe -o ..\..\qrc_img_resources.py ..\..\imgList.xml
python ..\..\setup.py py2exe --includes sip,hashlib,json,twisted -d ..\..\ArmoryStandalone
copy ..\..\img\*.ico ..\..\ArmoryStandalone
copy ..\..\img\armory_logo*.png ..\..\ArmoryStandalone
copy ..\..\default_bootstrap.torrent ..\..\ArmoryStandalone 
python ..\..\writeNSISCompilerArgs.py
makensis.exe ..\..\ArmorySetup.nsi
