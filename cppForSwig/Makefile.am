SUBDIRS = lmdb fcgi cryptopp

SWIG_OPTS = -c++ -python -threads

INCLUDE_FILES = UniversalTimer.h BinaryData.h lmdb_wrapper.h \
	BtcUtils.h DBUtils.h BlockObj.h BlockUtils.h EncryptionUtils.h \
	BtcWallet.h LedgerEntry.h ScrAddrObj.h Blockchain.h \
	BDM_mainthread.h BDM_supportClasses.h \
	BlockDataViewer.h HistoryPager.h Progress.h \
	txio.h TxClasses.h StoredBlockObj.h \
	DatabaseBuilder.h BlockchainScanner.h BlockDataMap.h \
	DataObject.h BitcoinP2P.h BDM_Server.h BDM_seder.h SocketObject.h \
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

bin_PROGRAMS = ArmoryDB
lib_LTLIBRARIES = libCppBlockUtils.la

#ArmoryDB
ArmoryDB_SOURCES = $(INCLUDE_FILES) \
		   $(DB_SOURCE_FILES)

ArmoryDB_CXXFLAGS = -Ilmdb \
		    -Icryptopp \
		    -Ifcgi -Ifcgi/include \
		    -D__STDC_LIMIT_MACROS -fPIC -pipe

ArmoryDB_LDADD = lmdb/liblmdb.a \
		 cryptopp/libcryptopp.a \
		 -Lfcgi/libfcgi/ -lfcgi \
		 -lpthread

ArmoryDB_LDFLAGS = -static

#libCppBlockUtils
libCppBlockUtils_la_SOURCES = 	$(INCLUDE_FILES) \
				$(CPPBLOCKUTILS_SOURCE_FILES) \
				CppBlockUtils_wrap.cxx
libCppBlockUtils_la_CXXFLAGS = 	-Ilmdb \
		    		-Icryptopp \
				$(PYTHONINC) \
				-D__STDC_LIMIT_MACROS -fPIC -pipe

libCppBlockUtils_la_LDFLAGS = 	-shared

libCppBlockUtils_la_LIBADD = 	-Llmdb -llmdb \
		 	 	cryptopp/libcryptopp.a \
		 	 	-lpthread

#custom rules
CppBlockUtils_wrap.cxx: CppBlockUtils.i
	swig -c++ -python -threads CppBlockUtils.i 

.PHONY: CppBlockUtils_wrap.cxx


