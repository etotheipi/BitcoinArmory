package=twisted
$(package)_version=15.0.0
$(package)_download_path=https://pypi.python.org/packages/source/T/Twisted
$(package)_file_name=Twisted-$($(package)_version).tar.bz2
$(package)_sha256_hash=ac609262253057cf2aeb9dc049ba7877d646f31b4caef06a50189a023df46b51
$(package)_dependencies=python3 zope.interface

define $(package)_stage_cmds
  $($(package)_prefixbin)python3 setup.py install --prefix=$($(package)_prefix)
endef
