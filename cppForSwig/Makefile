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

OBJS = UniversalTimer.o BinaryData.o leveldb_wrapper.o StoredBlockObj.o BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o libcryptopp.a libleveldb.a sighandler.o

#if python is specified, use it
ifndef PYVER
PYTHON_INCLUDES=$(shell python-config --includes )
else
PYTHON_INCLUDES=$(shell $(PYVER)-config --includes )
endif

CPPFLAGS += $(ARMORY_CPPFLAGS) -Icryptopp -Ileveldb/include -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS
LDLIBS += -lpthread -Lleveldb
SWIG_OPTS    += -c++ -python -classic -threads

SWIG_INC     += $(PYTHON_INCLUDES)

CXXCPP += $(CPPFLAGS)


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
StoredBlockObj.o: log.h BtcUtils.h BinaryData.h
leveldb_wrapper.o: log.h BtcUtils.h BinaryData.h
BlockUtils.o: log.h BinaryData.h UniversalTimer.h PartialMerkle.h
EncryptionUtils.o: log.h BtcUtils.h BinaryData.h
CppBlockUtils_wrap.cxx: log.h BlockUtils.h BinaryData.h BlockObj.h UniversalTimer.h BlockUtils.h BlockUtils.cpp CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: log.h BlockUtils.h  BinaryData.h UniversalTimer.h CppBlockUtils_wrap.cxx
	$(CXX) $(SWIG_INC) $(CXXFLAGS) $(CXXCPP) -c CppBlockUtils_wrap.cxx



##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************
clean:
	touch CppBlockUtils.i
	rm -f *.o *.out *.a
	rm -f CppBlockUtils_wrap.cxx 
	$(MAKE) -C cryptopp clean
	$(MAKE) -C leveldb clean
	$(MAKE) -C gtest clean

