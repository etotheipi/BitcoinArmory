noinst_LTLIBRARIES = libcryptopp.la

libcryptopp_la_LIBADD =
AM_LDFLAGS = $(LDFLAGS)
AM_CXXFLAGS = $(CXXFLAGS) -std=c++11

#compilation flags
if CRYPTOPP_HAVE_CLANG
AM_CXXFLAGS += -DCRYPTOPP_DISABLE_ASM
endif

# On OSX, g++ = clang and comes up as both.
if IS_X86
if CRYPTOPP_HAVE_GCC
if ! BUILD_DARWIN

if ! GAS210_OR_LATER	# .intel_syntax wasn't supported until GNU assembler 2.10
AM_CXXFLAGS += -DCRYPTOPP_DISABLE_ASM
else
if ! GAS217_OR_LATER
AM_CXXFLAGS += -DCRYPTOPP_DISABLE_SSSE3
else
AM_CXXFLAGS += -march=native -mtune=generic $(X86_FEATURE_CFLAGS)

if HAVE_AES
AM_CXXFLAGS += -maes -DCRYPTOPP_ENABLE_AESNI
endif

if HAVE_PCLMUL
AM_CXXFLAGS += -mpclmul
endif

endif
endif

endif	# ! BUILD_DARWIN
endif	# CRYPTOPP_HAVE_GCC
endif	# IS_X86

if UNAME_LINUX
AM_LDFLAGS += -pthread
endif

if BUILD_DARWIN
AM_CXXFLAGS += -DNDEBUG -march=native
libcryptopp_la_LDFLAGS = -Wl,-rpath,@executable_path/ -Wl,-rpath,@loader_path/
endif

INCLUDE_FILES = 3way.h	    crc.h	gcm.h	    modexppc.h	ripemd.h     tea.h \
	adler32.h   cryptlib.h	gf2_32.h    mqueue.h	rng.h	     tiger.h \
	aes.h	    default.h	gf256.h     mqv.h	rsa.h	     trdlocal.h \
	algebra.h   des.h	gf2n.h	    nbtheory.h	rw.h	     trunhash.h \
	algparam.h  DetSign.h	gfpcrypt.h  network.h	safer.h      ttmac.h \
	arc4.h	    dh2.h	gost.h	    nr.h	salsa.h      twofish.h \
	argnames.h  dh.h	gzip.h	    oaep.h	seal.h	     validate.h \
	asn.h	    dll.h	hex.h	    oids.h	secblock.h   vmac.h \
	authenc.h   dmac.h	hmac.h	    osrng.h	seckey.h     wait.h \
	base32.h    dsa.h	hrtimer.h   pch.h	seed.h	     wake.h \
	base64.h    eax.h	ida.h	    pkcspad.h	serpent.h    whrlpool.h \
	basecode.h  ec2n.h	idea.h	    polynomi.h	serpentp.h   winpipes.h \
	bench.h     eccrypto.h	integer.h   pssr.h	shacal2.h    words.h \
	blowfish.h  ecp.h	iterhash.h  pubkey.h	sha.h	     xtrcrypt.h \
	blumshub.h  elgamal.h	lubyrack.h  pwdbased.h	shark.h      xtr.h \
	camellia.h  emsa2.h	luc.h	    queue.h	simple.h     zdeflate.h \
	cast.h	    eprecomp.h	md2.h	    rabin.h	skipjack.h   zinflate.h \
	cbcmac.h    esign.h	md4.h	    randpool.h	smartptr.h   zlib.h \
	ccm.h	    factory.h	md5.h	    rc2.h	socketft.h \
	channels.h  files.h	mdc.h	    rc5.h	sosemanuk.h \
	cmac.h	    filters.h	misc.h	    rc6.h	square.h \
	config.h    fips140.h	modarith.h  resource.h	stdcpp.h \
	cpu.h	    fltrimpl.h	modes.h     rijndael.h	strciphr.h

SOURCE_FILES = 3way.cpp	  gf2n.cpp      pssr.cpp	socketft.cpp \
	adler32.cpp	  default.cpp	gfpcrypt.cpp  pubkey.cpp    sosemanuk.cpp \
	algebra.cpp	  des.cpp	gost.cpp      queue.cpp     square.cpp \
	algparam.cpp	  dessp.cpp	gzip.cpp      rabin.cpp     squaretb.cpp \
	arc4.cpp	  DetSign.cpp	hex.cpp       randpool.cpp  strciphr.cpp \
	asn.cpp		  dh2.cpp	hmac.cpp      rc2.cpp	    tea.cpp \
	authenc.cpp	  dh.cpp	hrtimer.cpp   rc5.cpp \
	base32.cpp	  dll.cpp	ida.cpp       rc6.cpp	    tftables.cpp \
	base64.cpp	  idea.cpp      rdtables.cpp  tiger.cpp \
	basecode.cpp	  dsa.cpp	integer.cpp   tigertab.cpp \
	eax.cpp	iterhash.cpp  rijndael.cpp  trdlocal.cpp \
	ec2n.cpp	luc.cpp       ripemd.cpp    ttmac.cpp \
	bfinit.cpp	  eccrypto.cpp	md2.cpp       rng.cpp	    twofish.cpp \
	blowfish.cpp	  ecp.cpp	md4.cpp       rsa.cpp \
	blumshub.cpp	  elgamal.cpp	md5.cpp       rw.cpp \
	camellia.cpp	  emsa2.cpp	misc.cpp      safer.cpp \
	cast.cpp	  eprecomp.cpp	modes.cpp     salsa.cpp     vmac.cpp \
	casts.cpp	  esign.cpp	mqueue.cpp    seal.cpp	    wait.cpp \
	cbcmac.cpp	  files.cpp	mqv.cpp       seed.cpp	    wake.cpp \
	ccm.cpp		  filters.cpp	nbtheory.cpp  serpent.cpp   whrlpool.cpp \
	channels.cpp	  fips140.cpp	network.cpp   shacal2.cpp   winpipes.cpp \
	cmac.cpp	  oaep.cpp      sha.cpp	    xtr.cpp \
	cpu.cpp		  osrng.cpp     sharkbox.cpp  xtrcrypt.cpp \
	crc.cpp		  gcm.cpp	pch.cpp       shark.cpp     zdeflate.cpp \
	cryptlib_bds.cpp  gf2_32.cpp	pkcspad.cpp   simple.cpp    zinflate.cpp \
	cryptlib.cpp	  gf256.cpp	polynomi.cpp  skipjack.cpp  zlib.cpp

EXTRA_DIST = bench2.cpp bench.cpp test.cpp validat1.cpp validat2.cpp validat3.cpp \
	datatest.cpp regtest.cpp fipsalgt.cpp dlltest.cpp fipstest.cpp

libcryptopp_la_SOURCES = $(INCLUDE_FILES) $(SOURCE_FILES)
