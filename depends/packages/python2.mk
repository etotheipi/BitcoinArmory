package=python2
$(package)_version=2.7.9
$(package)_download_path=https://www.python.org/ftp/python/$($(package)_version)
$(package)_file_name=Python-$($(package)_version).tgz
$(package)_sha256_hash=c8bba33e66ac3201dabdc556f0ea7cfe6ac11946ec32d357c4c6f9b018c12c5b
$(package)_dependencies=native_$(package)
$(package)_patches=Python-2.7.9-xcompile.patch

define $(package)_set_vars
$(package)_config_env=CONFIG_SITE=config.site
endef

define $(package)_preprocess_cmds
  echo "ac_cv_file__dev_ptmx=no" > config.site && \
  echo "ac_cv_file__dev_ptc=no" >> config.site && \
  echo "ac_cv_have_long_long_format=yes" >> config.site && \
  patch -p1 < $($(package)_patch_dir)/Python-2.7.9-xcompile.patch
endef

define $(package)_config_cmds
  $($(package)_autoconf) --build=$(BUILD) --enable-ipv6
endef

define $(package)_build_cmds
  $(MAKE) PYTHON_FOR_BUILD=$(host_prefix)/native/hostpython PGEN_FOR_BUILD=$(host_prefix)/native/hostpgen BLDSHARED='$(host_CC) -shared'
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install PYTHON_FOR_BUILD=$(host_prefix)/native/hostpython BLDSHARED='$(host_cc) -shared'
endef
