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
