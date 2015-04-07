LINK = $(CXX)

# Export variables to make them available to cryptopp Makefile.
export AR
export CXX
export RANLIB

if TARGET_LINUX
CRYPTOPP_EXT=.a
else
if TARGET_WINDOWS
CRYPTOPP_EXT=.a
endif
endif

OBJS = UniversalTimer.o BinaryData.o lmdb_wrapper.o StoredBlockObj.o \
	BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o \
	BtcWallet.o LedgerEntry.o ScrAddrObj.o Blockchain.o BlockWriteBatcher.o \
	BDM_mainthread.o lmdbpp.o BDM_supportClasses.o \
	BlockDataViewer.o HistoryPager.o Progress.o \
	libcryptopp$(CRYPTOPP_EXT) mdb.o midl.o txio.o
#if python is specified, use it
#ifndef PYVER
#PYVER=python
#PYTHON_INCLUDES=$(shell python-config --includes )
#else
#PYTHON_INCLUDES=$(shell $(PYVER)-config --includes )
#endif

CPPFLAGS = $(ARMORY_CPPFLAGS) -Icryptopp -Imdb -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS
LDLIBS = -lpthread -Lmdb
SWIG_OPTS    = -c++ -python -threads

SWIG_INC     =

CXXCPP = $(CPPFLAGS) $(PYTHON_INCLUDES) -std=c++11

# each .o file depends on all .h files
EVERY_HEADER = bdmenums.h BDM_mainthread.h BDM_supportClasses.h BinaryData.h \
	Blockchain.h BlockDataManagerConfig.h BlockDataViewer.h BlockObj.h \
	BlockUtils.h BlockWriteBatcher.h BtcUtils.h BtcWallet.h EncryptionUtils.h \
	HistoryPager.h LedgerEntry.h lmdbpp.h lmdb_wrapper.h log.h \
	OS_TranslatePath.h PartialMerkle.h Progress.h ReorgUpdater.h ScrAddrObj.h \
	StoredBlockObj.h txio.h UniversalTimer.h util.h


#**************************************************************************

all: ../_CppBlockUtils.so ../qrc_img_resources.py

../_CppBlockUtils.so: $(OBJS) CppBlockUtils_wrap.o
	$(LINK) -shared -fPIC $(LDLIBS) $(LDFLAGS) $(CXXFLAGS) $(OBJS) $(STATICPYTHON) CppBlockUtils_wrap.o -o ../_CppBlockUtils.so

../qrc_img_resources.py: ../imgList.xml
	pyrcc4 -o ../qrc_img_resources.py ../imgList.xml


#**************************************************************************
libcryptopp$(CRYPTOPP_EXT): Makefile
	$(MAKE) -C cryptopp libcryptopp$(CRYPTOPP_EXT) RANLIB=$(RANLIB)
	mv cryptopp/libcryptopp$(CRYPTOPP_EXT) .

mdb.o: mdb/mdb.c mdb/lmdb.h mdb/midl.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -DNDEBUG -c mdb/mdb.c
midl.o: mdb/midl.c mdb/lmdb.h mdb/midl.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -DNDEBUG -c mdb/midl.c

%.o: %.cpp $(EVERY_HEADER)
	$(CXX) $(CXXCPP) $(CXXFLAGS) -c $<


CppBlockUtils_wrap.cxx: $(EVERY_HEADER) CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: $(EVERY_HEADER) CppBlockUtils_wrap.cxx
	$(CXX) $(SWIG_INC) $(CXXFLAGS) $(CXXCPP) -c CppBlockUtils_wrap.cxx

playground: ../_CppBlockUtils.so playground.cpp $(EVERY_HEADER)
	$(CXX) $(CXXCPP) $(CXXFLAGS) $(LDFLAGS) $(shell $(PYVER)-config --libs) -Wl,-rpath,$(PWD)/.. ../_CppBlockUtils.so -o playground playground.cpp

##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************
clean-local:
	touch CppBlockUtils.i
	rm -f *.o *.out *.a
	rm -f CppBlockUtils_wrap.cxx 
	$(MAKE) -C cryptopp clean
