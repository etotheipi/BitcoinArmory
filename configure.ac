AC_PREREQ(2.60)
AC_INIT([BitcoinArmory], [0.95.99], [moothecowlord@gmail.com])

AM_INIT_AUTOMAKE([1.10 subdir-objects foreign -Wall -Werror])

AC_CONFIG_SUBDIRS([cppForSwig/fcgi cppForSwig/cryptopp])

AM_PROG_AR
LT_INIT

AC_CANONICAL_HOST

#reset these flags if they are the default -g -02
AS_IF([test "$CFLAGS" = "-g -O2"] ,[AC_SUBST(CFLAGS, [ ])])
AS_IF([test "$CXXFLAGS" = "-g -O2"] ,[AC_SUBST(CXXFLAGS, [ ])])

#debug flag
AC_ARG_ENABLE([debug],
              AC_HELP_STRING([--enable-debug],
              [compile with debug symbols @<:@default=no@:>@]),
              [want_debug="$enableval"], [want_debug=no])

if test "x$want_debug" = "xyes" -a $ac_cv_c_compiler_gnu != no; then
  CFLAGS="$CFLAGS -O0 -g"
  CXXFLAGS="$CXXFLAGS -O0 -g"
  AC_DEFINE([DEBUG], 1, [Define for debugging])
else
  CFLAGS="$CFLAGS -O2"
  CXXFLAGS="$CXXFLAGS -O2"
fi

AC_PROG_CC
AC_PROG_CXX
AM_CONDITIONAL([HAVE_GCC], [test $CXX = g++])

AC_CONFIG_MACRO_DIR([m4])
m4_include([m4/ax_check_compile_flag.m4])
m4_include([m4/ax_swig_python.m4])
m4_include([m4/ax_pkg_swig.m4])
m4_include([m4/ax_python_devel.m4])
m4_include([m4/ax_python_module.m4])
m4_include([m4/ax_cxx_compile_stdcxx.m4])

#check for c++11
AX_CXX_COMPILE_STDCXX([11], [noext], [mandatory], [nodefault])

#check for  swig
if test "x$cross_compiling" != "xyes"; then
	AX_SWIG_PYTHON([no])
	AS_IF([test -z $AX_SWIG_PYTHON_CPPFLAGS], 
		[AC_MSG_ERROR([failed to procure swig include path, make sure swig is installed])])
	AX_PYTHON_MODULE([psutil], [fatal])
	AX_PYTHON_MODULE([twisted], [fatal])
else
AC_SUBST([AX_SWIG_PYTHON_CPPFLAGS], [`python-config --includes`])
fi

AC_MSG_RESULT([AX_SWIG_PYTHON_CPPFLAGS: $AX_SWIG_PYTHON_CPPFLAGS])

#check existence of Qt packages
if ! pkg-config --exists 'QtCore >= 4.8 QtCore <= 5 QtGui >= 4.8 QtGui <= 5'; then
	AC_MSG_ERROR([missing QtCore library, make sure libqtcore4 and libqt4-dev are installed])
fi

AC_CHECK_PROG([HAVE_PYRCC4], [pyrcc4], [yes], [no])
AS_IF([test $HAVE_PYRCC4 == yes], [],
	[AC_MSG_ERROR([missing pyrcc4 in path, make sure pyqt4-dev-tools])]) 

AC_SUBST([CXX_STANDARD], $CXX_STANDARD)

dnl Determine build OS.
case $host in
  *darwin*)
    BUILD_OS=darwin
    ;;
  *linux*)
    BUILD_OS=linux
    ;;
esac

dnl Clang detection is complicated since it comes up as GCC too.
AC_LANG_PUSH([C++])
AC_COMPILE_IFELSE(
[AC_LANG_PROGRAM([], [[
#ifndef __clang__
       not clang
#endif
]])],
[CLANG=yes], [CLANG=no])
AC_LANG_POP([C++])

AC_MSG_RESULT([is compiler clang: $CLANG])
AC_SUBST([CLANG])

AM_CONDITIONAL([HAVE_CLANG], [test x$CLANG = xyes])
AM_CONDITIONAL([BUILD_DARWIN], [test x$BUILD_OS = xdarwin])

AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES(Makefile 
		cppForSwig/Makefile 
		cppForSwig/lmdb/Makefile
		cppForSwig/gtest/Makefile)

AC_OUTPUT
