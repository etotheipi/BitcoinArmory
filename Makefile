# All the actual Makefiles are deeper in the directory tree.  
# I am just calling them, here.

PREFIX=/usr
DESTDIR=

all :
	$(MAKE) -C cppForSwig

clean :
	$(MAKE) -C cppForSwig clean
	rm -f osxbuild/build-app.log.txt
	rm -rf osxbuild/workspace/

install : all
	mkdir -p $(DESTDIR)$(PREFIX)/share/armory/img
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/extras
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/jsonrpc
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/ui
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/BitTornado/BT1
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/urllib3
	cp *.py *.so README $(DESTDIR)$(PREFIX)/lib/armory/
	rsync -rupE armoryengine $(DESTDIR)$(PREFIX)/lib/armory/
	rsync -rupE img $(DESTDIR)$(PREFIX)/share/armory/
	cp extras/*.py $(DESTDIR)$(PREFIX)/lib/armory/extras
	cp jsonrpc/*.py $(DESTDIR)$(PREFIX)/lib/armory/jsonrpc
	cp ui/*.py $(DESTDIR)$(PREFIX)/lib/armory/ui
	cp -r urllib3/* $(DESTDIR)$(PREFIX)/lib/armory/urllib3
	mkdir -p $(DESTDIR)$(PREFIX)/share/applications
	cp BitTornado/*.py $(DESTDIR)$(PREFIX)/lib/armory/BitTornado
	cp BitTornado/BT1/*.py $(DESTDIR)$(PREFIX)/lib/armory/BitTornado/BT1
	cp default_bootstrap.torrent $(DESTDIR)$(PREFIX)/lib/armory
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armory.desktop > $(DESTDIR)$(PREFIX)/share/applications/armory.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armoryoffline.desktop > $(DESTDIR)$(PREFIX)/share/applications/armoryoffline.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armorytestnet.desktop > $(DESTDIR)$(PREFIX)/share/applications/armorytestnet.desktop

all-test-tools: all
	$(MAKE) -C cppForSwig/gtest

test: all-test-tools
	./cppForSwig/gtest/CppBlockUtilsTests

osx :
	chmod +x osxbuild/deploy.sh
	cd osxbuild; ./deploy.sh
