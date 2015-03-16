package=pyqt5
$(package)_version=5.4.1
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-$($(package)_version)
$(package)_file_name=PyQt-gpl-$($(package)_version).tar.gz
$(package)_mingw32_file_name=PyQt-gpl-$($(package)_version).tar.gz
$(package)_sha256_hash=c6c33f392c0a2b0c9ec16531dc88fa9aee853e9fff10f0ad9d0e4777629fe79e
$(package)_mingw32_sha256_hash=39fe23844b08f67833581f98dbe5cf9de501785a0af1176e3e8046a9fb28a247
$(package)_dependencies=python3 qt sip gcc

define $(package)_set_vars
$(package)_build_opts=CC="$($(package)_cc)" CXX="$($(package)_cxx)" AR="$($(package)_ar)" NM="$($(package)_nm)" RANLIB="$($(package)_ranlib)"
endef

define $(package)_config_cmds
  $($(package)_prefixbin)python3 configure.py --confirm-license --sip=$($(package)_prefixbin)sip
endef

define $(package)_build_cmds
  $(MAKE) $($(package)_build_opts)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
