#!/bin/sh

CWD=$(pwd)

cd src/PyQt-gpl-5.4.1

python3 configure.py \
    --confirm-license \
    --qsci-api \
    --qmake=$CWD/qt-5.4.1/bin/qmake \
    --sip=$CWD/bin/sip \
    --sip-incdir=$CWD/include/python3.4m  \
    --sysroot=$CWD \
    --configuration=$CWD/patches/pyqt5/mingw.cfg \
    --spec win32-g++ \
    --static \
    --verbose

make V=1
make install
