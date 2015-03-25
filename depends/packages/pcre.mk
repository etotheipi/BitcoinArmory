package=pcre
$(package)_version=8.36
$(package)_download_path=http://sourceforge.net/projects/$(package)/files/$(package)/$($(package)_version)
$(package)_file_name=$(package)-$($(package)_version).tar.gz
$(package)_sha256_hash=b37544f33caed0cc502a1e729c3b1d3df5086dcc819b9125c30700c239246c9e

define $(package)_config_cmds
  $($(package)_autoconf)
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) DESTDIR=$($(package)_staging_dir) install
endef
