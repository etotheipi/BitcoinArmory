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
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/share/applications
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/share/armory/img
	rsync -rupE --exclude="img/.DS_Store" img $(DESTDIR)$(PREFIX)/share/armory/
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armory.desktop > $(DESTDIR)$(PREFIX)/share/applications/armory.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armoryoffline.desktop > $(DESTDIR)$(PREFIX)/share/applications/armoryoffline.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armorytestnet.desktop > $(DESTDIR)$(PREFIX)/share/applications/armorytestnet.desktop

install-exec-local:
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/extras
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/bitcoinrpc_jsonrpc
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc/web
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/ui
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/pytest
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/BitTornado/BT1
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/lib/armory/urllib3
	$(MKDIR_P) $(DESTDIR)$(PREFIX)/bin
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

Armory.app: Armory-tmp
	rm -rf osxbuild/$@
	cp -r osxbuild/Armory-tmp osxbuild/$@

Armory-tmp: all osxbuild/install-py3 osxbuild/install-qt5
	rm -rf osxbuild/Armory-tmp osxbuild/$@
	$(MKDIR_P) osxbuild/Armory-tmp/Contents/MacOS/py
	$(MKDIR_P) osxbuild/Armory-tmp/Contents/Frameworks
	$(MKDIR_P) osxbuild/Armory-tmp/Contents/Resources
	$(MKDIR_P) osxbuild/Armory-tmp/Contents/Dependencies
	$(MAKE) DESTDIR=osxbuild/Armory-tmp/Contents/MacOS/py PREFIX=/usr install
	cp osxbuild/Info.plist osxbuild/Armory-tmp/Contents
	cp img/armory_icon_fullres.icns osxbuild/Armory-tmp/Contents/Resources/Icon.icns
	cp osxbuild/Armory-script.sh osxbuild/Armory-tmp/Contents/MacOS/Armory
	cp osxbuild/armoryd-script.sh osxbuild/Armory-tmp/Contents/MacOS/armoryd
	cp -r osxbuild/install-py3/Python.framework osxbuild/Armory-tmp/Contents/Frameworks/
	cp -r osxbuild/install-qt5/lib/Qt{Core,Gui,Network}.framework osxbuild/Armory-tmp/Contents/Frameworks/
	chmod +x osxbuild/Armory-tmp/Contents/MacOS/Armory
	chmod +x osxbuild/Armory-tmp/Contents/MacOS/armoryd

osxbuild/install-py3:
	@echo "building py3"
	cd osxbuild && ./build-py3.sh

osxbuild/install-qt5:
	@echo "building qt5"
	cd osxbuild && ./build-qt5.sh
endif # end TARGET_DARWIN
