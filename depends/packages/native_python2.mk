package=native_python2
$(package)_version=2.7.9
$(package)_download_path=https://www.python.org/ftp/python/$($(package)_version)
$(package)_file_name=Python-$($(package)_version).tgz
$(package)_sha256_hash=c8bba33e66ac3201dabdc556f0ea7cfe6ac11946ec32d357c4c6f9b018c12c5b

define $(package)_config_cmds
  $($(package)_autoconf) --build=$(BUILD) --enable-ipv6
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install && \
  mkdir -p $($(package)_staging_dir)/$(build_prefix) && \
  cp python $($(package)_staging_dir)/$(build_prefix)/hostpython && \
  cp Parser/pgen $($(package)_staging_dir)/$(build_prefix)/hostpgen
endef
