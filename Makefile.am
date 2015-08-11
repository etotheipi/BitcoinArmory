SUBDIRS = cppForSwig
desktopdir = $(datarootdir)/applications
desktop_DATA = dpkgfiles/armory.desktop dpkgfiles/armoryoffline.desktop \
			  dpkgfiles/armorytestnet.desktop
CLEANFILES = $(desktop_DATA)

ROOT_SO = _CppBlockUtils.so
ROOT_PY = \
	announcefetch.py armorycolors.py armoryd.py armorymodels.py \
    ArmoryQt.py CppBlockUtils.py dynamicImport.py guardian.py \
    jasvet.py LICENSE.py qrc_img_resources.py qrcodenative.py \
    qt4reactor.py qtdefines.py qtdialogs.py SDM.py setup.py \
    subprocess_win.py update_version.py writeNSISCompilerArgs.py
ARMORYENGINE_PY = \
	armoryengine/ALL.py armoryengine/ArmoryBuild.py \
	armoryengine/ArmoryUtils.py armoryengine/AsciiSerialize.py \
	armoryengine/BDM.py armoryengine/BinaryPacker.py \
	armoryengine/BinaryUnpacker.py armoryengine/Block.py \
	armoryengine/CoinSelection.py armoryengine/Decorators.py \
	armoryengine/__init__.py armoryengine/MultiSigUtils.py \
	armoryengine/Networking.py armoryengine/parseAnnounce.py \
	armoryengine/PyBtcAddress.py armoryengine/PyBtcWallet.py \
	armoryengine/PyBtcWalletRecovery.py armoryengine/Script.py \
	armoryengine/Timer.py armoryengine/torrentDL.py \
	armoryengine/Transaction.py armoryengine/UserAddressUtils.py
BITCOINRPC_JSONRPC_PY = \
	bitcoinrpc_jsonrpc/authproxy.py bitcoinrpc_jsonrpc/__init__.py \
    bitcoinrpc_jsonrpc/json.py bitcoinrpc_jsonrpc/proxy.py
BITTORNADO_PY = \
	BitTornado/bencode.py BitTornado/bitfield.py BitTornado/clock.py \
	BitTornado/ConfigDir.py BitTornado/ConfigReader.py \
   	BitTornado/ConnChoice.py BitTornado/CreateIcons.py \
	BitTornado/CurrentRateMeasure.py BitTornado/download_bt1.py \
	BitTornado/HTTPHandler.py BitTornado/inifile.py BitTornado/__init__.py \
	BitTornado/iprangeparse.py BitTornado/launchmanycore.py \
	BitTornado/natpunch.py BitTornado/parseargs.py BitTornado/parsedir.py \
	BitTornado/piecebuffer.py BitTornado/PSYCO.py BitTornado/RateLimiter.py \
	BitTornado/RateMeasure.py BitTornado/RawServer.py BitTornado/selectpoll.py \
	BitTornado/ServerPortHandler.py BitTornado/SocketHandler.py \
	BitTornado/subnetparse.py BitTornado/torrentlistparse.py \
   	BitTornado/zurllib.py
BITTORNADO_BT1_PY = \
	BitTornado/BT1/btformats.py BitTornado/BT1/Choker.py \
	BitTornado/BT1/Connecter.py BitTornado/BT1/DownloaderFeedback.py \
	BitTornado/BT1/Downloader.py BitTornado/BT1/Encrypter.py \
	BitTornado/BT1/fakeopen.py BitTornado/BT1/FileSelector.py \
	BitTornado/BT1/Filter.py BitTornado/BT1/HTTPDownloader.py \
	BitTornado/BT1/__init__.py BitTornado/BT1/makemetafile.py \
	BitTornado/BT1/NatCheck.py BitTornado/BT1/PiecePicker.py \
	BitTornado/BT1/Rerequester.py BitTornado/BT1/Statistics.py \
	BitTornado/BT1/Storage.py BitTornado/BT1/StorageWrapper.py \
	BitTornado/BT1/StreamCheck.py BitTornado/BT1/T2T.py \
	BitTornado/BT1/track.py BitTornado/BT1/Uploader.py
