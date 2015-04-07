package=native_sip
$(package)_version=4.16.7
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/sip/sip-$($(package)_version)
$(package)_file_name=sip-$($(package)_version).tar.gz
$(package)_sha256_hash=4caa8d52e4403bae5c4c64f44de03a2cfd0bb10b6d96c5fb771133516df9abbd
$(package)_dependencies=native_python2

define $(package)_set_vars
  $(package)_config_opts=CC="$($(package)_cc)" CXX="$($(package)_cxx)" CFLAGS="$($(package)_cflags)"
  $(package)_config_opts+=CXXFLAGS="$($(package)_cxxflags)" LFLAGS="$($(package)_ldflags)"
  $(package)_config_opts+=LINK_SHLIB="$($(package)_cc)" LINK="$($(package)_cc)"
endef

define $(package)_config_cmds
  $($(package)_prefixbin)/python configure.py $($(package)_config_opts)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
