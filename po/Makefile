
LANGUAGES=is

merge: $(patsubst %,%.po,$(LANGUAGES))
mo: $(patsubst %,%.mo,$(LANGUAGES))

%.po: messages.pot
	msgmerge -U $@ messages.pot

%.mo: %.po messages.pot
	msgfmt $< -o $@

# must be run from the top level "make install"
install:
	test "$(DESTDIR)" != ''
	for i in $(LANGUAGES); do mkdir -p $(DESTDIR)$(PREFIX)/share/locale/$$i/LC_MESSAGES; cp $$i.mo $(DESTDIR)$(PREFIX)/share/locale/$$i/LC_MESSAGES/armory.mo; done

