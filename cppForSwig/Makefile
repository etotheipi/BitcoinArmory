include ../config.mk

COMPILER = g++ 

ifdef DEBUG
COMPILER_OPTS = -c -g -Wall -fPIC 
else
COMPILER_OPTS = -c -O2 -pipe -fPIC 
endif

#**************************************************************************
LINKER = g++ 
OBJS = UniversalTimer.o BinaryData.o leveldb_wrapper.o StoredBlockObj.o BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o libcryptopp.a libleveldb.a


DEPSDIR ?= /usr

INCLUDE_OPTS += -Icryptopp -Ileveldb/include -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS 
LIBRARY_OPTS += -lpthread -Lleveldb -L/usr/lib/python2.7/config-x86_64-linux-gnu/ -lpython2.7
SWIG_OPTS    += -c++ -python -classic -threads


UNAME := $(shell uname)

ifeq ($(UNAME), Darwin)
   # This configuration assumes you have setup your 10.X.X system like
   # Red Emerald in this thread: 
   #    https://bitcointalk.org/index.php?topic=73648.msg976015#msg976015
   # The makefile updates he shows are already tied into this if/else branch
   PYVER 		 += `python -c 'import sys; print str(sys.version_info[0]) + "." + str(sys.version_info[1])'`
   SWIG_INC     += -I"/usr/include/python$(PYVER)"
   STATICPYTHON +=   "/usr/lib/python$(PYVER)/config/libpython$(PYVER).a"
else
   PYVER 		 += `python2 -c 'import sys; print str(sys.version_info[0]) + "." + str(sys.version_info[1])'`
   SWIG_INC     += -I"$(DEPSDIR)/include/python$(PYVER)"
   #STATICPYTHON +=   "$(DEPSDIR)/lib/libpython$(PYVER).a"
   STATICPYTHON =


endif


#**************************************************************************
all :
	make BlockUtilsTest.out

swig : $(OBJS) CppBlockUtils_wrap.o
	g++ -shared -fPIC $(LIBRARY_OPTS) $(OBJS) $(STATICPYTHON) CppBlockUtils_wrap.o -o ../_CppBlockUtils.so
	pyrcc4 -o ../qrc_img_resources.py ../imgList.xml

BlockUtilsTest.out : $(OBJS) BlockUtilsTest.cpp
	$(LINKER) $(OBJS) -o BlockUtilsTest.out $(INCLUDE_OPTS) $(LIBRARY_OPTS) BlockUtilsTest.cpp


#**************************************************************************
libcryptopp.a: Makefile
	cd cryptopp; make libcryptopp.a; mv libcryptopp.a ..

libleveldb.a: Makefile
	cd leveldb; make libleveldb.a; mv libleveldb.a ..

UniversalTimer.o: UniversalTimer.h UniversalTimer.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) UniversalTimer.cpp

BinaryData.o: BinaryData.h BinaryData.cpp BtcUtils.h log.h
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BinaryData.cpp

BtcUtils.o: BtcUtils.h BtcUtils.cpp log.h
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BtcUtils.cpp

BlockObj.o: log.h BinaryData.h BtcUtils.h BlockObj.h BlockObj.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BlockObj.cpp

StoredBlockObj.o: log.h BtcUtils.h BinaryData.h StoredBlockObj.h StoredBlockObj.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) StoredBlockObj.cpp

leveldb_wrapper.o: log.h BtcUtils.h BinaryData.h leveldb_wrapper.h leveldb_wrapper.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) leveldb_wrapper.cpp

BlockUtils.o: log.h BlockUtils.h BinaryData.h UniversalTimer.h PartialMerkle.h BlockUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BlockUtils.cpp

EncryptionUtils.o: log.h BtcUtils.h BinaryData.h EncryptionUtils.h EncryptionUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) EncryptionUtils.cpp

CppBlockUtils_wrap.cxx: log.h BlockUtils.h BinaryData.h BlockObj.h UniversalTimer.h BlockUtils.h BlockUtils.cpp CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: log.h BlockUtils.h  BinaryData.h UniversalTimer.h CppBlockUtils_wrap.cxx
	$(COMPILER) $(SWIG_INC) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) CppBlockUtils_wrap.cxx



##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************
clean:
	touch CppBlockUtils.i
	rm -f *.o *.out 
        #cd cryptopp; make clean;


