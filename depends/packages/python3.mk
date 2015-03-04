package=python3
$(package)_version=3.4.3
$(package)_download_path=https://www.python.org/ftp/python/$($(package)_version)
$(package)_file_name=Python-$($(package)_version).tgz
$(package)_sha256_hash=8b743f56e9e50bf0923b9e9c45dd927c071d7aa56cd46569d8818add8cf01147

define $(package)_config_cmds
  $($(package)_autoconf) --build=$(BUILD)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
