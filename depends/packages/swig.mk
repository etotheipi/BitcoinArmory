package=swig
$(package)_version=3.0.5
$(package)_download_path=http://sourceforge.net/projects/swig/files/swig/$(package)-$($(package)_version)
$(package)_file_name=$(package)-$($(package)_version).tar.gz
$(package)_sha256_hash=9f4cb9e8f213f041853646f58fe5e8428d63250d05f5c943b6fa759c77322a3c
$(package)_dependencies=pcre

define $(package)_set_vars
$(package)_config_opts = --without-allegrocl --without-chicken --without-clisp
$(package)_config_opts += --without-csharp --without-gcj --without-guile
$(package)_config_opts += --without-java --without-lua --without-mzscheme
$(package)_config_opts += --without-ocaml --without-octave --without-perl5
$(package)_config_opts += --without-php4 --without-pike --without-r
$(package)_config_opts += --without-ruby --without-rxspencer --without-tcl
$(package)_config_opts += --prefix $($(package)_staging_dir)
$(package)_config_opts += PCRE_CONFIG=$($(package)_prefixbin)/pcre-config
$(package)_build_opts = LIBS="-lpcre -lz"
endef

define $(package)_config_cmds
  $($(package)_autoconf)
endef

define $(package)_build_cmds
  $(MAKE) $($(package)_build_opts)
endef

define $(package)_stage_cmds
  $(MAKE) install
endef
