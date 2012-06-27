COMPILER = g++ 
#COMPILER_OPTS = -c -g -Wall -fPIC -D_DEBUG
COMPILER_OPTS = -c -O2 -pipe -fPIC 

#**************************************************************************
LINKER = g++ 
OBJS = UniversalTimer.o BinaryData.o FileDataPtr.o BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o libcryptopp.a libleveldb.a


DEPSDIR ?= /usr

INCLUDE_OPTS += -Icryptopp -Ileveldb/include -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS 
LIBRARY_OPTS += -lpthread 
SWIG_INC     += -I"$(DEPSDIR)/include/python2.7"
STATICPYTHON +=   "$(DEPSDIR)/lib/libpython2.7.a"
SWIG_OPTS    += -c++ -python -classic

ifneq (exists, $(shell [ -d "$(DEPSDIR)/include/python2.7" ]  && echo exists ))
   SWIG_INC     = -I"$(DEPSDIR)/include/python2.6"
   STATICPYTHON = "$(DEPSDIR)/lib/libpython2.6.a"
   ifneq (exists, $(shell [ -d "$(DEPSDIR)/include/python2.6" ]  && echo exists ))
      SWIG_INC     = -I"$(DEPSDIR)/include/python2.5"
      STATICPYTHON =   "$(DEPSDIR)/lib/libpython2.5.a"
   endif
endif


#**************************************************************************
all :
	make BlockUtilsTest.out
	
swig : $(OBJS) CppBlockUtils_wrap.o
	g++ -shared $(LIBRARY_OPTS) $(OBJS) $(STATICPYTHON) CppBlockUtils_wrap.o -o ../_CppBlockUtils.so
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

BinaryData.o: BinaryData.h BinaryData.cpp BtcUtils.h 
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BinaryData.cpp

FileDataPtr.o: FileDataPtr.h BtcUtils.h BinaryData.h FileDataPtr.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) FileDataPtr.cpp

BtcUtils.o: BtcUtils.h BtcUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BtcUtils.cpp

BlockObj.o: BinaryData.h BtcUtils.h BlockObj.h BlockObj.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BlockObj.cpp

BlockUtils.o: BlockUtils.h BinaryData.h UniversalTimer.h BlockUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BlockUtils.cpp

EncryptionUtils.o: BtcUtils.h BinaryData.h EncryptionUtils.h EncryptionUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) EncryptionUtils.cpp

CppBlockUtils_wrap.cxx: BlockUtils.h BinaryData.h BlockObj.h UniversalTimer.h BlockUtils.h BlockUtils.cpp CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: BlockUtils.h  BinaryData.h UniversalTimer.h CppBlockUtils_wrap.cxx
	$(COMPILER) $(SWIG_INC) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) CppBlockUtils_wrap.cxx



##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************
clean:
	touch CppBlockUtils.i
	rm -f *.o *.out libleveldb.a libcryptopp.a cryptopp/*.out
	cd cryptopp; make clean;
	


