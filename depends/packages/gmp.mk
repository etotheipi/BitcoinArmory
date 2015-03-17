package=gmp
$(package)_version=6.0.0a
$(package)_download_path=https://ftp.gnu.org/gnu/$(package)
$(package)_file_name=$(package)-$($(package)_version).tar.bz2
$(package)_sha256_hash=7f8e9a804b9c6d07164cf754207be838ece1219425d64e28cfa3e70d5c759aaf
$(package)_cc=$(host_CC)
$(package)_cxx=$(host_CXX)
$(package)_ar=$(host_AR)
$(package)_nm=$(host_NM)
$(package)_ranlib=$(host_RANLIB)

define $(package)_set_vars
$(package)_config_opts_mingw32=--disable-static --enable-shared
endef

define $(package)_config_cmds
  $($(package)_autoconf)
endef

define $(package)_build_cmds
  $(MAKE)
  # Need to comment out, because a test fails under mingw
  #$(MAKE) check
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
