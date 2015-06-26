package=native_libSM
$(package)_version=1.2.2
$(package)_download_path=http://xorg.freedesktop.org/releases/individual/lib/
$(package)_file_name=libSM-$($(package)_version).tar.bz2
$(package)_sha256_hash=0baca8c9f5d934450a70896c4ad38d06475521255ca63b717a6510fdb6e287bd
$(package)_dependencies=native_xtrans native_xproto native_libICE

define $(package)_set_vars
  $(package)_config_opts=--without-libuuid  --without-xsltproc  --disable-docs --disable-static
  $(package)_config_opts_linux=--with-pic
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
