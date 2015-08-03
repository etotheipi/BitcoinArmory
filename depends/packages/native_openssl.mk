# Pretty much taken verbatim from Bitcoin Core
package=native_openssl
$(package)_version=1.0.1m
$(package)_download_path=https://www.openssl.org/source
$(package)_file_name=openssl-$($(package)_version).tar.gz
$(package)_sha256_hash=095f0b7b09116c0c5526422088058dc7e6e000aa14d22acca6a4e2babcdfef74

define $(package)_set_vars
$(package)_config_env=AR="$($(package)_ar)" RANLIB="$($(package)_ranlib)" CC="$($(package)_cc)"
$(package)_config_opts=--prefix=$(host_prefix) --openssldir=$(host_prefix)/etc/openssl no-zlib no-shared no-dso
$(package)_config_opts+=no-krb5 no-camellia no-capieng no-cast no-cms no-dtls1 no-gost no-gmp no-heartbeats no-idea no-jpake no-md2
$(package)_config_opts+=no-mdc2 no-rc5 no-rdrand no-rfc3779 no-rsax no-sctp no-seed no-sha0 no-static_engine no-whirlpool no-rc2 no-rc4 no-ssl2 no-ssl3
$(package)_config_opts+=$($(package)_cflags) $($(package)_cppflags)

ifeq ($(build_os),linux)
$(package)_config_opts+=-fPIC
ifeq ($(build_arch),x86_64)
$(package)_config_opts+=linux-x86_64
else ifeq ($(build_arch),i686)
$(package)_config_opts+=linux-generic32
else ifeq ($(build_arch),arm)
$(package)_config_opts+=linux-generic32
else ifeq ($(build_arch),aarch64)
$(package)_config_opts+=linux-generic64
else ifeq ($(build_arch),mipsel)
$(package)_config_opts+=linux-generic32
else ifeq ($(build_arch),mips)
$(package)_config_opts+=linux-generic32
endif
endif

ifeq ($(build_os),darwin)
ifeq ($(build_arch),x86_64)
$(package)_config_opts+=darwin64-x86_64-cc
endif
endif

ifeq ($(build_os),mingw32)
ifeq ($(build_arch),x86_64)
$(package)_config_opts+=mingw64
else ifeq ($(build_arch),i686)
$(package)_config_opts+=mingw
endif
endif
endef

define $(package)_preprocess_cmds
  sed -i.old "/define DATE/d" util/mkbuildinf.pl && \
  sed -i.old "s|engines apps test|engines|" Makefile.org
endef

define $(package)_config_cmds
  ./Configure $($(package)_config_opts)
endef

define $(package)_build_cmds
  $(MAKE) -j1 build_libs libcrypto.pc libssl.pc openssl.pc
endef

define $(package)_stage_cmds
  $(MAKE) INSTALL_PREFIX=$($(package)_staging_prefix_dir) -j1 install_sw
endef

define $(package)_postprocess_cmds
  rm -rf share bin etc
endef
