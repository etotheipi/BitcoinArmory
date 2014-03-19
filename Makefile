# All the actual Makefiles are deeper in the directory tree.  
# I am just calling them, here.

PREFIX=/usr

all :
	$(MAKE) -C cppForSwig

clean :
	$(MAKE) -C cppForSwig clean
	rm -f osxbuild/build-app.log.txt
	rm -rf osxbuild/workspace/

install : all
	mkdir -p $(PREFIX)/share/armory/img
	mkdir -p $(PREFIX)/lib/armory/extras
	mkdir -p $(PREFIX)/lib/armory/jsonrpc
	mkdir -p $(PREFIX)/lib/armory/ui
	cp *.py *.so README $(PREFIX)/lib/armory/
	rsync -rupE armoryengine $(PREFIX)/lib/armory/
	rsync -rupE img $(PREFIX)/share/armory/
	cp extras/*.py $(PREFIX)/lib/armory/extras
	cp jsonrpc/*.py $(PREFIX)/lib/armory/jsonrpc
	cp ui/*.py $(PREFIX)/lib/armory/ui
	mkdir -p $(PREFIX)/share/applications
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armory.desktop > $(PREFIX)/share/applications/armory.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armoryoffline.desktop > $(PREFIX)/share/applications/armoryoffline.desktop
	sed "s:python /usr:python $(PREFIX):g" < dpkgfiles/armorytestnet.desktop > $(PREFIX)/share/applications/armorytestnet.desktop
	

osx :
	chmod +x osxbuild/deploy.sh
	cd osxbuild; ./deploy.sh
