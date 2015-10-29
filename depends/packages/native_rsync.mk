package=native_rsync
$(package)_version=3.1.1
$(package)_download_path=https://rsync.samba.org/ftp/rsync
$(package)_file_name=rsync-$($(package)_version).tar.gz
$(package)_sha256_hash=7de4364fcf5fe42f3bdb514417f1c40d10bbca896abe7e7f2c581c6ea08a2621

define $(package)_config_cmds
  $($(package)_autoconf)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
