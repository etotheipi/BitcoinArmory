# All the actual Makefiles are deeper in the directory tree.  
# I am just calling them, here.

all :
	cd cppForSwig; make swig

clean :
	cd cppForSwig; make clean
	rm -rf osxbuild/Armory.app
	rm -rf osxbuild/env

install :
	mkdir -p $(DESTDIR)/usr/share/armory/img
	mkdir -p $(DESTDIR)/usr/lib/armory/extras
	mkdir -p $(DESTDIR)/usr/lib/armory/jsonrpc
	mkdir -p $(DESTDIR)/usr/lib/armory/dialogs
	cp *.py *.so README $(DESTDIR)/usr/lib/armory/
	cp img/* $(DESTDIR)/usr/share/armory/img
	cp extras/*.py $(DESTDIR)/usr/lib/armory/extras
	cp jsonrpc/*.py $(DESTDIR)/usr/lib/armory/jsonrpc
	cp dialogs/*.py $(DESTDIR)/usr/lib/armory/dialogs
	mkdir -p $(DESTDIR)/usr/share/applications
	cp dpkgfiles/armory*.desktop $(DESTDIR)/usr/share/applications/

osx :
	chmod +x osxbuild/deploy.sh
	cd osxbuild; ./deploy.sh