EXTRAS_PY = \
	extras/armoryengine_basics.py extras/BDMbasics_getBalance.py \
	extras/BDMbasics_listUTXOs.py extras/BDMbasics_traceTxHistory.py \
	extras/BDMbasics_watchBalance.py extras/breakDownWallet.py \
	extras/cli_sign_txdp.py extras/createTestBlocksForReadBlkUpdate.py \
	extras/createTestChain.py extras/dlscript.py \
	extras/extractKeysFromWallet.py extras/findpass.py \
	extras/frag_wallet.py extras/__init__.py extras/LastBlockHash.py \
	extras/LatestBlocksFinder.py extras/lookathex.py \
	extras/manually_import_500k_addr.py extras/mysteryHex.py \
	extras/PromoKit.py extras/sample_armory_code.py \
	extras/satoshiDiceStats.py extras/sign_dl_list.py \
	extras/sign_release.py extras/unfrag_wallet.py \
	extras/verify_dl_list.py
PYTEST_PY = \
	pytest/__init__.py pytest/testAnnounce.py pytest/testArmoryD.py \
	pytest/testArmoryDStartup.py pytest/testArmoryDTiab.py \
	pytest/testDecorators.py pytest/testFragmentedBackup.py \
	pytest/testParseAnnounce.py pytest/testPyBtcAddress.py \
	pytest/testPyBtcWallet.py pytest/testPyBtcWalletRecovery.py \
	pytest/testPyTX.py pytest/testSplitSecret.py pytest/testUserAddress.py \
	pytest/Tiab.py
TXJSONRPC_PY = \
	txjsonrpc/auth.py txjsonrpc/__init__.py txjsonrpc/jsonrpclib.py \
	txjsonrpc/jsonrpc.py txjsonrpc/meta.py
TXJSONRPC_WEB_PY = txjsonrpc/web/__init__.py txjsonrpc/web/jsonrpc.py
UI_PY = \
	ui/__init__.py ui/MultiSigDialogs.py ui/MultiSigModels.py \
    ui/toolsDialogs.py ui/TxFrames.py ui/UpgradeDownloader.py \
    ui/VerifyOfflinePackage.py ui/WalletFrames.py ui/Wizards.py
URLLIB3_PY = \
	urllib3/_collections.py urllib3/connectionpool.py \
	urllib3/connection.py urllib3/exceptions.py urllib3/fields.py \
	urllib3/filepost.py urllib3/__init__.py urllib3/poolmanager.py \
	urllib3/request.py urllib3/response.py urllib3/util.py
URLLIB3_CONTRIB_PY = \
	urllib3/contrib/__init__.py urllib3/contrib/ntlmpool.py \
	urllib3/contrib/pyopenssl.py
URLLIB3_PACKAGES_PY = \
	urllib3/packages/__init__.py urllib3/packages/ordered_dict.py \
	urllib3/packages/six.py 
URLLIB3_PACKAGES_SSL_MATCH_HOSTNAME_PY = \
	urllib3/packages/ssl_match_hostname/_implementation.py \
	urllib3/packages/ssl_match_hostname/__init__.py
MESSAGES_PY = $(ROOT_PY) $(ARMORYENGINE_PY) $(UI_PY)

all:
	$(MAKE) -C cppForSwig

