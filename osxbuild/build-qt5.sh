#!/bin/sh

CWD=$(pwd)
mkdir qt5-temp install-qt5
cd qt5-temp
wget https://download.qt.io/archive/qt/5.2/5.2.1/single/qt-everywhere-opensource-src-5.2.1.tar.gz
tar -zxvf qt-everywhere-opensource-src-5.2.1.tar.gz
cd qt-everywhere-opensource-src-5.2.1
mkdir -p qtbase/mkspecs/macx-clang-linux
cp -f qtbase/mkspecs/macx-clang/Info.plist.lib qtbase/mkspecs/macx-clang-linux/
cp -f qtbase/mkspecs/macx-clang/Info.plist.app qtbase/mkspecs/macx-clang-linux/
cp -f qtbase/mkspecs/macx-clang/qplatformdefs.h qtbase/mkspecs/macx-clang-linux/
cp -f ../../qt5-qmake.conf qtbase/mkspecs/macx-clang-linux/qmake.conf
conf_flags="-prefix $CWD/install-qt5 -system-zlib -confirm-license -opensource"
conf_flags="$conf_flags -nomake examples -nomake tests"
conf_flags="$conf_flags -no-sql-db2 -no-sql-ibase -no-sql-oci -no-sql-tds"
conf_flags="$conf_flags -no-sql-mysql -no-sql-odbc -no-sql-psql -no-sql-sqlite"
conf_flags="$conf_flags -no-sql-sqlite2"
conf_flags="$conf_flags -release -pkg-config -v"
conf_flags="$conf_flags -xplatform macx-clang-linux"
conf_flags="$conf_flags -device-option MAC_SDK_PATH=/usr/share/MacOSX10.9.sdk/"
conf_flags="$conf_flags -device-option CROSS_COMPILE=x86_64-apple-darwin11-"
conf_flags="$conf_flags -device-option MAC_MIN_VERSION=10.7"
conf_flags="$conf_flags -device-option MAC_TARGET=x86_64-apple-darwin11"
conf_flags="$conf_flags -device-option MAC_LD64_VERSION=241.9"
conf_flasg="$conf_flags -skip qtx11extras -skip qtwinextras -skip qtdoc"
sed -i.old 's/if \[ "$$$$XPLATFORM_MAC" = "yes" \]; then xspecvals=$$$$(macSDKify/if \[ "$$$$BUILD_ON_MAC" = "yes" \]; then xspecvals=$$$$(macSDKify/' qtbase/configure
export PKG_CONFIG_SYSROOT_DIR=/
export PKG_CONFIG_LIBDIR=/usr/lib/pkgconfig
export PKG_CONFIG_PATH=/usr/share/pkgconfig
./configure $conf_flags
make
make install
cd ../..
rm -rf qt5-temp
