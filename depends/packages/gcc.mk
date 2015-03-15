package=gcc
$(package)_version=4.9.2
$(package)_download_path=http://mirrors.kernel.org/gnu/$(package)/$(package)-$($(package)_version)
$(package)_file_name=$(package)-$($(package)_version).tar.gz
$(package)_sha256_hash=3e573826ec8b0d62d47821408fbc58721cd020df3e594cd492508de487a43b5e
$(package)_dependencies=gmp mpfr mpc
$(package)_patches=30880.patch
$(package)_cc=$($($(1)_type)_CC)
$(package)_cxx=$($($(1)_type)_CXX)
$(package)_ar=$($($(1)_type)_AR)
$(package)_nm=$($($(1)_type)_NM)
$(package)_ranlib=$($($(1)_type)_RANLIB)

define $(package)_preprocess_cmds
  patch -p1 < $($(package)_patch_dir)/30880.patch
endef

define $(package)_config_cmds
  $($(package)_autoconf) --disable-shared --enable-languages=c,c++ --with-gmp=$($(package)_prefix) --with-mpfr=$($(package)_prefix) --with-mpc=$($(package)_prefix)
endef

define $(package)_build_cmds
  $(MAKE) bootstrap
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
