CXX = g++
CC = gcc

ifdef DEBUG
CFLAGS=-g3 -Wall -pipe -fPIC
CXXFLAGS=-g3 -Wall -pipe -fPIC
else
CFLAGS = -O2 -pipe -fPIC
CXXFLAGS = -O2 -pipe -fPIC
endif

ifdef STATIC_LINK
CFLAGS += -static-libstdc++ -static-libgcc
CXXFLAGS += -static-libstdc++ -static-libgcc
endif

platform=$(shell uname)

ifeq ($(shell uname), Darwin)
MACOSX_DEPLOYMENT_TARGET=10.7
export MACOSX_DEPLOYMENT_TARGET
LDFLAGS += -undefined dynamic_lookup -headerpad_max_install_names
endif

#**************************************************************************
LINK = $(CXX)

OBJS = UniversalTimer.o BinaryData.o lmdb_wrapper.o StoredBlockObj.o \
	BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o \
	BtcWallet.o LedgerEntry.o ScrAddrObj.o Blockchain.o \
	BDM_mainthread.o lmdbpp.o BDM_supportClasses.o \
	BlockDataViewer.o HistoryPager.o Progress.o \
	libcryptopp.a mdb.o midl.o txio.o \
	DatabaseBuilder.o BlockchainScanner.o BlockDataMap.o

#if python is specified, use it
ifndef PYVER
PYVER=python
PYTHON_INCLUDES=$(shell python-config --includes )
else
PYTHON_INCLUDES=$(shell $(PYVER)-config --includes )
endif

CPPFLAGS += $(ARMORY_CPPFLAGS) -Icryptopp -Imdb -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS
LDLIBS += -lpthread -Lmdb
SWIG_OPTS    += -c++ -python -threads

SWIG_INC     += 

# rt library used for glibc <2.17. Safe to include for Linux but not OS X.
# Place at the end due to link order concerns involving Ubuntu 12.04.
ifneq ($(OS),Windows_NT)
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        LDLIBS += -lrt
    endif
endif

CXXCPP += $(CPPFLAGS) $(PYTHON_INCLUDES) -std=c++11

# OS X requires a little extra elbow grease to support C++11.
ifneq ($(OS),Windows_NT)
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        CXXCPP += -stdlib=libc++
        LDLIBS += -lc++
    endif
endif

# each .o file depends on all .h files
ALL_HEADERS_FOUND=$(wildcard *.h)
ALL_HEADERS=$(filter-out CppBlockUtils_wrap.h,$(ALL_HEADERS_FOUND))


#**************************************************************************

all: ../_CppBlockUtils.so ../qrc_img_resources.py

../_CppBlockUtils.so: $(OBJS) CppBlockUtils_wrap.o
	$(LINK) -shared -fPIC $(LDFLAGS) $(CXXFLAGS) $(OBJS) $(STATICPYTHON) CppBlockUtils_wrap.o $(LDLIBS) -o ../_CppBlockUtils.so

../qrc_img_resources.py: ../imgList.xml
	pyrcc4 -o ../qrc_img_resources.py ../imgList.xml


#**************************************************************************
libcryptopp.a: Makefile
	$(MAKE) -C cryptopp libcryptopp.a
	mv cryptopp/libcryptopp.a .

mdb.o: mdb/mdb.c mdb/lmdb.h mdb/midl.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -DNDEBUG -c mdb/mdb.c
midl.o: mdb/midl.c mdb/lmdb.h mdb/midl.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -DNDEBUG -c mdb/midl.c

%.o: %.cpp $(ALL_HEADERS)
	$(CXX) $(CXXCPP) $(CXXFLAGS) -c $<


CppBlockUtils_wrap.cxx: $(ALL_HEADERS) CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: $(ALL_HEADERS) CppBlockUtils_wrap.cxx
	$(CXX) $(SWIG_INC) $(CXXFLAGS) $(CXXCPP) -c CppBlockUtils_wrap.cxx

playground: ../_CppBlockUtils.so playground.cpp $(ALL_HEADERS)
	$(CXX) $(CXXCPP) $(CXXFLAGS) $(LDFLAGS) $(shell $(PYVER)-config --libs) -Wl,-rpath,$(PWD)/.. ../_CppBlockUtils.so -o playground playground.cpp

##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************
clean:
	touch CppBlockUtils.i
	rm -f *.o *.out *.a
	rm -f CppBlockUtils_wrap.cxx 
	$(MAKE) -C cryptopp clean
