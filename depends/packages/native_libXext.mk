package=native_libXext
$(package)_version=1.3.3
$(package)_download_path=http://xorg.freedesktop.org/releases/individual/lib/
$(package)_file_name=libXext-$($(package)_version).tar.bz2
$(package)_sha256_hash=b518d4d332231f313371fdefac59e3776f4f0823bcb23cf7c7305bfb57b16e35
$(package)_dependencies=native_xproto native_xextproto native_libX11 native_libXau

define $(package)_set_vars
  $(package)_config_opts=--disable-static
  $(package)_config_opts_arm_linux=--enable-malloc0returnsnull
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
