#!/bin/sh

CWD=$(pwd)

cd src/qt-everywhere-opensource-src-5.4.1

conf_flags="-prefix $CWD/qt-5.4.1 -confirm-license -opensource"
conf_flags="$conf_flags -nomake examples -nomake tests"
conf_flags="$conf_flags -no-sql-db2 -no-sql-ibase -no-sql-oci -no-sql-tds"
conf_flags="$conf_flags -no-sql-mysql -no-sql-odbc -no-sql-psql -no-sql-sqlite"
conf_flags="$conf_flags -no-sql-sqlite2"
conf_flags="$conf_flags -release -static -openssl-linked -pkg-config -v"
conf_flags="$conf_flags -xplatform win32-g++ -device-option CROSS_COMPILE=x86_64-w64-mingw32-"
conf_flags="$conf_flags -skip qtx11extras -skip qtwinextras -skip qtmacextras"
conf_flags="$conf_flags -skip qtandroidextras -skip qtconnectivity"
conf_flags="$conf_flags -skip qtdeclarative -skip qtdoc -skip qtgraphicaleffects"
conf_flags="$conf_flags -skip qtimageformats -skip qtlocation -skip qtmultimedia"
conf_flags="$conf_flags -skip qtquick1 -skip qtquickcontrols -skip qtscript"
conf_flags="$conf_flags -skip qtsensors -skip qtserialport -skip qtsvg"
conf_flags="$conf_flags -skip qttools -skip qttranslations -skip qtxmlpatterns"
export PKG_CONFIG_SYSROOT_DIR=/
export PKG_CONFIG_LIBDIR=$CWD/lib/pkgconfig
export PKG_CONFIG_PATH=$CWD/share/pkgconfig
export CPATH=$CWD/include
./configure $conf_flags

rm qtactiveqt/src/tools/idc/Makefile
cat << EOF > qtactiveqt/src/tools/idc/Makefile
all:
install:
EOF

make
make install
