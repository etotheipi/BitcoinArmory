SUBDIRS = cppForSwig
desktopdir = $(datarootdir)/applications
desktop_DATA = dpkgfiles/armory.desktop dpkgfiles/armoryoffline.desktop \
			  dpkgfiles/armorytestnet.desktop
CLEANFILES = $(desktop_DATA)

all:
	$(MAKE) -C cppForSwig

clean-local:
	rm -f CppBlockUtils.py
	rm -f qrc_img_resources.py
	rm -f _CppBlockUtils.so
	rm -f cppForSwig/cryptopp/a.out
	rm -f *.pyc BitTornado/*.pyc bitcoinrpc_jsonrpc/*.pyc ui/*.pyc
	rm -f armoryengine/*.pyc dialogs/*.pyc BitTornado/BT1/*.pyc
	rm -f pytest/*.pyc txjsonrpc/*.pyc jsonrpc/*.pyc txjsonrpc/web/*.pyc

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(datarootdir)/applications
	$(MKDIR_P) $(DESTDIR)$(datarootdir)/armory/img
	rsync -rupE --exclude="img/.DS_Store" img $(DESTDIR)$(datarootdir)/armory/

install-exec-local:
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/extras
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/bitcoinrpc_jsonrpc
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/txjsonrpc
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/txjsonrpc/web
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/ui
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/pytest
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/BitTornado/BT1
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/urllib3
	$(MKDIR_P) $(DESTDIR)$(bindir)
	$(SED) "s: /usr/lib: $(libdir):g" < dpkgfiles/armory > $(DESTDIR)$(bindir)/armory
	chmod +x $(DESTDIR)$(bindir)/armory
	cp *.py *.so README.md $(DESTDIR)$(libdir)/armory/
	rsync -rupE armoryengine $(DESTDIR)$(libdir)/armory/
	cp extras/*.py $(DESTDIR)$(libdir)/armory/extras
	cp bitcoinrpc_jsonrpc/*.py $(DESTDIR)$(libdir)/armory/bitcoinrpc_jsonrpc
	cp -R txjsonrpc/*.py $(DESTDIR)$(libdir)/armory/txjsonrpc
	cp -R txjsonrpc/web/*.py $(DESTDIR)$(libdir)/armory/txjsonrpc/web
	cp ui/*.py $(DESTDIR)$(libdir)/armory/ui
	cp pytest/*.py $(DESTDIR)$(libdir)/armory/pytest
	cp -R urllib3/* $(DESTDIR)$(libdir)/armory/urllib3
	cp BitTornado/*.py $(DESTDIR)$(libdir)/armory/BitTornado
	cp BitTornado/BT1/*.py $(DESTDIR)$(libdir)/armory/BitTornado/BT1
	cp default_bootstrap.torrent $(DESTDIR)$(libdir)/armory

dpkgfiles/%.desktop: dpkgfiles/%.desktop.in Makefile
	sed -e 's,[@]bindir[@],$(bindir),g' < $< > $@
	chmod +x $@

all-test-tools: all
	$(MAKE) -C cppForSwig/gtest

gtest: all-test-tools
	(cd cppForSwig/gtest && ./CppBlockUtilsTests)

pytest: all
	python -m unittest discover

test: gtest pytest

mo: messages
	$(MAKE) -C po mo

messages:
	xgettext -o po/messages.pot --from-code=UTF-8 -L Python -ktr *.py armoryengine/*.py ui/*.py

if TARGET_LINUX
if BUILD_LINUX
deb: all
	@while [ -z "$$AMD64_CHROOT" ]; do \
		read -r -p "Name of amd64 chroot: " AMD64_CHROOT; \
	done && \
	while [ -z "$$I386_CHROOT" ]; do \
		read -r -p "Name of i386 chroot: " I386_CHROOT; \
	done && \
	python dpkgfiles/make_deb_package.py $$AMD64_CHROOT 64 1 1 0 && \
	python dpkgfiles/make_deb_package.py $$I386_CHROOT 32 1 1 0
endif
endif

if TARGET_DARWIN
if BUILD_LINUX
QMAKE=qmake-qt4
else
if BUILD_DARWIN
QMAKE=qmake -spec macx-g++
endif
endif
objc:
	$(SIP) -w -x VendorID -t WS_MACX -t Qt_4_8_6 -x Py_v3 -B Qt_5_0_0 -o \
		-P -g -c osxbuild/objc_armory/ $(SIP_CPPFLAGS) \
		osxbuild/objc_armory/ArmoryMac.sip
	$(QMAKE) osxbuild/objc_armory/ArmoryMac.pro -o osxbuild/objc_armory/
	$(MAKE) -C osxbuild/objc_armory/ CC="$(CC)" CXX="$(CXX)" LINK="$(LINK)"

if USE_GITIAN
Armory.app: Armory-tmp-gitian
	rm -rf osxbuild/$@
	cp -R osxbuild/Armory-tmp-gitian osxbuild/$@
else
Armory.app: Armory-tmp
	rm -rf osxbuild/$@
	cp -R osxbuild/Armory-tmp osxbuild/$@
endif

Armory-tmp: all osxbuild/install-py3 osxbuild/install-qt5
	rm -rf osxbuild/$@
	$(MKDIR_P) osxbuild/$@/Contents/MacOS/py
	$(MKDIR_P) osxbuild/$@/Contents/Frameworks
	$(MKDIR_P) osxbuild/$@/Contents/Resources
	$(MKDIR_P) osxbuild/$@/Contents/Dependencies
	$(MAKE) DESTDIR=osxbuild/$@/Contents/MacOS/py PREFIX=/usr install
	cp osxbuild/Info.plist osxbuild/$@/Contents
	cp img/armory_icon_fullres.icns osxbuild/$@/Contents/Resources/Icon.icns
	cp osxbuild/Armory-script.sh osxbuild/$@/Contents/MacOS/Armory
	cp osxbuild/armoryd-script.sh osxbuild/$@/Contents/MacOS/armoryd
	cp -R osxbuild/install-py3/Python.framework osxbuild/$@/Contents/Frameworks/
	cp -R osxbuild/install-qt5/lib/Qt{Core,Gui,Network}.framework osxbuild/$@/Contents/Frameworks/
	chmod +x osxbuild/$@/Contents/MacOS/Armory
	chmod +x osxbuild/$@/Contents/MacOS/armoryd

Armory-tmp-gitian: all
	rm -rf osxbuild/$@
	$(MKDIR_P) osxbuild/$@/Contents/MacOS/py
	$(MKDIR_P) osxbuild/$@/Contents/Frameworks
	$(MKDIR_P) osxbuild/$@/Contents/Resources
	$(MKDIR_P) osxbuild/$@/Contents/Dependencies
	$(MAKE) DESTDIR=osxbuild/$@/Contents/MacOS/py PREFIX=/usr install
	cp osxbuild/Info.plist osxbuild/$@/Contents
	cp img/armory_icon_fullres.icns osxbuild/$@/Contents/Resources/Icon.icns
	cp osxbuild/Armory-script.sh osxbuild/$@/Contents/MacOS/Armory
	cp osxbuild/armoryd-script.sh osxbuild/$@/Contents/MacOS/armoryd
	cp -R depends/x86_64-apple-darwin11/Python.framework osxbuild/$@/Contents/Frameworks/
	cp -R depends/x86_64-apple-darwin11/lib/Qt{Core,Gui,Network}.framework osxbuild/$@/Contents/Frameworks/
	chmod +x osxbuild/$@/Contents/MacOS/Armory
	chmod +x osxbuild/$@/Contents/MacOS/armoryd

osxbuild/install-py3:
	@echo "building py3"
	cd osxbuild && ./build-py3.sh

osxbuild/install-qt5:
	@echo "building qt5"
	cd osxbuild && ./build-qt5.sh
endif # end TARGET_DARWIN
