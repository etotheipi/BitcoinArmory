# All the actual Makefiles are deeper in the directory tree.  
# I am just calling them, here.

DESTDIR=/usr

all :
	$(MAKE) -C cppForSwig swig

clean :
	$(MAKE) -C cppForSwig clean
	rm -rf osxbuild/Armory.app
	rm -rf osxbuild/env

install : all
	mkdir -p $(DESTDIR)/share/armory/img
	mkdir -p $(DESTDIR)/lib/armory/extras
	mkdir -p $(DESTDIR)/lib/armory/jsonrpc
	mkdir -p $(DESTDIR)/lib/armory/ui
	cp *.py *.so README $(DESTDIR)/lib/armory/
	cp img/* $(DESTDIR)/share/armory/img
	cp extras/*.py $(DESTDIR)/lib/armory/extras
	cp jsonrpc/*.py $(DESTDIR)/lib/armory/jsonrpc
	cp ui/*.py $(DESTDIR)/lib/armory/ui
	mkdir -p $(DESTDIR)/share/applications
	sed "s:python /usr:python $(DESTDIR):g" < dpkgfiles/armory.desktop > $(DESTDIR)/share/applications/armory.desktop
	sed "s:python /usr:python $(DESTDIR):g" < dpkgfiles/armoryoffline.desktop > $(DESTDIR)/share/applications/armoryoffline.desktop
	sed "s:python /usr:python $(DESTDIR):g" < dpkgfiles/armorytestnet.desktop > $(DESTDIR)/share/applications/armorytestnet.desktop
	

osx :
	chmod +x osxbuild/deploy.sh
	cd osxbuild; ./deploy.sh
