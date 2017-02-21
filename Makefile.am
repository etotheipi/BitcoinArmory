# Makefile for BitcoinArmory bitcoin wallet

SUBDIRS = cppForSwig

ACLOCAL_AMFLAGS = -I m4

lrelease:
	lrelease lang/*.ts

qrc_img_resources.py: imgList.xml
	pyrcc4 -o qrc_img_resources.py imgList.xml

copy-script:
	cp cppForSwig/ArmoryDB ./ArmoryDB
	cp cppForSwig/CppBlockUtils.py ./CppBlockUtils.py
	cp cppForSwig/.libs/libCppBlockUtils.so ./_CppBlockUtils.so

.PHONY: copy-script lrelease qrc_img_resources.py

all-local: copy-script lrelease qrc_img_resources.py

clean-local:
	rm -f ArmoryDB
	rm -f CppBlockUtils.py
	rm -f _CppBlockUtils.so
	rm -f CppBlockUtils.pyc
