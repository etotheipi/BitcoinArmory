package=native_psutil
$(package)_version=2.2.1
$(package)_download_path=https://pypi.python.org/packages/source/p/psutil
$(package)_file_name=psutil-$($(package)_version).tar.gz
$(package)_sha256_hash=a0e9b96f1946975064724e242ac159f3260db24ffa591c3da0a355361a3a337f
$(package)_dependencies=native_python2
$(package)_build_env=CC="$($(package)_cc)" LD="$($(package)_cc)" CFLAGS="$($(package)_cflags)"

define $(package)_build_cmds
  $($(package)_prefixbin)/python2 setup.py build
endef

define $(package)_stage_cmds
  $($(package)_prefixbin)/python2 setup.py install --root=$($(package)_staging_dir) --prefix=$($(package)_prefix)
endef
