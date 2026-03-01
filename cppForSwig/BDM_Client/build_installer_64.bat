REM This should only be run from cppForSwig\BitcoinArmory_SwigDLL directory

mkdir ..\..\ArmoryStandalone
copy ..\Release\guardian.exe ..\..\ArmoryStandalone

python ..\..\update_version.py
copy ..\libs\x64\BDM_Client.dll ..\..\_CppBlockUtils.pyd
C:\Python27\Lib\site-packages\PyQt4\pyrcc4.exe -o ..\..\qrc_img_resources.py ..\..\imgList.xml
python ..\..\setup.py py2exe --includes sip,hashlib -d ..\..\ArmoryStandalone
copy ..\x64\Release\BlockDataManager.exe ..\..\ArmoryStandalone\ArmoryDB.exe

mkdir ..\..\ArmoryStandalone\lang
lrelease ..\..\lang\armory_da.ts -qm ..\..\ArmoryStandalone\lang\armory_da.qm
lrelease ..\..\lang\armory_de.ts -qm ..\..\ArmoryStandalone\lang\armory_de.qm
lrelease ..\..\lang\armory_el.ts -qm ..\..\ArmoryStandalone\lang\armory_el.qm
lrelease ..\..\lang\armory_en.ts -qm ..\..\ArmoryStandalone\lang\armory_en.qm
lrelease ..\..\lang\armory_es.ts -qm ..\..\ArmoryStandalone\lang\armory_es.qm
lrelease ..\..\lang\armory_fr.ts -qm ..\..\ArmoryStandalone\lang\armory_fr.qm
lrelease ..\..\lang\armory_he.ts -qm ..\..\ArmoryStandalone\lang\armory_he.qm
lrelease ..\..\lang\armory_hr.ts -qm ..\..\ArmoryStandalone\lang\armory_hr.qm
lrelease ..\..\lang\armory_id.ts -qm ..\..\ArmoryStandalone\lang\armory_id.qm
lrelease ..\..\lang\armory_ru.ts -qm ..\..\ArmoryStandalone\lang\armory_ru.qm
lrelease ..\..\lang\armory_sv.ts -qm ..\..\ArmoryStandalone\lang\armory_sv.qm

python ..\..\writeNSISCompilerArgs.py
makensis.exe ..\..\ArmorySetup.nsi
