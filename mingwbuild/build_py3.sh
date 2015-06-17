#!/bin/sh

CWD=$(pwd)

cd src/Python-3.4.3

# created by patches
rm -f Misc/config_mingw Misc/cross_mingw32 Python/fileblocks.c

for i in ../../patches/python3-arch/*; do patch -Np1 < $i; done
autoreconf -vfi

touch Include/graminit.h
touch Python/graminit.c
touch Parser/Python.asdl
touch Parser/asdl.py
touch Parser/asdl_c.py
touch Include/Python-ast.h
touch Python/Python-ast.c
echo \"\" > Parser/pgen.stamp

export ac_cv_working_tzset=no

conf_flags="--prefix=$CWD --host=x86_64-w64-mingw32 --build=x86_64-linux-gnu --enable-shared --with-threads --without-ensurepip"
MSYSTEM=MINGW ./configure $conf_flags OPT= CFLAGS="-fwrapv -D__USE_MINGW_ANSI_STDIO=1 -DNDEBUG" CXXFLAGS="-fwrapv -D__USE_MINGW_ANSI_STDIO=1 -DNDEBUG" LDFLAGS="-static -static-libgcc" CPPFLAGS="-static"
sed -i "1s|^|*static*\n|" Modules/Setup.local
MSYSTEM=MINGW ./configure $conf_flags OPT= CFLAGS="-fwrapv -D__USE_MINGW_ANSI_STDIO=1 -DNDEBUG" CXXFLAGS="-fwrapv -D__USE_MINGW_ANSI_STDIO=1 -DNDEBUG" LDFLAGS="-static -static-libgcc" CPPFLAGS="-static"

sed -i "s/\#cmath cmathmodule.c _math.c/cmath cmathmodule.c _math.c/" Modules/Setup
sed -i "s/\#math mathmodule.c _math.c/math mathmodule.c _math.c/" Modules/Setup
sed -i "s/\#_struct _struct.c/_struct _struct.c/" Modules/Setup
sed -i "s/\#_random _randommodule.c/_random _randommodule.c/" Modules/Setup
sed -i "s/\#mmap mmapmodule.c/mmap mmapmodule.c/" Modules/Setup
sed -i "s/\#_csv _csv.c/_csv _csv.c/" Modules/Setup
sed -i "s/\#_socket socketmodule.c/_socket socketmodule.c/" Modules/Setup
sed -i "s/\#_md5 md5module.c/_md5 md5module.c/" Modules/Setup
sed -i "s/\#_sha1 sha1module.c/_sha1 sha1module.c/" Modules/Setup
sed -i "s/\#_sha256 sha256module.c/_sha256 sha256module.c/" Modules/Setup
sed -i "s/\#_sha512 sha512module.c/_sha512 sha512module.c/" Modules/Setup
grep -q '^_opcode _opcode.c' Modules/Setup && true || echo '_opcode _opcode.c' >> Modules/Setup

sed -i "/exts.append\( Extension\('_csv', \['_csv.c'\]\) \)/aexts.append( Extension('_CppBlockUtils', ['CppBlockUtils_wrap.cxx', 'BDM_mainthread.cpp', 'BDM_supportClasses.cpp', 'BinaryData.cpp', 'Blockchain.cpp', 'BlockDataViewer.cpp', 'BlockObj.cpp', 'BlockUtils.cpp', 'BlockWriteBatcher.cpp', 'BtcUtils.cpp', 'BtcWallet.cpp', 'EncryptionUtils.cpp', 'FileMap.cpp', 'HistoryPager.cpp', 'LedgerEntry.cpp', 'lmdbpp.cpp', 'lmdb_wrapper.cpp', 'Progress.cpp', 'ScrAddrObj.cpp', 'sighandler.cpp', 'SSHeaders.cpp', 'StoredBlockObj.cpp', 'txio.cpp', 'UniversalTimer.cpp'], library_dirs=['$CWD/../cppForSwig'], libraries=['cryptopp'], extra_compile_args=['-std=c++11']) )/" setup.py

make

sed -i "s/^LIBS=/LIBS=-lwsock32 -lws2_32/" Makefile
sed -i 's|^LDSHARED.*$(CC)|LDSHARED=$(CXX)|' Makefile
sed -i 's|^BLDSHARED.*$(CC)|BLDSHARED=$(CXX)|' Makefile
sed -i 's|^MAINCC.*$(CC)|MAINCC=$(CXX)|' Makefile

sed -i "/CONFIGURE_CFLAGS_NODIST=/d" Makefile

make CFLAGS="-std=c++11"
make install
