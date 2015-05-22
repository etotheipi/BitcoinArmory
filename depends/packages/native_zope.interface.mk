package=native_zope.interface
$(package)_version=4.1.2
$(package)_download_path=https://pypi.python.org/packages/source/z/zope.interface
$(package)_file_name=zope.interface-$($(package)_version).tar.gz
$(package)_sha256_hash=441fefcac1fbac57c55239452557d3598571ab82395198b2565a29d45d1232f6
$(package)_dependencies=native_python3

define $(package)_build_cmds
  $($(package)_prefixbin)/python3 setup.py build
endef

define $(package)_stage_cmds
  $($(package)_prefixbin)/python3 setup.py install --root=$($(package)_staging_dir) --prefix=$($(package)_prefix)
endef
