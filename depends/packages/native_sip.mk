package=native_sip
$(package)_version=4.16.6
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/sip/sip-$($(package)_version)
$(package)_file_name=sip-$($(package)_version).tar.gz
$(package)_sha256_hash=8c7db2baf52935ee7d8573c98d6ede0d90e4308b8b9e7739e59acf1650714552
$(package)_dependencies=native_python2

define $(package)_config_cmds
  $($(package)_prefixbin)/python configure.py
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
