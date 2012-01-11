COMPILER = g++ 
#COMPILER_OPTS = -c -g -Wall -D_DEBUG
COMPILER_OPTS = -c -march=native -O2 -pipe 


LINKER = g++ 
OBJS = UniversalTimer.o BinaryData.o BtcUtils.o BlockObj.o BlockObjRef.o BlockUtils.o EncryptionUtils.o

# I used to link to the cryptopp directory included with the repo,
# but ever since adding AES, I've found that I need to link to the
# installed libraries...
INCLUDE_OPTS += -I/usr/include/cryptopp -Icryptopp -fPIC -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS 
LIBRARY_OPTS += -lcryptopp -lpthread
SWIG_INC += -I/usr/include/python2.7

SWIG_OPTS    += -c++ -python -classic

# Use the following line if you get an error about needing the classic option in swig

ifneq (exists, $(shell [ -d /usr/include/python2.7 ]  && echo exists ))
   SWIG_INC = -I/usr/include/python2.6
   ifneq (exists, $(shell [ -d /usr/include/python2.6 ]  && echo exists ))
      SWIG_INC = -I/usr/include/python2.5
   endif
endif

all :
	make BlockUtilsTest.out
	
swig : $(OBJS) CppBlockUtils_wrap.o
	g++ -shared $(LIBRARY_OPTS) $(OBJS) CppBlockUtils_wrap.o -o ../_CppBlockUtils.so

BlockUtilsTest.out : $(OBJS) BlockUtilsTest.cpp
	$(LINKER) $(OBJS) -o BlockUtilsTest.out $(INCLUDE_OPTS) $(LIBRARY_OPTS) BlockUtilsTest.cpp


#**************************************************************************
# Rules for performing the compilation of each individual object file.

UniversalTimer.o: UniversalTimer.h UniversalTimer.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) UniversalTimer.cpp

BinaryData.o: BinaryData.h BinaryData.cpp BtcUtils.h 
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) BinaryData.cpp

BtcUtils.o: BtcUtils.h BtcUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) BtcUtils.cpp

BlockObj.o: BinaryData.h BtcUtils.h BlockObjRef.h BlockObj.h BlockObj.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) BlockObj.cpp

BlockObjRef.o: BinaryData.h BtcUtils.h BlockObj.h BlockObjRef.h BlockObjRef.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) BlockObjRef.cpp

BlockUtils.o: BlockUtils.h BinaryData.h UniversalTimer.h BlockUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) BlockUtils.cpp

EncryptionUtils.o: BtcUtils.h BinaryData.h EncryptionUtils.h EncryptionUtils.cpp
	$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) EncryptionUtils.cpp

CppBlockUtils_wrap.cxx: BlockUtils.h BinaryData.h BlockObj.h BlockObjRef.h UniversalTimer.h BlockUtils.h BlockUtils.cpp CppBlockUtils.i
	swig $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: BlockUtils.h  BinaryData.h UniversalTimer.h CppBlockUtils_wrap.cxx
	$(COMPILER) $(SWIG_INC) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) CppBlockUtils_wrap.cxx

#ECDSA_cryptopp.o: ECDSA_cryptopp.cpp
	#$(COMPILER) $(COMPILER_OPTS) $(INCLUDE_OPTS) $(LIBRARY_OPTS) ECDSA_cryptopp.cpp

#ECDSA_test.out : ECDSA_cryptopp.cpp
	#$(LINKER) -o ECDSA_test.out $(INCLUDE_OPTS) $(LIBRARY_OPTS) ECDSA_cryptopp.cpp


##########################################################################
# And now we have created all the individual object files specified with 
# the macro "OBJS". 
#************************************************************************


clean:
	touch CppBlockUtils.i
	-rm *.o *.out 
	


