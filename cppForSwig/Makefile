CXX = g++

ifdef DEBUG
CFLAGS=-g3 -Wall -pipe -fPIC
CXXFLAGS=-g3 -Wall -pipe -fPIC
else
CFLAGS=-O2 -pipe -fPIC
CXXFLAGS=-O2 -pipe -fPIC
endif

platform=$(shell uname)

ifeq ($(shell uname), Darwin)
MACOSX_DEPLOYMENT_TARGET=10.7
export MACOSX_DEPLOYMENT_TARGET
LDFLAGS += -undefined dynamic_lookup -headerpad_max_install_names
endif

#**************************************************************************
LINK = $(CXX)

OBJS = UniversalTimer.o BinaryData.o leveldb_wrapper.o StoredBlockObj.o \
	BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o \
	BtcWallet.o LedgerEntry.o ScrAddrObj.o Blockchain.o BlockWriteBatcher.o \
	BDM_mainthread.o \
	libcryptopp.a libleveldb.a 

#if python is specified, use it
ifndef PYVER
PYVER=python
PYTHON_INCLUDES=$(shell python-config --includes )
else
PYTHON_INCLUDES=$(shell $(PYVER)-config --includes )
endif

CPPFLAGS += $(ARMORY_CPPFLAGS) -Icryptopp -Ileveldb/include -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS -std=c++11
LDLIBS += -lpthread -Lleveldb
SWIG_OPTS    += -c++ -python -classic -threads

SWIG_INC     += 

CXXCPP += $(CPPFLAGS) $(PYTHON_INCLUDES)

# each .o file depends on all .h files
ALL_HEADERS_FOUND=$(wildcard *.h)
ALL_HEADERS=$(filter-out CppBlockUtils_wrap.h,$(ALL_HEADERS_FOUND))


#**************************************************************************

all: ../_CppBlockUtils.so ../qrc_img_resources.py

../_CppBlockUtils.so: $(OBJS) CppBlockUtils_wrap.o
	$(LINK) -shared -fPIC $(LDLIBS) $(LDFLAGS) $(CXXFLAGS) $(OBJS) $(STATICPYTHON) CppBlockUtils_wrap.o -o ../_CppBlockUtils.so

../qrc_img_resources.py: ../imgList.xml
	pyrcc4 -o ../qrc_img_resources.py ../imgList.xml


#**************************************************************************
libcryptopp.a: Makefile
	$(MAKE) -C cryptopp libcryptopp.a
	mv cryptopp/libcryptopp.a .

libleveldb.a: Makefile
	$(MAKE) -C leveldb libleveldb.a
	mv leveldb/libleveldb.a .

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
	rm -f pypaths.txt

hardclean:
	touch CppBlockUtils.i
	rm -f *.o *.out *.a
	rm -f CppBlockUtils_wrap.cxx 
	rm -f pypaths.txt
	$(MAKE) -C cryptopp clean
	$(MAKE) -C leveldb clean