clean-local:
	rm -f CppBlockUtils.py
	rm -f qrc_img_resources.py
	rm -f _CppBlockUtils.so
	rm -f cppForSwig/cryptopp/a.out
	rm -f *.pyc BitTornado/*.pyc bitcoinrpc_jsonrpc/*.pyc ui/*.pyc
	rm -f armoryengine/*.pyc dialogs/*.pyc BitTornado/BT1/*.pyc
	rm -f pytest/*.pyc txjsonrpc/*.pyc jsonrpc/*.pyc txjsonrpc/web/*.pyc

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(datarootdir)/applications
	$(MKDIR_P) $(DESTDIR)$(datarootdir)/armory/img
	rsync -rupE --exclude="img/.DS_Store" img $(DESTDIR)$(datarootdir)/armory/

install-exec-local:
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/extras
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/bitcoinrpc_jsonrpc
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/txjsonrpc/web
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/ui
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/pytest
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/BitTornado/BT1
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/urllib3/contrib
	$(MKDIR_P) $(DESTDIR)$(libdir)/armory/urllib3/packages/ssl_match_hostname
	$(MKDIR_P) $(DESTDIR)$(bindir)
	$(SED) "s: /usr/lib: $(libdir):g" < dpkgfiles/armory > $(DESTDIR)$(bindir)/armory
	chmod +x $(DESTDIR)$(bindir)/armory
	cp $(ROOT_PY) $(ROOT_SO) README.md $(DESTDIR)$(libdir)/armory/
	rsync -rupE armoryengine $(DESTDIR)$(libdir)/armory/
	cp $(EXTRAS_PY) $(DESTDIR)$(libdir)/armory/extras
	cp $(BITCOINRPC_JSONRPC_PY) $(DESTDIR)$(libdir)/armory/bitcoinrpc_jsonrpc
	cp $(TXJSONRPC_PY) $(DESTDIR)$(libdir)/armory/txjsonrpc
	cp $(TXJSONRPC_WEB_PY) $(DESTDIR)$(libdir)/armory/txjsonrpc/web
	cp $(UI_PY) $(DESTDIR)$(libdir)/armory/ui
	cp $(PYTEST_PY) $(DESTDIR)$(libdir)/armory/pytest
	cp $(URLLIB3_PY) $(DESTDIR)$(libdir)/armory/urllib3
	cp $(URLLIB3_CONTRIB_PY) $(DESTDIR)$(libdir)/armory/urllib3/contrib
	cp $(URLLIB3_PACKAGES_PY) $(DESTDIR)$(libdir)/armory/urllib3/packages
	cp $(URLLIB3_PACKAGES_SSL_MATCH_HOSTNAME_PY) \
	   $(DESTDIR)$(libdir)/armory/urllib3/packages/ssl_match_hostname
	cp $(BITTORNADO_PY) $(DESTDIR)$(libdir)/armory/BitTornado
	cp $(BITTORNADO_BT1_PY) $(DESTDIR)$(libdir)/armory/BitTornado/BT1
	cp default_bootstrap.torrent $(DESTDIR)$(libdir)/armory

dpkgfiles/%.desktop: dpkgfiles/%.desktop.in Makefile
	sed -e 's,[@]bindir[@],$(bindir),g' < $< > $@
	chmod +x $@

all-test-tools: all
	$(MAKE) -C cppForSwig/gtest

gtest: all-test-tools
	(cd cppForSwig/gtest && ./CppBlockUtilsTests)

pytest: all
	python -m unittest discover

test: gtest pytest

mo: messages
	$(MAKE) -C po mo

messages: $(MESSAGES_PY)
	xgettext -o po/messages.pot --from-code=UTF-8 -L Python -ktr $(MESSAGES_PY)

if TARGET_LINUX
if BUILD_LINUX
deb: all
	@while [ -z "$$AMD64_CHROOT" ]; do \
		read -r -p "Name of amd64 chroot: " AMD64_CHROOT; \
	done && \
	while [ -z "$$I386_CHROOT" ]; do \
		read -r -p "Name of i386 chroot: " I386_CHROOT; \
	done && \
	python dpkgfiles/make_deb_package.py $$AMD64_CHROOT 64 1 1 0 && \
	python dpkgfiles/make_deb_package.py $$I386_CHROOT 32 1 1 0
endif
endif

if TARGET_DARWIN
if BUILD_LINUX
QMAKE=qmake-qt4
else
if BUILD_DARWIN
QMAKE=qmake -spec macx-g++
endif
endif
objc:
	$(SIP) -w -x VendorID -t WS_MACX -t Qt_4_8_6 -x Py_v3 -B Qt_5_0_0 -o \
		-P -g -c osxbuild/objc_armory/ $(SIP_CPPFLAGS) \
		osxbuild/objc_armory/ArmoryMac.sip
	$(QMAKE) osxbuild/objc_armory/ArmoryMac.pro -o osxbuild/objc_armory/
	$(MAKE) -C osxbuild/objc_armory/ CC="$(CC)" CXX="$(CXX)" LINK="$(LINK)"

if USE_GITIAN
Armory.app: Armory-tmp-gitian
	rm -rf osxbuild/$@
	cp -R osxbuild/Armory-tmp-gitian osxbuild/$@
else
Armory.app: Armory-tmp
	rm -rf osxbuild/$@
	cp -R osxbuild/Armory-tmp osxbuild/$@
endif

Armory-tmp: all osxbuild/install-py3 osxbuild/install-qt5
	rm -rf osxbuild/$@
	$(MKDIR_P) osxbuild/$@/Contents/MacOS/py
	$(MKDIR_P) osxbuild/$@/Contents/Frameworks
	$(MKDIR_P) osxbuild/$@/Contents/Resources
	$(MKDIR_P) osxbuild/$@/Contents/Dependencies
	$(MAKE) DESTDIR=osxbuild/$@/Contents/MacOS/py PREFIX=/usr install
	cp osxbuild/Info.plist osxbuild/$@/Contents
	cp img/armory_icon_fullres.icns osxbuild/$@/Contents/Resources/Icon.icns
	cp osxbuild/Armory-script.sh osxbuild/$@/Contents/MacOS/Armory
	cp osxbuild/armoryd-script.sh osxbuild/$@/Contents/MacOS/armoryd
	cp -R osxbuild/install-py3/Python.framework osxbuild/$@/Contents/Frameworks/
	cp -R osxbuild/install-qt5/lib/Qt{Core,Gui,Network}.framework osxbuild/$@/Contents/Frameworks/
	chmod +x osxbuild/$@/Contents/MacOS/Armory
	chmod +x osxbuild/$@/Contents/MacOS/armoryd

Armory-tmp-gitian: all
	rm -rf osxbuild/$@
	$(MKDIR_P) osxbuild/$@/Contents/MacOS/py
	$(MKDIR_P) osxbuild/$@/Contents/Frameworks
	$(MKDIR_P) osxbuild/$@/Contents/Resources
	$(MKDIR_P) osxbuild/$@/Contents/Dependencies
	$(MAKE) DESTDIR=osxbuild/$@/Contents/MacOS/py PREFIX=/usr install
	cp osxbuild/Info.plist osxbuild/$@/Contents
	cp img/armory_icon_fullres.icns osxbuild/$@/Contents/Resources/Icon.icns
	cp osxbuild/Armory-script.sh osxbuild/$@/Contents/MacOS/Armory
	cp osxbuild/armoryd-script.sh osxbuild/$@/Contents/MacOS/armoryd
	cp -R depends/x86_64-apple-darwin11/Python.framework osxbuild/$@/Contents/Frameworks/
	cp -R depends/x86_64-apple-darwin11/lib/Qt{Core,Gui,Network}.framework osxbuild/$@/Contents/Frameworks/
	chmod +x osxbuild/$@/Contents/MacOS/Armory
	chmod +x osxbuild/$@/Contents/MacOS/armoryd

osxbuild/install-py3:
	@echo "building py3"
	cd osxbuild && ./build-py3.sh

osxbuild/install-qt5:
	@echo "building qt5"
	cd osxbuild && ./build-qt5.sh
endif # end TARGET_DARWIN
