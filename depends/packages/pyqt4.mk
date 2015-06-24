package=pyqt4
$(package)_version=4.11.3
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-$($(package)_version)
$(package)_linux_file_name=PyQt-x11-gpl-$($(package)_version).tar.gz
$(package)_darwin_file_name=PyQt-mac-gpl-$($(package)_version).tar.gz
$(package)_mingw32_file_name=PyQt-win-gpl-$($(package)_version).zip
$(package)_file_name=$($(package)_$(host_os)_file_name)
$(package)_linux_sha256_hash=853780dcdbe2e6ba785d703d059b096e1fc49369d3e8d41a060be874b8745686
$(package)_darwin_sha256_hash=8b8bb3a2ef8b7368710e0bc59d6e94e1f513f7dbf10a3aaa3154f7b848c88b4d
$(package)_mingw32_sha256_hash=aa25a2e11464fd2ff26e1a3ad514aae6d89a61bb03ce4746d255a82cf909225d
$(package)_sha256_hash=$($(package)_$(host_os)_sha256_hash)
$(package)_dependencies=native_python2 qt48 native_sip
$(package)_patches=remove_timestamps.patch

define $(package)_preprocess_cmds
  patch -p1 < $($(package)_patch_dir)/remove_timestamps.patch
endef

define $(package)_config_cmds
  export QTDIR=$($(package)_prefix) && \
  export PATH="$($(package)_prefixbin):$($(package)_prefix)/native/bin/:${PATH}" && \
  $($(package)_prefix)/native/bin/python configure-ng.py --confirm-license --qmake $($(package)_prefix)/native/bin/qmake --sip=$($(package)_prefix)/native/bin/sip --sip-incdir $($(package)_prefix)/native/include/python2.7/ --bindir=$($(package)_staging_prefix_dir)/bin --sysroot=$($(package)_prefix) --static --verbose
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) install
endef
