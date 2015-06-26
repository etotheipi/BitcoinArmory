package=native_libxcb
$(package)_version=1.10
$(package)_download_path=http://xcb.freedesktop.org/dist
$(package)_file_name=libxcb-$($(package)_version).tar.bz2
$(package)_sha256_hash=98d9ab05b636dd088603b64229dd1ab2d2cc02ab807892e107d674f9c3f2d5b5
$(package)_dependencies=native_xcb_proto native_libXau native_xproto

define $(package)_set_vars
$(package)_config_opts=--disable-static
endef

define $(package)_preprocess_cmds
  sed "s/pthread-stubs//" -i configure
endef

define $(package)_config_cmds
  export PKG_CONFIG_PATH=$(build_prefix)/lib/pkgconfig && \
  $($(package)_autoconf)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef

define $(package)_postprocess_cmds
  rm -rf share/man share/doc
endef
