package=mpfr
$(package)_version=3.1.2
$(package)_download_path=http://www.$(package).org/$(package)-current
$(package)_file_name=$(package)-$($(package)_version).tar.gz
$(package)_sha256_hash=176043ec07f55cd02e91ee3219db141d87807b322179388413a9523292d2ee85
$(package)_dependencies=gmp
$(package)_cc=$(default_host_CC)
$(package)_cxx=$(default_host_CXX)
$(package)_ar=$(default_host_AR)
$(package)_nm=$(default_host_NM)
$(package)_ranlib=$(default_host_RANLIB)

define $(package)_set_vars
$(package)_config_opts_mingw32=--enable-static --disable-shared
endef

define $(package)_config_cmds
  $($(package)_autoconf) --with-gmp=$($(package)_prefix)
endef

define $(package)_build_cmds
  $(MAKE)
  # Disable tests to allow this to work under mingw
  #$(MAKE) check
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
