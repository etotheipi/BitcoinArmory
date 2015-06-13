# Pretty much taken verbatim from Bitcoin Core
PACKAGE=native_qt
$(package)_version=5.2.1
$(package)_download_path=http://download.qt-project.org/official_releases/qt/5.2/$($(package)_version)/single
$(package)_file_name=qt-everywhere-opensource-src-$($(package)_version).tar.gz
$(package)_sha256_hash=84e924181d4ad6db00239d87250cc89868484a14841f77fb85ab1f1dbdcd7da1
$(package)_dependencies=openssl
$(package)_linux_dependencies=freetype fontconfig dbus libxcb libX11 xproto libXext
$(package)_qt_libs=corelib network gui
$(package)_patches=mac-qmake.conf fix-xcb-include-order.patch qt5-tablet-osx.patch qt5-yosemite.patch

define $(package)_set_vars
$(package)_config_opts_release = -release
$(package)_config_opts_debug   = -debug
$(package)_config_opts += -opensource -confirm-license
$(package)_config_opts += -nomake examples -nomake tests
$(package)_config_opts += -no-sql-db2 -no-sql-ibase -no-sql-oci -no-sql-tds -no-sql-mysql
$(package)_config_opts += -no-sql-odbc -no-sql-psql -no-sql-sqlite -no-sql-sqlite2
$(package)_config_opts += -skip qtandroidextras -skip qtconnectivity
$(package)_config_opts += -skip qtdeclarative -skip qtdoc -skip qtgraphicaleffects
$(package)_config_opts += -skip qtimageformats -skip qtlocation -skip qtmultimedia
$(package)_config_opts += -skip qtquick1 -skip qtquickcontrols -skip qtscript
$(package)_config_opts += -skip qtsensors -skip qtserialport -skip qtsvg
$(package)_config_opts += -skip qttools -skip qttranslations
$(package)_config_opts += -skip qtwinextras -skip qtx11extras -skip qtxmlpatterns

# NB: Due to minimum Mac requirements, disable post-SSE3 assembly.
$(package)_config_opts += -no-sse4.1 -no-sse4.2 -no-avx -no-avx2

$(package)_config_opts += -prefix $(host_prefix)/qt-native -bindir $(build_prefix)/bin
$(package)_config_opts += -system-zlib -v -silent -pkg-config

$(package)_config_opts_linux  = -qt-xkbcommon -qt-xcb  -no-eglfs -no-linuxfb -system-freetype -no-sm -fontconfig -no-xinput2 -no-libudev -no-egl -no-opengl
$(package)_config_opts_arm_linux  = -platform linux-g++ -xplatform $(host)
$(package)_config_opts_i686_linux  = -xplatform linux-g++-32
$(package)_config_opts_mingw32  = -no-opengl -xplatform win32-g++ -device-option CROSS_COMPILE="$(host)-"
$(package)_build_env  = QT_RCC_TEST=1
endef

define $(package)_preprocess_cmds
  sed -i.old "s/src_plugins.depends = src_sql src_xml src_network/src_plugins.depends = src_xml src_network/" qtbase/src/src.pro && \
  sed -i.old "/XIproto.h/d" qtbase/src/plugins/platforms/xcb/qxcbxsettings.cpp && \
  sed -i.old 's/if \[ "$$$$XPLATFORM_MAC" = "yes" \]; then xspecvals=$$$$(macSDKify/if \[ "$$$$BUILD_ON_MAC" = "yes" \]; then xspecvals=$$$$(macSDKify/' qtbase/configure && \
  mkdir -p qtbase/mkspecs/macx-clang-linux &&\
  cp -f qtbase/mkspecs/macx-clang/Info.plist.lib qtbase/mkspecs/macx-clang-linux/ &&\
  cp -f qtbase/mkspecs/macx-clang/Info.plist.app qtbase/mkspecs/macx-clang-linux/ &&\
  cp -f qtbase/mkspecs/macx-clang/qplatformdefs.h qtbase/mkspecs/macx-clang-linux/ &&\
  cp -f $($(package)_patch_dir)/mac-qmake.conf qtbase/mkspecs/macx-clang-linux/qmake.conf && \
  echo "QMAKE_CFLAGS     += $($(package)_cflags) $($(package)_cppflags)" >> qtbase/mkspecs/common/gcc-base.conf && \
  echo "QMAKE_CXXFLAGS   += $($(package)_cxxflags) $($(package)_cppflags)" >> qtbase/mkspecs/common/gcc-base.conf && \
  echo "QMAKE_LFLAGS     += $($(package)_ldflags)" >> qtbase/mkspecs/common/gcc-base.conf && \
  sed -i.old "s|QMAKE_CFLAGS            = |QMAKE_CFLAGS            = $($(package)_cflags) $($(package)_cppflags) |" qtbase/mkspecs/win32-g++/qmake.conf && \
  sed -i.old "s|QMAKE_LFLAGS            = |QMAKE_LFLAGS            = $($(package)_ldflags) |" qtbase/mkspecs/win32-g++/qmake.conf && \
  sed -i.old "s|QMAKE_CXXFLAGS          = |QMAKE_CXXFLAGS            = $($(package)_cxxflags) $($(package)_cppflags) |" qtbase/mkspecs/win32-g++/qmake.conf
endef

define $(package)_config_cmds
  export PKG_CONFIG_SYSROOT_DIR=/ && \
  export PKG_CONFIG_LIBDIR=$(host_prefix)/lib/pkgconfig && \
  export PKG_CONFIG_PATH=$(host_prefix)/share/pkgconfig  && \
  export CPATH=$(host_prefix)/include && \
  ./configure $($(package)_config_opts) && \
  sed -i.old "1s|^|export INSTALL_ROOT=$($(package)_staging_dir)\n|" Makefile
endef

define $(package)_build_cmds
export CPATH=$(host_prefix)/include && \
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) install
endef

define $(package)_postprocess_cmds
  mv bin/qmake bin/qmake-native
endef
