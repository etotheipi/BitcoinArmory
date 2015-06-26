package=native_qt48
$(package)_version=4.8.6
$(package)_download_path=http://download.qt.io/archive/qt/4.8/$($(package)_version)
$(package)_file_name=qt-everywhere-opensource-src-$($(package)_version).tar.gz
$(package)_sha256_hash=8b14dd91b52862e09b8e6a963507b74bc2580787d171feda197badfa7034032c
$(package)_dependencies=native_freetype native_dbus native_libX11 native_xproto native_libXext native_libICE native_libSM

define $(package)_set_vars
$(package)_config_opts  = -prefix $(host_prefix)/qt-native -headerdir $(host_prefix)/qt-native/include/qt4 -bindir $(build_prefix)/bin
$(package)_config_opts += -release -no-separate-debug-info -opensource -confirm-license
$(package)_config_opts += -stl -qt-zlib

$(package)_config_opts += -nomake examples -nomake tests -nomake translations -nomake demos -nomake docs
$(package)_config_opts += -no-audio-backend -no-glib -no-nis -no-cups -no-iconv -no-gif -no-pch
$(package)_config_opts += -no-xkb -no-xrender -no-xrandr -no-xfixes -no-xcursor -no-xinerama -no-xsync -no-xinput -no-mitshm -no-xshape
$(package)_config_opts += -no-libtiff -no-fontconfig -no-openssl
$(package)_config_opts += -no-sql-db2 -no-sql-ibase -no-sql-oci -no-sql-tds -no-sql-mysql
$(package)_config_opts += -no-sql-odbc -no-sql-psql -no-sql-sqlite -no-sql-sqlite2
$(package)_config_opts += -no-xmlpatterns -no-multimedia -no-phonon -no-scripttools -no-declarative
$(package)_config_opts += -no-phonon-backend -no-webkit -no-javascript-jit -no-script
$(package)_config_opts += -no-svg -no-libjpeg -no-libtiff -no-libpng -no-libmng -no-qt3support -no-opengl

$(package)_config_opts_x86_64_linux  += -platform linux-g++-64
$(package)_config_opts_i686_linux  = -platform linux-g++-32
$(package)_build_env  = QT_RCC_TEST=1
endef

define $(package)_preprocess_cmds
  sed -i.old "s|/usr/X11R6/lib64|$(build_prefix)/lib|" mkspecs/*/*.conf && \
  sed -i.old "s|/usr/X11R6/lib|$(build_prefix)/lib|" mkspecs/*/*.conf && \
  sed -i.old "s|/usr/X11R6/include|$(build_prefix)/include|" mkspecs/*/*.conf
endef

define $(package)_config_cmds
  export PKG_CONFIG_SYSROOT_DIR=/ && \
  export PKG_CONFIG_LIBDIR=$(build_prefix)/lib/pkgconfig && \
  export PKG_CONFIG_PATH=$(build_prefix)/share/pkgconfig  && \
  export CPATH=$(build_prefix)/include && \
  ./configure $($(package)_config_opts)
endef

define $(package)_build_cmds
  export CPATH=$(build_prefix)/include && \
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) INSTALL_ROOT=$($(package)_staging_dir) install  
endef

define $(package)_postprocess_cmds
  rm -rf lib/cmake/ lib/*.prl lib/*.la && \
  mv bin/qmake bin/qmake-native
endef
