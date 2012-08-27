# All the actual Makefiles are deeper in the directory tree.  
# I am just calling them, here.
DESTDIR ?= /usr

all :
	cd cppForSwig; make swig

clean :
	cd cppForSwig; make clean

install :
	mkdir -p $(DESTDIR)/share/armory/img
	cp *.py *.so README LICENSE $(DESTDIR)/share/armory/
	cp img/* $(DESTDIR)/share/armory/img
	mkdir -p $(DESTDIR)/share/applications
	cp dpkgfiles/armory*.desktop $(DESTDIR)/share/applications/
