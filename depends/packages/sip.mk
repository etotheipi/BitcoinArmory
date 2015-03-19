package=sip
$(package)_version=4.16.6
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/$(package)/$(package)-$($(package)_version)
$(package)_file_name=$(package)-$($(package)_version).tar.gz
$(package)_mingw32_file_name=$(package)-$($(package)_version).zip
$(package)_sha256_hash=8c7db2baf52935ee7d8573c98d6ede0d90e4308b8b9e7739e59acf1650714552
$(package)_mingw32_sha256_hash=2ff9d41131222fd3c9951338dc4b5f3bf3d5e44787f39938624f12cbe4e0cdbb
$(package)_dependencies=python2 gcc

define $(package)_set_vars
$(package)_build_opts=CC="$($(package)_cc)" CXX="$($(package)_cxx)" AR="$($(package)_ar)" NM="$($(package)_nm)" RANLIB="$($(package)_ranlib)" LINK="$($(package)_cxx)"
endef

define $(package)_config_cmds
  $($(package)_prefixbin)/python configure.py
endef

define $(package)_build_cmds
  $(MAKE) $($(package)_build_opts)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
