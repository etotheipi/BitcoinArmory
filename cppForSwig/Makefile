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
LDFLAGS += -undefined dynamic_lookup 
endif

#**************************************************************************
LINK = $(CXX)

OBJS = UniversalTimer.o BinaryData.o leveldb_wrapper.o StoredBlockObj.o \
	BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o Util.o \
	BtcWallet.o LedgerEntry.o ScrAddrObj.o Blockchain.o BlockWriteBatcher.o \
	libcryptopp.a libleveldb.a

#if python is specified, use it
ifndef PYVER
PYVER=python
PYTHON_INCLUDES=$(shell python-config --includes )
else
PYTHON_INCLUDES=$(shell $(PYVER)-config --includes )
endif

CPPFLAGS += $(ARMORY_CPPFLAGS) -Icryptopp -Ileveldb/include -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS
LDLIBS += -lpthread -Lleveldb
SWIG_OPTS    += -c++ -python -classic -threads

SWIG_INC     += 

CXXCPP += $(CPPFLAGS) $(PYTHON_INCLUDES)


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

%.o: %.cpp %.h
	$(CXX) $(CXXCPP) $(CXXFLAGS) -c $<

BinaryData.o: BtcUtils.h log.h
BtcUtils.o: log.h
BlockObj.o: BinaryData.h BtcUtils.h
BtcWallet.o: BinaryData.h BlockObj.h ScrAddrObj.h BlockUtils.h
LedgerEntry.o: BinaryData.h BtcUtils.h BlockObj.h
ScrAddrObj.o: BinaryData.h BtcUtils.h BlockObj.h LedgerEntry.h
StoredBlockObj.o: log.h BtcUtils.h BinaryData.h
leveldb_wrapper.o: log.h BtcUtils.h BinaryData.h
BlockUtils.o: log.h BinaryData.h UniversalTimer.h PartialMerkle.h
EncryptionUtils.o: log.h BtcUtils.h BinaryData.h
CppBlockUtils_wrap.cxx: log.h BlockUtils.h BinaryData.h BlockObj.h UniversalTimer.h BlockUtils.h BtcWallet.h LedgerEntry.h StoredBlockObj.h Blockchain.h CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: log.h BlockUtils.h  BinaryData.h UniversalTimer.h CppBlockUtils_wrap.cxx
	$(CXX) $(SWIG_INC) $(CXXFLAGS) $(CXXCPP) -c CppBlockUtils_wrap.cxx

playground: ../_CppBlockUtils.so playground.cpp BlockUtils.h ScrAddrObj.h LedgerEntry.h
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
	


