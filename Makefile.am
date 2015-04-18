SUBDIRS = cppForSwig
PREFIX = @prefix@

all:
	$(MAKE) -C cppForSwig

clean-local:
	$(MAKE) -C cppForSwig clean
	rm -f CppBlockUtils.py
	rm -f qrc_img_resources.py
	rm -f _CppBlockUtils.so
	rm -f cppForSwig/cryptopp/a.out
	rm -f *.pyc BitTornado/*.pyc bitcoinrpc_jsonrpc/*.pyc ui/*.pyc
	rm -f armoryengine/*.pyc dialogs/*.pyc BitTornado/BT1/*.pyc
	rm -f pytest/*.pyc txjsonrpc/*.pyc jsonrpc/*.pyc txjsonrpc/web/*.pyc

install-data-local:
	mkdir -p $(DESTDIR)$(PREFIX)/share/applications
	mkdir -p $(DESTDIR)$(PREFIX)/share/armory/img
	rsync -rupE --exclude="img/.DS_Store" img $(DESTDIR)$(PREFIX)/share/armory/
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armory.desktop > $(DESTDIR)$(PREFIX)/share/applications/armory.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armoryoffline.desktop > $(DESTDIR)$(PREFIX)/share/applications/armoryoffline.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armorytestnet.desktop > $(DESTDIR)$(PREFIX)/share/applications/armorytestnet.desktop

install-exec-local:
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/extras
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/bitcoinrpc_jsonrpc
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc/web
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/ui
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/pytest
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/BitTornado/BT1
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/urllib3
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	sed "s: /usr: $(PREFIX):g" < dpkgfiles/armory > $(DESTDIR)$(PREFIX)/bin/armory
	chmod +x $(DESTDIR)$(PREFIX)/bin/armory
	cp *.py *.so README.md $(DESTDIR)$(PREFIX)/lib/armory/
	rsync -rupE armoryengine $(DESTDIR)$(PREFIX)/lib/armory/
	cp extras/*.py $(DESTDIR)$(PREFIX)/lib/armory/extras
	cp bitcoinrpc_jsonrpc/*.py $(DESTDIR)$(PREFIX)/lib/armory/bitcoinrpc_jsonrpc
	cp -r txjsonrpc/*.py $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc
	cp -r txjsonrpc/web/*.py $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc/web
	cp ui/*.py $(DESTDIR)$(PREFIX)/lib/armory/ui
	cp pytest/*.py $(DESTDIR)$(PREFIX)/lib/armory/pytest
	cp -r urllib3/* $(DESTDIR)$(PREFIX)/lib/armory/urllib3
	cp BitTornado/*.py $(DESTDIR)$(PREFIX)/lib/armory/BitTornado
	cp BitTornado/BT1/*.py $(DESTDIR)$(PREFIX)/lib/armory/BitTornado/BT1
	cp default_bootstrap.torrent $(DESTDIR)$(PREFIX)/lib/armory

if TARGET_DARWIN
if BUILD_LINUX
QMAKE=qmake-qt4
SIPPYQTINCLUDEDIR=/usr/share/sip/PyQt4
else
if BUILD_DARWIN
QMAKE=qmake -spec macx-g++
SIPPYQTINCLUDEDIR=/System/Library/Frameworks/Python.framework/Versions/2.7/share/sip/PyQt4
endif
endif
objc:
	sip -w -x VendorID -t WS_MACX -t Qt_4_8_6 -x Py_v3 -B Qt_5_0_0 -o \
		-P -g -c osxbuild/objc_armory/ -I $(SIPPYQTINCLUDEDIR) \
		osxbuild/objc_armory/ArmoryMac.sip
	$(QMAKE) osxbuild/objc_armory/ArmoryMac.pro -o osxbuild/objc_armory/
	$(MAKE) -C osxbuild/objc_armory/ CC="$(CC)" CXX="$(CXX)" LINK="$(LINK)"

Armory.app: Armory-tmp
	rm -rf osxbuild/$@
	cp -r osxbuild/Armory-tmp osxbuild/$@

Armory-tmp: all
	rm -rf osxbuild/Armory-tmp osxbuild/$@
	mkdir -p osxbuild/Armory-tmp/Contents/MacOS/py
	mkdir -p osxbuild/Armory-tmp/Contents/Resources
	$(MAKE) DESTDIR=osxbuild/Armory-tmp/Contents/MacOS/py PREFIX=/usr install
	cp osxbuild/Info.plist osxbuild/Armory-tmp/Contents
	cp img/armory_icon_fullres.icns osxbuild/Armory-tmp/Contents/Resources/Icon.icns
	cp osxbuild/Armory-script-autotools.sh osxbuild/Armory-tmp/Contents/MacOS/Armory
	cp osxbuild/armoryd-script-autotools.sh osxbuild/Armory-tmp/Contents/MacOS/armoryd
	chmod +x osxbuild/Armory-tmp/Contents/MacOS/Armory
	chmod +x osxbuild/Armory-tmp/Contents/MacOS/armoryd
endif # end TARGET_DARWIN
