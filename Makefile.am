# Makefile for BitcoinArmory bitcoin wallet

SUBDIRS = cppForSwig

EXTRA_DIST = *.py *.md LICENSE LICENSE-ATI LICENSE-MIT \
	nginx_example.conf imgList.xml autogen.sh \
	armoryengine/*.py ui/*.py \
	img/* lang/* \
	windowsbuild/* linuxbuild/* osxbuild/*

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

install-local-exec: all
	sed "s: /usr: $(PREFIX):g" < dpkgfiles/armory > $(DESTDIR)$(PREFIX)/bin/armory chmod +x $(DESTDIR)$(PREFIX)/bin/armory

clean-local:
	rm -f ArmoryDB
	rm -f CppBlockUtils.py
	rm -f _CppBlockUtils.so
	rm -f CppBlockUtils.pyc
