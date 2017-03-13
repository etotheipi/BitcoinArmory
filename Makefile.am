# Makefile for BitcoinArmory bitcoin wallet
SUBDIRS = cppForSwig
PREFIX = /usr

EXTRA_DIST = *.py *.md LICENSE LICENSE-ATI LICENSE-MIT \
	nginx_example.conf imgList.xml autogen.sh \
	armoryengine/*.py ui/*.py \
	img/* lang/* dpkgfiles/* \
	windowsbuild/* linuxbuild/* osxbuild/*

ACLOCAL_AMFLAGS = -I m4

lrelease:
	lrelease lang/*.ts

qrc_img_resources.py: imgList.xml
	pyrcc4 -o qrc_img_resources.py imgList.xml

copy-script:
	cp cppForSwig/ArmoryDB ./ArmoryDB
	cp cppForSwig/CppBlockUtils.py ./CppBlockUtils.py
if BUILD_DARWIN
	cp cppForSwig/.libs/libCppBlockUtils.dylib ./_CppBlockUtils.so
else
	cp cppForSwig/.libs/libCppBlockUtils.so ./_CppBlockUtils.so
endif

.PHONY: copy-script lrelease qrc_img_resources.py

all-local: copy-script lrelease qrc_img_resources.py

#target to clean up pre autotools installation left overs
uninstall-old: 
	rm -f $(DESTDIR)$(PREFIX)/bin/ArmoryDB 

install-exec-hook: uninstall-old
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/ui
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/armoryengine
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	mkdir -p $(DESTDIR)$(PREFIX)/share/applications
	cp *.py *.so README.md $(DESTDIR)$(PREFIX)/lib/armory
	cp -r ui/* $(DESTDIR)$(PREFIX)/lib/armory/ui
	cp -r armoryengine/* $(DESTDIR)$(PREFIX)/lib/armory/armoryengine
	sed "s: /usr: $(PREFIX):g" < dpkgfiles/armory > $(DESTDIR)$(PREFIX)/bin/armory 
	chmod +x $(DESTDIR)$(PREFIX)/bin/armory
if ! BUILD_DARWIN
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armory.desktop > $(DESTDIR)$(PREFIX)/share/applications/armory.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armoryoffline.desktop > $(DESTDIR)$(PREFIX)/share/applications/armoryoffline.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armorytestnet.desktop > $(DESTDIR)$(PREFIX)/share/applications/armorytestnet.desktop
endif

uninstall-hook: uninstall-old
	rm -rf $(DESTDIR)$(PREFIX)/lib/armory
	rm -rf $(DESTDIR)$(PREFIX)/bin/armory
	rm -f $(DESTDIR)$(PREFIX)/share/applications/armory.*

clean-local:
	rm -f ArmoryDB
	rm -f CppBlockUtils.py
	rm -f _CppBlockUtils.so
	rm -f CppBlockUtils.pyc
