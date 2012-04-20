# All the actual Makefiles are deeper in the directory tree.  
# I am just calling them, here.

all :
	cd cppForSwig; make swig

clean :
	cd cppForSwig; make clean

install :
	mkdir -p $(DESTDIR)/usr/share/armory/img
	cp *.py *.so README LICENSE $(DESTDIR)/usr/share/armory/
	cp img/* $(DESTDIR)/usr/share/armory/img
	mkdir -p $(DESTDIR)/usr/share/applications
	cp dpkgfiles/armory*.desktop $(DESTDIR)/usr/share/applications/
