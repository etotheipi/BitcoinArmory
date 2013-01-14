COMPILER = g++ 
#COMPILER_OPTS = -c -g -Wall -fPIC -D_DEBUG
COMPILER_OPTS = -c -O2 -pipe -fPIC 

#**************************************************************************
LINKER = g++ 
OBJS = UniversalTimer.o BinaryData.o FileDataPtr.o BtcUtils.o BlockObj.o BlockUtils.o EncryptionUtils.o libcryptopp.a


DEPSDIR ?= /usr

INCLUDE_OPTS += -Icryptopp -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS 
LIBRARY_OPTS += -lpthread 
SWIG_OPTS    += -c++ -python -classic -threads
PYVER 		 += `python -c 'import sys; print str(sys.version_info[0]) + "." + str(sys.version_info[1])'`


UNAME := $(shell uname)

ifeq ($(UNAME), Darwin)
   # This configuration assumes you have setup your 10.X.X system like
   # Red Emerald in this thread: 
   #    https://bitcointalk.org/index.php?topic=73648.msg976015#msg976015
	# The makefile updates he shows are already tied into this if/else branch
   SWIG_INC     += -I"/usr/include/python$(PYVER)"
   STATICPYTHON +=   "/usr/lib/python$(PYVER)/config/libpython$(PYVER).a"
else
   SWIG_INC     += -I"$(DEPSDIR)/include/python$(PYVER)"
   STATICPYTHON +=   "$(DEPSDIR)/lib/libpython$(PYVER).a"


   # A failed attempt at auto-detecting .a file and using .so if .a DNE
   #PYTHONA = "$(DEPSDIR)/lib/libpython$(PYVER).a"
   #ifeq ($(wildcard $(PYTHONA)),)
      #STATICPYTHON +=   "$(DEPSDIR)/lib/libpython$(PYVER).so"
   #else
      #STATICPYTHON +=   "$(DEPSDIR)/lib/libpython$(PYVER).a"
   #endif
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
	rm -f *.o *.out libcryptopp.a cryptopp/*.out
	cd cryptopp; make clean;
	


