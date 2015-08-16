PYTHON_INCLUDES=@PYTHON_INCLUDES@
PYTHON_LIBS=@PYTHON_LIBS@
MLDFLAGS=@MLDFLAGS@

if TARGET_LINUX
UNAME=Linux
else
if TARGET_WINDOWS
UNAME=Windows
else
if TARGET_DARWIN
UNAME=Darwin
endif
endif
endif

# Export variables to make them available to cryptopp Makefile.
export AR
export CXX
export MLDFLAGS
export RANLIB
export UNAME

CRYPTOPP_EXT=.a

if TARGET_DARWIN
MACOSX_DEPLOYMENT_TARGET=10.7
export MACOSX_DEPLOYMENT_TARGET
endif

CPPFLAGS = $(ARMORY_CPPFLAGS) -Icryptopp -Imdb -DUSE_CRYPTOPP -D__STDC_LIMIT_MACROS
SWIG_OPTS    = -c++ -python -threads

SWIG_INC     =

CXXCPP = $(CPPFLAGS) $(PYTHON_INCLUDES)

#**************************************************************************
libcryptopp$(CRYPTOPP_EXT): Makefile
	$(MAKE) -C cryptopp libcryptopp$(CRYPTOPP_EXT) RANLIB="$(RANLIB)" CXX="$(CXX)"
	mv cryptopp/libcryptopp$(CRYPTOPP_EXT) .

mdb.o: mdb/mdb.c mdb/lmdb.h mdb/midl.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -DNDEBUG -c mdb/mdb.c
midl.o: mdb/midl.c mdb/lmdb.h mdb/midl.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -DNDEBUG -c mdb/midl.c

%.o: %.cpp $(EVERY_HEADER)
	$(CXX) $(CXXCPP) $(CXXFLAGS) -c $<


CppBlockUtils_wrap.cxx: $(EVERY_HEADER) CppBlockUtils.i
	$(SWIG) $(SWIG_OPTS) -outdir ../ -v CppBlockUtils.i 

CppBlockUtils_wrap.o: $(EVERY_HEADER) CppBlockUtils_wrap.cxx
	$(CXX) $(SWIG_INC) $(CXXFLAGS) $(CXXCPP) -c CppBlockUtils_wrap.cxx

clean-local:
	touch CppBlockUtils.i
	rm -f *.o *.out *.a
	rm -f CppBlockUtils_wrap.cxx 
	$(MAKE) -C cryptopp clean
