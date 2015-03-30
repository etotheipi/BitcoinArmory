package=native_psutil
$(package)_version=2.2.1
$(package)_download_path=https://pypi.python.org/packages/source/p/psutil
$(package)_file_name=psutil-$($(package)_version).tar.gz
$(package)_sha256_hash=a0e9b96f1946975064724e242ac159f3260db24ffa591c3da0a355361a3a337f
$(package)_dependencies=native_python2

define $(package)_stage_cmds
  $($(package)_prefixbin)/python setup.py install --prefix=$($(package)_staging_prefix_dir)
endef
