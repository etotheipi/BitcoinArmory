MAYBE_BUILD =
if BUILD_TESTS
MAYBE_BUILD += gtest
endif

DIST_SUBDIRS = lmdb fcgi cryptopp
SUBDIRS = lmdb fcgi cryptopp $(MAYBE_BUILD)

SWIG_FLAGS = -c++ -python -threads
AM_CXXFLAGS = $(CXXFLAGS) -std=c++11

if HAVE_GCC
SWIG_FLAGS += -D__GNUC__
if HAVE_64BIT
SWIG_FLAGS += -D__LP64__
endif
endif

if HAVE_CLANG
SWIG_FLAGS += -D__CLANG__
endif

EXTRA_DIST = CppBlockUtils.i CppBlockUtils.py

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
	ReentrantLock.h StringSockets.h log.h OS_TranslatePath.h \
	TransactionBatch.h BlockchainScanner_Super.h SigHashEnum.h TxEvalState.h \
	make_unique.h TxOutScrRef.h bdmenums.h DbHeader.h SocketIncludes.h \
	PartialMerkle.h util.h WalletManager.h SwigClient.h Wallets.h \
	CoinSelection.h LedgerEntryData.h ThreadSafeClasses.h \
	Win_TranslatePath.h ScriptRecipient.h \
	bech32/ref/c++/bech32.h bech32/ref/c++/segwit_addr.h

DB_SOURCE_FILES = UniversalTimer.cpp BinaryData.cpp lmdb_wrapper.cpp \
	BtcUtils.cpp DBUtils.cpp BlockObj.cpp BlockUtils.cpp EncryptionUtils.cpp \
	BtcWallet.cpp LedgerEntry.cpp ScrAddrObj.cpp Blockchain.cpp \
	BDM_mainthread.cpp BDM_supportClasses.cpp \
	BlockDataViewer.cpp HistoryPager.cpp Progress.cpp \
	txio.cpp TxClasses.cpp StoredBlockObj.cpp \
	DatabaseBuilder.cpp BlockchainScanner.cpp BlockchainScanner_Super.cpp BlockDataMap.cpp \
	DataObject.cpp BitcoinP2P.cpp BDM_Server.cpp BDM_seder.cpp SocketObject.cpp \
	FcgiMessage.cpp BlockDataManagerConfig.cpp \
	Transactions.cpp Script.cpp Signer.cpp nodeRPC.cpp JSON_codec.cpp \
	StringSockets.cpp main.cpp ReentrantLock.cpp log.cpp TxEvalState.cpp

CPPBLOCKUTILS_SOURCE_FILES = UniversalTimer.cpp BinaryData.cpp \
	BtcUtils.cpp DBUtils.cpp EncryptionUtils.cpp \
	BDM_seder.cpp DataObject.cpp FcgiMessage.cpp \
	SocketObject.cpp SwigClient.cpp StringSockets.cpp \
	BlockDataManagerConfig.cpp TxClasses.cpp \
	WalletManager.cpp Wallets.cpp Script.cpp Signer.cpp \
	Transactions.cpp \
	CoinSelection.cpp ReentrantLock.cpp JSON_codec.cpp \
	TransactionBatch.cpp log.cpp TxEvalState.cpp \
	bech32/ref/c++/bech32.cpp bech32/ref/c++/segwit_addr.cpp


#ArmoryDB
noinst_PROGRAMS = ArmoryDB

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
if HAVE_GUI
lib_LTLIBRARIES = libCppBlockUtils.la

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
endif
