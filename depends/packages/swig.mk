package=swig
$(package)_version=3.0.5
$(package)_download_path=http://sourceforge.net/projects/swig/files/swig/$(package)-$($(package)_version)
$(package)_file_name=$(package)-$($(package)_version).tar.gz
$(package)_sha256_hash=9f4cb9e8f213f041853646f58fe5e8428d63250d05f5c943b6fa759c77322a3c

define $(package)_config_cmds
  $($(package)_autoconf) --prefix=$($(package)_staging_dir)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) install
endef
