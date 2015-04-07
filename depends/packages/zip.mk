# Currently broken. Tried setting BINDIR, MANDIR, and prefix, but can't get
# zip to install in the correct location.
package=zip
$(package)_version=3.0
$(package)_download_path=http://sourceforge.net/projects/infozip/files/Zip 3.x (latest)/3.0
$(package)_file_name=zip30.tar.gz
$(package)_sha256_hash=f0e8bb1f9b7eb0b01285495a2699df3a4b766784c1765a8f1aeedf63c0806369

define $(package)_build_cmds
  $(MAKE) -f unix/Makefile generic
endef

define $(package)_stage_cmds
  $(MAKE) -f unix/Makefile install
endef
