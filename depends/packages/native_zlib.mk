package=native_zlib
$(package)_version=1.2.8
$(package)_download_path=http://zlib.net
$(package)_file_name=zlib-$($(package)_version).tar.gz
$(package)_sha256_hash=36658cb768a54c1d4dec43c3116c27ed893e88b02ecfcb44f2166f9c0b7f2a0d

define $(package)_config_cmds
  ./configure --prefix $($(package)_prefix) --static
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
