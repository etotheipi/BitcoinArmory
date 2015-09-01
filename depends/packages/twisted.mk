package=twisted
$(package)_version=15.0.0
$(package)_download_path=https://pypi.python.org/packages/source/T/Twisted
$(package)_file_name=Twisted-$($(package)_version).tar.bz2
$(package)_sha256_hash=ac609262253057cf2aeb9dc049ba7877d646f31b4caef06a50189a023df46b51
$(package)_dependencies=python2 native_python2 native_zope.interface
$(package)_build_env=CC="$($(package)_cc)" LD="$($(package)_cc)" LDSHARED="$($(package)_cc) -shared" CFLAGS="-I$(host_prefix)/include/python2.7 $($(package)_cflags)" LDFLAGS="$($(package)_ldflags)"

define $(package)_build_cmds
  $($(package)_prefix)/native/bin/python2 setup.py build
endef

define $(package)_stage_cmds
  $($(package)_prefix)/native/bin/python2 setup.py install --root=$($(package)_staging_dir) --prefix=$($(package)_prefix)
endef
