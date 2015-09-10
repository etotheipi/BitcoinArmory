package=python3
$(package)_version=3.4.3
$(package)_download_path=https://www.python.org/ftp/python/$($(package)_version)
$(package)_file_name=Python-$($(package)_version).tgz
$(package)_sha256_hash=8b743f56e9e50bf0923b9e9c45dd927c071d7aa56cd46569d8818add8cf01147
$(package)_patches=0010-cross-darwin-feature.patch

define $(package)_set_vars
$(package)_config_env_darwin=READELF="x86_64-apple-darwin11-otool" CONFIG_SITE=config.site MACOSX_DEPLOYMENT_TARGET=10.7
$(package)_config_opts_darwin = --disable-ipv6 --without-ensurepip --enable-framework=$(host_prefix)
endef

define $(package)_preprocess_cmds
  echo "ac_cv_file__dev_ptmx=no" > config.site && \
  echo "ac_cv_file__dev_ptc=no" >> config.site && \
  patch -p1 --ignore-whitespace < $($(package)_patch_dir)/0010-cross-darwin-feature.patch && \
  autoreconf && \
  sed -i.old "/frameworkinstallapps:/,+1d" Makefile.pre.in
endef

define $(package)_config_cmds
  $($(package)_autoconf) --build=$(BUILD)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) STRIPFLAG="-s --strip-program=x86_64-apple-darwin11-strip" install
endef
