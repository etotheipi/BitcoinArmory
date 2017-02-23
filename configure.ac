AC_PREREQ(2.60)
AC_INIT([BitcoinArmory], [0.95.99], [moothecowlord@gmail.com])

AM_INIT_AUTOMAKE([1.10 foreign -Wall -Werror])

AM_PROG_AR
LT_INIT

AC_PROG_CC
AC_PROG_CXX

AC_CONFIG_MACRO_DIR([m4])
m4_include([m4/ax_check_compile_flag.m4])
m4_include([m4/ax_swig_python.m4])
m4_include([m4/ax_pkg_swig.m4])
m4_include([m4/ax_python_devel.m4])
m4_include([m4/ax_python_module.m4])

AX_CHECK_COMPILE_FLAG([-std=c++11], [compile_flag_cxx11=yes])
if test "x${compile_flag_cxx11}" = "xyes"; then
	CXXFLAGS="-std=c++11 $CXXFLAGS"
	CXX_STANDARD=201103L
else
    AC_MSG_ERROR([need c++ 11 compiler])
fi

AX_SWIG_PYTHON([no])
AS_IF([test -z $AX_SWIG_PYTHON_CPPFLAGS], 
	[AC_MSG_ERROR([failed to procure swig include path, make sure swig is installed])])

#check existence of Qt packages
if ! pkg-config --exists 'QtCore >= 4.8 QtCore <= 5 QtGui >= 4.8 QtGui <= 5'; then
	AC_MSG_ERROR([missing QtCore library, make sure libqtcore4 and libqt4-dev are installed])
fi

AC_CHECK_PROG([HAVE_PYRCC4], [pyrcc4], [yes], [no])
AS_IF([test $HAVE_PYRCC4 == yes], [],
	[AC_MSG_ERROR([missing pyrcc4 in path, make sure pyqt4-dev-tools])]) 

AX_PYTHON_MODULE([psutil], [fatal])
AX_PYTHON_MODULE([twisted], [fatal])

AC_SUBST([CXX_STANDARD])

AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES(Makefile 
		cppForSwig/Makefile 
		cppForSwig/lmdb/Makefile)
AC_CONFIG_SUBDIRS([cppForSwig/fcgi cppForSwig/cryptopp])

AC_OUTPUT
