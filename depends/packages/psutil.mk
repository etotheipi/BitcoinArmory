package=psutil
$(package)_version=2.2.1
$(package)_download_path=https://pypi.python.org/packages/source/p/$(package)
$(package)_file_name=$(package)-$($(package)_version).tar.gz
$(package)_sha256_hash=a0e9b96f1946975064724e242ac159f3260db24ffa591c3da0a355361a3a337f
$(package)_dependencies=python3

define $(package)_stage_cmds
  $($(package)_prefixbin)python3.4 setup.py install --prefix=$($(package)_prefix)
endef
