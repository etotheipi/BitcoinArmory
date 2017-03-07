SUBDIRS = ../lmdb ../fcgi ../cryptopp

INCLUDE_FILES = ../UniversalTimer.h ../BinaryData.h ../lmdb_wrapper.h \
	../BtcUtils.h ../DBUtils.h ../BlockObj.h ../BlockUtils.h ../EncryptionUtils.h \
	../BtcWallet.h ../LedgerEntry.h ../ScrAddrObj.h ../Blockchain.h \
	../BDM_mainthread.h ../BDM_supportClasses.h \
	../BlockDataViewer.h ../HistoryPager.h ../Progress.h \
	../txio.h ../TxClasses.h ../StoredBlockObj.h \
	../DatabaseBuilder.h ../BlockchainScanner.h ../BlockDataMap.h \
	../DataObject.h ../BitcoinP2p.h ../BDM_Server.h ../BDM_seder.h ../SocketObject.h \
	../FcgiMessage.h ../BlockDataManagerConfig.h \
	../Transactions.h ../nodeRPC.h ../JSON_codec.h \
	../ReentrantLock.h ../StringSockets.h ../log.h ../OS_TranslatePath.h \
	../WalletManager.h ../Wallets.h ../Signer.h ../SwigClient.h \
	../CoinSelection.h \
	gtest.h

SOURCE_FILES = ../UniversalTimer.cpp ../BinaryData.cpp ../lmdb_wrapper.cpp \
	../BtcUtils.cpp ../DBUtils.cpp ../BlockObj.cpp ../BlockUtils.cpp ../EncryptionUtils.cpp \
	../BtcWallet.cpp ../LedgerEntry.cpp ../ScrAddrObj.cpp ../Blockchain.cpp \
	../BDM_mainthread.cpp ../BDM_supportClasses.cpp \
	../BlockDataViewer.cpp ../HistoryPager.cpp ../Progress.cpp \
	../txio.cpp ../TxClasses.cpp ../StoredBlockObj.cpp \
	../DatabaseBuilder.cpp ../BlockchainScanner.cpp ../BlockDataMap.cpp \
	../DataObject.cpp ../BitcoinP2P.cpp ../BDM_Server.cpp ../BDM_seder.cpp ../SocketObject.cpp \
	../FcgiMessage.cpp ../BlockDataManagerConfig.cpp \
	../Transactions.cpp ../nodeRPC.cpp ../JSON_codec.cpp \
	../StringSockets.cpp ../ReentrantLock.cpp \
	../WalletManager.cpp ../Wallets.cpp ../Script.cpp ../Signer.cpp ../SwigClient.cpp \
	../CoinSelection.cpp \
	gtest-all.cc

AM_CXXFLAGS = -I../lmdb \
	-I../cryptopp \
	-I../fcgi -I../fcgi/include \
	-D__STDC_LIMIT_MACROS

AM_LDFLAGS = -static

bin_PROGRAMS = CppBlockUtilsTests ContainerTests DB1kIterTest

CppBlockUtilsTests_SOURCES = $(INCLUDE_FILES) $(SOURCE_FILES) CppBlockUtilsTests.cpp
DB1kIterTest_SOURCES = $(INCLUDE_FILES) $(SOURCE_FILES) DB1kIterTest.cpp
ContainerTests_SOURCES = ContainerTests.cpp gtest.h gtest-all.cc

CppBlockUtilsTests_LDADD = -L../lmdb -llmdb \
	-L../cryptopp -lcryptopp \
	-L../fcgi/libfcgi/ -lfcgi \
	-lpthread

ContainerTests_LDADD = -lpthread

DB1kIterTest_LDADD = -L../lmdb -llmdb \
	-L../cryptopp -lcryptopp \
	-L../fcgi/libfcgi/ -lfcgi \
	-lpthread



