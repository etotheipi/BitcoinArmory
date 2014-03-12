CXX = g++

ifdef DEBUG
CFLAGS=-g3 -Wall -pipe -fPIC
CXXFLAGS=-g3 -Wall -pipe -fPIC
else
CFLAGS=-O2 -pipe -fPIC
CXXFLAGS=-O2 -pipe -fPIC
endif

platform=$(shell uname)

#**************************************************************************
LINK = $(CXX)

OBJS = UniversalTimer.o BinaryData.o leveldb_wrapper.o StoredBlockObj.o BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o libcryptopp.a libleveldb.a

# This is a script created by goatpig which detects where the python 
# dependencies are and writes them to the pypaths.txt file. It defines :
# 		$(PYTHON_LIB) 
# 		$(PYVER) 
# 		$(PYTHON_INCLUDE)
# If this makefile doesn't work for you, you should manually modify
# pypaths.txt to define those three variables, and then comment out 
# DO_EXEC_WHEREISPY line (to prevent the script from attempting to run
# and overwriting the manual values).
ifneq ($(platform),Darwin)
# OS X will do its own thing.
DO_EXEC_WHEREISPY := $(shell ./whereispy.sh)
endif

include ./pypaths.txt

CPPFLAGS += $(ARMORY_CPPFLAGS) -Icryptopp -Ileveldb/include -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS
LDLIBS += -lpthread -Lleveldb -L$(PYTHON_LIB) -l$(PYVER)
SWIG_OPTS    += -c++ -python -classic -threads

SWIG_INC     += -I"$(PYTHON_INCLUDE)"
STATICPYTHON += "$(PYTHON_LIB)"

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
	rm pypaths.txt

hardclean:
	touch CppBlockUtils.i
	rm -f *.o *.out *.a
	rm -f CppBlockUtils_wrap.cxx 
	rm pypaths.txt
	$(MAKE) -C cryptopp clean
	$(MAKE) -C leveldb clean
	


