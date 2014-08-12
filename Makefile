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
	rm -f CppBlockUtils.py
	rm -f qrc_img_resources.py
	rm -f _CppBlockUtils.so
	rm -f cppForSwig/cryptopp/a.out
	rm -f *.pyc BitTornado/*.pyc bitcoinrpc_jsonrpc/*.pyc ui/*.pyc
	rm -f armoryengine/*.pyc dialogs/*.pyc BitTornado/BT1/*.pyc
	rm -f pytest/*.pyc txjsonrpc/*.pyc jsonrpc/*.pyc txjsonrpc/web/*.pyc 

install : all
	mkdir -p $(DESTDIR)$(PREFIX)/share/armory/img
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/extras
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/bitcoinrpc_jsonrpc
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc/web
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/ui
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/pytest
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/BitTornado/BT1
	mkdir -p $(DESTDIR)$(PREFIX)/lib/armory/urllib3
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	cp dpkgfiles/armory $(DESTDIR)$(PREFIX)/bin
	chmod +x $(DESTDIR)$(PREFIX)/bin/armory
	cp *.py *.so README $(DESTDIR)$(PREFIX)/lib/armory/
	rsync -rupE armoryengine $(DESTDIR)$(PREFIX)/lib/armory/
	rsync -rupE --exclude="img/.DS_Store" img $(DESTDIR)$(PREFIX)/share/armory/
	cp extras/*.py $(DESTDIR)$(PREFIX)/lib/armory/extras
	cp bitcoinrpc_jsonrpc/*.py $(DESTDIR)$(PREFIX)/lib/armory/bitcoinrpc_jsonrpc
	cp -r txjsonrpc/*.py $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc
	cp -r txjsonrpc/web/*.py $(DESTDIR)$(PREFIX)/lib/armory/txjsonrpc/web
	cp ui/*.py $(DESTDIR)$(PREFIX)/lib/armory/ui
	cp pytest/*.py $(DESTDIR)$(PREFIX)/lib/armory/pytest
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
	(cd cppForSwig/gtest && ./CppBlockUtilsTests)
	python -m unittest discover

osx :
	chmod +x osxbuild/deploy.sh
	cd osxbuild; ./deploy.sh
