package=pyqt5
$(package)_version=5.4.1
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-$($(package)_version)
$(package)_file_name=PyQt-gpl-$($(package)_version).tar.gz
$(package)_mingw32_file_name=PyQt-gpl-$($(package)_version).tar.gz
$(package)_sha256_hash=c6c33f392c0a2b0c9ec16531dc88fa9aee853e9fff10f0ad9d0e4777629fe79e
$(package)_mingw32_sha256_hash=39fe23844b08f67833581f98dbe5cf9de501785a0af1176e3e8046a9fb28a247
$(package)_dependencies=native_python3 python3 qt native_sip
$(package)_patches=darwin.cfg

define $(package)_config_cmds
  sed -i.old "1s|^|install_sysroot = $(host_prefix)\n|" $($(package)_patch_dir)/darwin.cfg && \
  sed -i.old "s|if 'linux' in target_config.qmake_spec|if 'linux' in target_config.qmake_spec and 'mac' not in target_config.qmake_spec|" configure.py && \
  $($(package)_prefix)/native/bin/python3 configure.py --confirm-license --qmake=$($(package)_prefix)/native/bin/qmake --sip=$($(package)_prefix)/native/bin/sip --sip-incdir=$($(package)_prefix)/native/include/python3.4m --configuration=$($(package)_patch_dir)/darwin.cfg --sysroot=$($(package)_prefix) --spec=macx-clang-linux
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) INSTALL_ROOT=$($(package)_staging_dir) install
endef
