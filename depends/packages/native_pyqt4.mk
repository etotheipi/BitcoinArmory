package=native_pyqt4
$(package)_version=4.11.3
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-$($(package)_version)
$(package)_file_name=PyQt-x11-gpl-$($(package)_version).tar.gz
$(package)_sha256_hash=853780dcdbe2e6ba785d703d059b096e1fc49369d3e8d41a060be874b8745686
$(package)_dependencies=native_python2 qt48 native_sip
$(package)_patches=remove_timestamps.patch

define $(package)_preprocess_cmds
  patch -p1 < $($(package)_patch_dir)/remove_timestamps.patch
endef

define $(package)_config_cmds
  export QTDIR=$($(package)_prefix) && \
  export PATH="$($(package)_prefix):$($(package)_prefix)/../bin:${PATH}" && \
  $($(package)_prefix)/bin/python configure-ng.py --confirm-license --qmake $($(package)_prefix)/bin/qmake --sip=$($(package)_prefix)/bin/sip --sip-incdir $($(package)_prefix)/include/python2.7/ --bindir=$($(package)_staging_prefix_dir)/bin --sysroot=$($(package)_prefix) --static --verbose
endef

define $(package)_build_cmds
  cd pyrcc && $(MAKE)
endef

define $(package)_stage_cmds
  cd pyrcc && $(MAKE) install
endef
