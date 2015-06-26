package=native_libICE
$(package)_version=1.0.9
$(package)_download_path=http://xorg.freedesktop.org/releases/individual/lib/
$(package)_file_name=libICE-$($(package)_version).tar.bz2
$(package)_sha256_hash=8f7032f2c1c64352b5423f6b48a8ebdc339cc63064af34d66a6c9aa79759e202
$(package)_dependencies=native_xtrans native_xproto

define $(package)_set_vars
  $(package)_config_opts=--disable-static --disable-docs --disable-specs --without-xsltproc
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
