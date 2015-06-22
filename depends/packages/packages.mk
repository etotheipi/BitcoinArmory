# zip is currently broken. Add it back to packages when it is fixed.
packages:=openssl pyqt5 python3 twisted
native_packages := native_pcre native_psutil native_python3 native_rsync native_sip native_swig native_zlib native_zope.interface

qt_native_packages = native_protobuf
qt_packages = qrencode protobuf

qt_linux_packages= qt expat dbus libxcb xcb_proto libXau xproto freetype fontconfig libX11 xextproto libXext xtrans
qt_darwin_packages=qt
qt_mingw32_packages=qt

ifneq ($(build_os),darwin)
darwin_native_packages=native_cctools
endif
