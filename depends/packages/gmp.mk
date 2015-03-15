package=gmp
$(package)_version=6.0.0a
$(package)_download_path=https://ftp.gnu.org/gnu/$(package)
$(package)_file_name=$(package)-$($(package)_version).tar.bz2
$(package)_sha256_hash=7f8e9a804b9c6d07164cf754207be838ece1219425d64e28cfa3e70d5c759aaf
$(package)_cc=$($($(1)_type)_CC)
$(package)_cxx=$($($(1)_type)_CXX)
$(package)_ar=$($($(1)_type)_AR)
$(package)_nm=$($($(1)_type)_NM)
$(package)_ranlib=$($($(1)_type)_RANLIB)

define $(package)_config_cmds
  $($(package)_autoconf)
endef

define $(package)_build_cmds
  $(MAKE) && \
  $(MAKE) check
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
