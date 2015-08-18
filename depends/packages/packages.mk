# zip is currently broken. Add it back to packages when it is fixed.
packages:=python2
native_packages := native_pcre native_python2 native_pyqt4 native_rsync native_sip native_swig native_zlib

qt_native_packages = native_protobuf
qt_packages = qrencode protobuf

qt_darwin_packages=qt
qt_mingw32_packages=qt

ifneq ($(build_os),darwin)
darwin_native_packages=native_cctools
endif

ifneq ($(host_arch),arm)
packages+=pyqt4 twisted
native_packages+=native_psutil native_zope.interface
qt_linux_packages+=qt48 expat dbus libxcb xcb_proto libXau xproto freetype fontconfig libX11 xextproto libXext xtrans libICE libSM
endif
