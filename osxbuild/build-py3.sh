#!/bin/sh

CWD=$(pwd)
SHA256SUM=8b743f56e9e50bf0923b9e9c45dd927c071d7aa56cd46569d8818add8cf01147
mkdir py3-temp install-py3
cd py3-temp
wget https://www.python.org/ftp/python/3.4.3/Python-3.4.3.tgz
if [ $(echo "$SHA256SUM  Python-3.4.3.tgz") -ne 0 ]
then
    echo "sha256sum mismatch"
    exit 1
fi
tar -zxvf Python-3.4.3.tgz
cd Python-3.4.3
echo "ac_cv_file__dev_ptmx=no" > config.site
echo "ac_cv_file__dev_ptc=no" >> config.site
patch -p1 --ignore-whitespace < $CWD/0010-cross-darwin-feature.patch
autoreconf
conf_flags="--prefix $CWD/install-py3 --host x86_64-apple-darwin11 --build x86_64-linux-gnu --disable-ipv6 --without-ensurepip --enable-framework=$CWD/install-py3"
export CC="clang -target x86_64-apple-darwin11 -mmacosx-version-min=10.7 --sysroot /usr/share/MacOSX10.9.sdk -mlinker-version=241.9"
export CXX="clang++ -target x86_64-apple-darwin11 -mmacosx-version-min=10.7 --sysroot /usr/share/MacOSX10.9.sdk -mlinker-version=241.9"
export READELF=x86_64-apple-darwin11-otool
export MACOSX_DEPLOYMENT_TARGET=10.7
export CONFIG_SITE=config.site
./configure $conf_flags
make
make install
cd ../..
rm -rf py3-temp
