REM This should only be run from cppForSwig\BitcoinArmory_SwigDLL directory
python ..\..\update_version.py
copy ..\libs\x64\BDM_Client.dll ..\..\_CppBlockUtils.pyd 
C:\Python27_64\Lib\site-packages\PyQt4\pyrcc4.exe -o ..\..\qrc_img_resources.py ..\..\imgList.xml
python64 ..\..\setup.py py2exe --includes sip,hashlib,json,twisted -d ..\..\ArmoryStandalone
python64 ..\..\writeNSISCompilerArgs.py
makensis.exe ..\..\ArmorySetup.nsi
