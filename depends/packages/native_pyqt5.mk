package=native_pyqt5
$(package)_version=5.4.1
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-$($(package)_version)
$(package)_file_name=PyQt-gpl-$($(package)_version).tar.gz
$(package)_sha256_hash=c6c33f392c0a2b0c9ec16531dc88fa9aee853e9fff10f0ad9d0e4777629fe79e
$(package)_dependencies=native_python3 native_qt native_sip

define $(package)_config_cmds
  $($(package)_prefix)/bin/python3 configure.py --confirm-license --bindir=$($(package)_prefix)/bin --qmake=$($(package)_prefix)/bin/qmake-native --sip=$($(package)_prefix)/bin/sip --sip-incdir=$($(package)_prefix)/include/python3.4m --spec=linux-g++ --verbose
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) INSTALL_ROOT=$($(package)_staging_dir) install
endef
