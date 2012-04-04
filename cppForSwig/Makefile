COMPILER = g++ 
#COMPILER_OPTS = -c -g -Wall -fPIC -D_DEBUG
COMPILER_OPTS = -c -O2 -pipe -fPIC

#**************************************************************************
LINKER = g++ 
OBJS = UniversalTimer.o BinaryData.o BinaryDataMMAP_POSIX.o BtcUtils.o BlockObj.o BlockObjRef.o BlockUtils.o EncryptionUtils.o libcryptopp.a

INCLUDE_OPTS += -Icryptopp -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS 
LIBRARY_OPTS += -lpthread -lpython2.7
SWIG_INC     += -I/usr/include/python2.7
SWIG_OPTS    += -c++ -python -classic

ifneq (exists, $(shell [ -d /usr/include/python2.7 ]  && echo exists ))
   SWIG_INC     = -I/usr/include/python2.6
   LIBRARY_OPTS = -lpthread -lpython2.6
   ifneq (exists, $(shell [ -d /usr/include/python2.6 ]  && echo exists ))
      SWIG_INC     = -I/usr/include/python2.5
      LIBRARY_OPTS = -lpthread -lpython2.5
   endif
endif


#**************************************************************************
all :
	make BlockUtilsTest.out
	
swig : $(OBJS) CppBlockUtils_wrap.o
	g++ -shared $(LIBRARY_OPTS) $(OBJS) CppBlockUtils_wrap.o -o ../_CppBlockUtils.so

BlockUtilsTest.out : $(OBJS) BlockUtilsTest.cpp
	$(LINKER) $(OBJS) -o BlockUtilsTest.out $(INCLUDE_OPTS) $(LIBRARY_OPTS) BlockUtilsTest.cpp


#**************************************************************************
libcryptopp.a: Makefile
	cd cryptopp; make libcryptopp.a; mv libcryptopp.a ..

UniversalTimer.o: UniversalTimer.h UniversalTimer.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) UniversalTimer.cpp

UniversalTimer.o: UniversalTimer.h UniversalTimer.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) UniversalTimer.cpp

BinaryData.o: BinaryData.h BinaryData.cpp BtcUtils.h 
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BinaryData.cpp

BinaryDataMMAP_POSIX.o: BinaryDataMMAP_POSIX.h BinaryDataMMAP_POSIX.cpp BtcUtils.h 
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BinaryDataMMAP_POSIX.cpp

BtcUtils.o: BtcUtils.h BtcUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BtcUtils.cpp

BlockObj.o: BinaryData.h BtcUtils.h BlockObjRef.h BlockObj.h BlockObj.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BlockObj.cpp

BlockObjRef.o: BinaryData.h BtcUtils.h BlockObj.h BlockObjRef.h BlockObjRef.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BlockObjRef.cpp

BlockUtils.o: BlockUtils.h BinaryData.h UniversalTimer.h BlockUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) BlockUtils.cpp

EncryptionUtils.o: BtcUtils.h BinaryData.h EncryptionUtils.h EncryptionUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) EncryptionUtils.cpp

CppBlockUtils_wrap.cxx: BlockUtils.h BinaryData.h BlockObj.h BlockObjRef.h UniversalTimer.h BlockUtils.h BlockUtils.cpp CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: BlockUtils.h  BinaryData.h UniversalTimer.h CppBlockUtils_wrap.cxx
	$(COMPILER) $(SWIG_INC) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) CppBlockUtils_wrap.cxx



##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************
clean:
	touch CppBlockUtils.i
	-rm *.o *.out 
	


