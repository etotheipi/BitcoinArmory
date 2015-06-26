package=native_libX11
$(package)_version=1.6.2
$(package)_download_path=http://xorg.freedesktop.org/releases/individual/lib/
$(package)_file_name=libX11-$($(package)_version).tar.bz2
$(package)_sha256_hash=2aa027e837231d2eeea90f3a4afe19948a6eb4c8b2bec0241eba7dbc8106bd16
$(package)_dependencies=native_libxcb native_xtrans native_xextproto native_xproto

define $(package)_set_vars
$(package)_config_opts=--disable-xkb --disable-static
endef

define $(package)_config_cmds
  export PKG_CONFIG_PATH=$(build_prefix)/lib/pkgconfig:$(build_prefix)/share/pkgconfig && \
  $($(package)_autoconf)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
