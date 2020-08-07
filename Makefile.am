# Makefile for BitcoinArmory bitcoin wallet
SUBDIRS = cppForSwig

EXTRA_DIST = *.py *.md LICENSE LICENSE-ATI LICENSE-MIT \
	nginx_example.conf imgList.xml autogen.sh \
	armoryengine/*.py ui/*.py \
	img/* lang/* dpkgfiles/* \
	windowsbuild/* linuxbuild/* osxbuild/* BitcoinArmory.spec

ACLOCAL_AMFLAGS = -I m4

lrelease:
if HAVE_GUI
	$(HAVE_LRELEASE) lang/*.ts
endif

qrc_img_resources.py: imgList.xml
if HAVE_GUI
	pyrcc4 -o qrc_img_resources.py imgList.xml
endif

copy-script:
	cp cppForSwig/ArmoryDB ./ArmoryDB

# SWIG code and requirements.
if HAVE_GUI
	cp cppForSwig/CppBlockUtils.py ./CppBlockUtils.py
if BUILD_DARWIN
	cp cppForSwig/.libs/libCppBlockUtils.dylib ./_CppBlockUtils.so
else
	cp cppForSwig/.libs/libCppBlockUtils.so ./_CppBlockUtils.so
endif
endif

.PHONY: copy-script lrelease qrc_img_resources.py

all-local: copy-script lrelease qrc_img_resources.py


#target to clean up pre autotools installation left overs
uninstall-old:
	rm -f $(DESTDIR)$(prefix)/bin/ArmoryDB

install-exec-hook: uninstall-old
if HAVE_GUI
	mkdir -p $(DESTDIR)$(prefix)/lib/armory/ui
	mkdir -p $(DESTDIR)$(prefix)/lib/armory/armoryengine
	mkdir -p $(DESTDIR)$(prefix)/lib/armory/lang
	mkdir -p $(DESTDIR)$(prefix)/share/applications
	cp *.py *.so README.md $(DESTDIR)$(prefix)/lib/armory
	cp -r ui/* $(DESTDIR)$(prefix)/lib/armory/ui
	cp -r armoryengine/* $(DESTDIR)$(prefix)/lib/armory/armoryengine
	cp lang/*.qm $(DESTDIR)$(prefix)/lib/armory/lang
endif

	mkdir -p $(DESTDIR)$(prefix)/bin
# Sometimes, uninstall-old deletes a valid ArmoryDB. Copy again to be safe.
	cp ArmoryDB $(DESTDIR)$(prefix)/bin

# No need to install test binaries.
if BUILD_TESTS
	rm -f $(DESTDIR)$(prefix)/bin/ContainerTests
	rm -f $(DESTDIR)$(prefix)/bin/CppBlockUtilsTests
	rm -f $(DESTDIR)$(prefix)/bin/DB1kIterTest
endif

# Skip Linux-specific steps on OSX.
if ! BUILD_DARWIN
# Unfuck broken build system that, upon make install, incorrectly
# regenerates files with DESTDIR instead of prefix.
# Who the hell uses autotools in 2017?
if HAVE_GUI
	rsync -rupE --exclude="img/.DS_Store" img $(DESTDIR)$(prefix)/share/armory/
	sed "s: /usr: $(prefix):g" < dpkgfiles/armory > $(DESTDIR)$(prefix)/bin/armory
	chmod +x $(DESTDIR)$(prefix)/bin/armory
	mkdir -p $(DESTDIR)$(datadir)/applications
	chmod 0755 $(DESTDIR)$(datadir)/applications
	for f in armory.desktop armoryoffline.desktop armorytestnet.desktop ; do sed "s:/usr/local/bin:$(bindir):g" < dpkgfiles/$$f > $(DESTDIR)$(datadir)/applications/$$f ; chmod 0644 $(DESTDIR)$(datadir)/applications/$$f ; done
endif
endif

uninstall-hook: uninstall-old
	rm -rf $(DESTDIR)$(prefix)/lib/armory
	rm -rf $(DESTDIR)$(prefix)/bin/armory
	rm -f  $(DESTDIR)$(prefix)/share/applications/armory*
	rm -rf $(DESTDIR)$(prefix)/share/armory

clean-local:
	rm -f ArmoryDB
	rm -f CppBlockUtils.py
	rm -f _CppBlockUtils.so
	rm -f CppBlockUtils.pyc

srpm: dist
	mkdir -p dist
	tmpdir=`mktemp -d` ; rpmbuild --define "_topdir $$tmpdir" -ts bitcoinarmory-$(PACKAGE_VERSION).tar.gz && { mv -f "$$tmpdir"/SRPMS/* . ; } ; rm -rf "$$tmpdir"

rpm: dist
	mkdir -p dist
	tmpdir=`mktemp -d` ; rpmbuild --define "_topdir $$tmpdir" -ta bitcoinarmory-$(PACKAGE_VERSION).tar.gz && { mv -f "$$tmpdir"/SRPMS/* "$$tmpdir"/RPMS/*/* . ; } ; rm -rf "$$tmpdir"
