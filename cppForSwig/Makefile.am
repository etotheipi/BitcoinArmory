SUBDIRS = lmdb fcgi cryptopp gtest

SWIG_FLAGS = -c++ -python -threads
AM_CXXFLAGS = $(CXXFLAGS) -std=c++11

if HAVE_GCC
SWIG_FLAGS += -D__GNUC__
endif

if HAVE_CLANG
SWIG_FLAGS += -D__CLANG__
endif

INCLUDE_FILES = UniversalTimer.h BinaryData.h lmdb_wrapper.h \
	BtcUtils.h DBUtils.h BlockObj.h BlockUtils.h EncryptionUtils.h \
	BtcWallet.h LedgerEntry.h ScrAddrObj.h Blockchain.h \
	BDM_mainthread.h BDM_supportClasses.h \
	BlockDataViewer.h HistoryPager.h Progress.h \
	txio.h TxClasses.h StoredBlockObj.h \
	DatabaseBuilder.h BlockchainScanner.h BlockDataMap.h \
	DataObject.h BitcoinP2p.h BDM_Server.h BDM_seder.h SocketObject.h \
	FcgiMessage.h BlockDataManagerConfig.h \
	Transactions.h Script.h Signer.h nodeRPC.h JSON_codec.h \
	ReentrantLock.h StringSockets.h log.h OS_TranslatePath.h

DB_SOURCE_FILES = UniversalTimer.cpp BinaryData.cpp lmdb_wrapper.cpp \
	BtcUtils.cpp DBUtils.cpp BlockObj.cpp BlockUtils.cpp EncryptionUtils.cpp \
	BtcWallet.cpp LedgerEntry.cpp ScrAddrObj.cpp Blockchain.cpp \
	BDM_mainthread.cpp BDM_supportClasses.cpp \
	BlockDataViewer.cpp HistoryPager.cpp Progress.cpp \
	txio.cpp TxClasses.cpp StoredBlockObj.cpp \
	DatabaseBuilder.cpp BlockchainScanner.cpp BlockDataMap.cpp \
	DataObject.cpp BitcoinP2P.cpp BDM_Server.cpp BDM_seder.cpp SocketObject.cpp \
	FcgiMessage.cpp BlockDataManagerConfig.cpp \
	Transactions.cpp Script.cpp Signer.cpp nodeRPC.cpp JSON_codec.cpp \
	StringSockets.cpp main.cpp ReentrantLock.cpp

CPPBLOCKUTILS_SOURCE_FILES = UniversalTimer.cpp BinaryData.cpp \
	BtcUtils.cpp DBUtils.cpp EncryptionUtils.cpp \
	BDM_seder.cpp DataObject.cpp FcgiMessage.cpp \
	SocketObject.cpp SwigClient.cpp StringSockets.cpp \
	BlockDataManagerConfig.cpp TxClasses.cpp \
	WalletManager.cpp Wallets.cpp Script.cpp Signer.cpp \
	Transactions.cpp \
        CoinSelection.cpp ReentrantLock.cpp JSON_codec.cpp

noinst_PROGRAMS = ArmoryDB
lib_LTLIBRARIES = libCppBlockUtils.la

#ArmoryDB
ArmoryDB_SOURCES = $(INCLUDE_FILES) \
		   $(DB_SOURCE_FILES)

ArmoryDB_CXXFLAGS = $(AM_CXXFLAGS) -Ilmdb \
		    -Icryptopp \
		    -Ifcgi -Ifcgi/include \
		    -D__STDC_LIMIT_MACROS

ArmoryDB_LDADD = -Llmdb -llmdb \
		 -Lcryptopp -lcryptopp \
		 -Lfcgi/libfcgi/ -lfcgi \
		 -lpthread

ArmoryDB_LDFLAGS = -static $(LDFLAGS)

#libCppBlockUtils
libCppBlockUtils_la_SOURCES = $(INCLUDE_FILES) \
				$(CPPBLOCKUTILS_SOURCE_FILES) \
				CppBlockUtils_wrap.cxx
libCppBlockUtils_la_CXXFLAGS = $(AM_CXXFLAGS) -Ilmdb \
		    		-Icryptopp \
				$(AX_SWIG_PYTHON_CPPFLAGS) \
				$(EXTRA_PYTHON_INCLUDES) \
				-D__STDC_LIMIT_MACROS

libCppBlockUtils_la_LIBADD = 	-Llmdb -llmdb \
		 	 	./cryptopp/libcryptopp.la \
		 	 	-lpthread

libCppBlockUtils_la_LDFLAGS = $(LDFLAGS)

if BUILD_DARWIN
libCppBlockUtils_la_LDFLAGS += -Wl,-rpath,@executable_path/ -Wl,-rpath,@loader_path/
endif

#custom rules
CppBlockUtils_wrap.cxx: CppBlockUtils.i
	swig $(SWIG_FLAGS) CppBlockUtils.i 

.PHONY: CppBlockUtils_wrap.cxx

clean-local:
	rm -f CppBlockUtils.py
	rm -f CppBlockUtils_wrap.cxx
	rm -f CppBlockUtils_wrap.h
