AC_PREREQ(2.60)
AC_INIT([BitcoinArmory], [0.96.5], [moothecowlord@gmail.com])

AM_INIT_AUTOMAKE([1.10 subdir-objects foreign -Wall -Werror])

AC_CONFIG_SUBDIRS([cppForSwig/fcgi cppForSwig/cryptopp])

AM_PROG_AR
LT_INIT

AC_CANONICAL_HOST

#reset these flags if they are the default -g -02
AS_IF([test "$CFLAGS" = "-g -O2"] ,[AC_SUBST(CFLAGS, [ ])])
AS_IF([test "$CXXFLAGS" = "-g -O2"] ,[AC_SUBST(CXXFLAGS, [ ])])

#build tests arg
AC_ARG_ENABLE([tests],
	      AC_HELP_STRING([--enable-tests],
	      [build with test suites @<:@default=no@:>@]),
	      [want_tests="$enableval"], [want_tests=no])

#build debug arg
AC_ARG_ENABLE([debug],
              AC_HELP_STRING([--enable-debug],
              [compile with debug symbols @<:@default=no@:>@]),
              [want_debug="$enableval"], [want_debug=no])

#build gui arg
AC_ARG_WITH([gui],
              AC_HELP_STRING([--without-gui],
              [do not build GUI @<:@default=no@:>@]),
              [with_gui="$withval"], [with_gui=yes])


if test "x$want_debug" = "xyes" -a $ac_cv_c_compiler_gnu != no; then
  CFLAGS="$CFLAGS -O0 -g"
  CXXFLAGS="$CXXFLAGS -O0 -g"
  AC_DEFINE([DEBUG], 1, [Define for debugging])
else
  CFLAGS="$CFLAGS -O2"
  CXXFLAGS="$CXXFLAGS -O2"
fi

AM_CONDITIONAL([HAVE_GUI], [test "x$with_gui" = "xyes"])
   
AC_PROG_CC
AC_PROG_CXX
AM_CONDITIONAL([HAVE_GCC], [test $CXX = g++])
AC_CHECK_SIZEOF([long unsigned int])
AM_CONDITIONAL([HAVE_64BIT], [test $ac_cv_sizeof_long_unsigned_int = 8])

AC_CONFIG_MACRO_DIR([m4])
m4_include([m4/ax_check_compile_flag.m4])
m4_include([m4/ax_swig_python.m4])
m4_include([m4/ax_pkg_swig.m4])
m4_include([m4/ax_python_devel.m4])
m4_include([m4/ax_python_module.m4])
m4_include([m4/ax_cxx_compile_stdcxx.m4])

#check for c++11
AX_CXX_COMPILE_STDCXX([11], [noext], [mandatory], [nodefault])

if test "x$with_gui" = "xyes"; then
#check for  swig

AC_CHECK_PROG([HAVE_SWIG], [swig], [yes], [no])
AS_IF([test $HAVE_SWIG == yes], [],
	[AC_MSG_ERROR([missing swig!])]) 

if test "x$cross_compiling" != "xyes"; then
	AX_SWIG_PYTHON([no])
	AS_IF([test -z $AX_SWIG_PYTHON_CPPFLAGS], 
		[AC_MSG_ERROR([failed to procure swig include path, make sure swig is installed])])
	AX_PYTHON_MODULE([psutil], [fatal])
else
AC_SUBST([AX_SWIG_PYTHON_CPPFLAGS], [`python-config --includes`])
fi

AC_MSG_RESULT([AX_SWIG_PYTHON_CPPFLAGS: $AX_SWIG_PYTHON_CPPFLAGS])

AC_CHECK_PROG([HAVE_PYRCC4], [pyrcc4], [yes], [no])
AS_IF([test $HAVE_PYRCC4 == yes], [],
	[AC_MSG_ERROR([missing pyrcc4 in path, make sure pyqt4-dev-tools is installed])]) 

AC_CHECK_PROGS([HAVE_LRELEASE], [lrelease lrelease-qt4], [no])
AS_IF([test $HAVE_LRELEASE == no],
	[AC_MSG_ERROR([missing lrelease in path, make sure qt4-linguist-tools is installed])], 
        [])

fi

AC_SUBST([CXX_STANDARD], $CXX_STANDARD)

dnl Determine build OS and do other OS-specific things.
case $host in
  *darwin*)
    BUILD_OS=darwin

    # Handle Mac OS X SDK flags.
    AC_ARG_WITH(macosx-sdk,
      [AS_HELP_STRING([--with-macosx-sdk=DIR],
        [compile using the SDK in DIR])])
    if test "${with_macosx_sdk}" != "" ; then
        test ! -d "${with_macosx_sdk}" && AC_MSG_ERROR([SDK "${with_macosx_sdk}" not found])
        CFLAGS="${CFLAGS} -isysroot ${with_macosx_sdk}"
        CXXFLAGS="${CXXFLAGS} -isysroot ${with_macosx_sdk}"
        OBJC="${OBJC} -isysroot ${with_macosx_sdk}"
    fi
    AC_ARG_WITH(macosx-version-min,
      [AS_HELP_STRING([--with-macosx-version-min=VERSION],
        [compile for Mac OS X VERSION and above])])
    if test "${with_macosx_version_min}" != "" ; then
        CFLAGS="${CFLAGS} -mmacosx-version-min=${with_macosx_version_min}"
        CXXFLAGS="${CXXFLAGS} -mmacosx-version-min=${with_macosx_version_min}"
        OBJC="${OBJC} -mmacosx-version-min=${with_macosx_version_min}"
    fi

    CXXFLAGS="${CXXFLAGS} -stdlib=libc++ -fPIC -pipe"
    LD="${LD} -stdlib=libc++ -std=c++11 -lc++ -undefined dynamic_lookup -headerpad_max_install_names"

    # There really ought to be some sort of Qt check here. M4 files don't work
    # well with Armory. Revisit this later. Not required, just nice to have.
    ;;
  *linux*)
    BUILD_OS=linux

    if test "x$with_gui" = "xyes"; then
       # Check existence of Qt packages.
       if ! pkg-config --exists 'QtCore >= 4.8 QtCore <= 5 QtGui >= 4.8 QtGui <= 5'; then
       	   AC_MSG_ERROR([missing QtCore library, make sure libqtcore4 and libqt4-dev are installed])
       fi
    fi
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

# Declare CFLAGS "unprecious" so that it can be passed directly to subdirs.
AC_DEFUN([AX_UNPRECIOUS], [
    m4_define([_AC_PRECIOUS_VARS], m4_bpatsubst(_AC_PRECIOUS_VARS, [$1
], []))
])
AX_UNPRECIOUS([CFLAGS])

export BUILD_OS
export CFLAGS
export CXXFLAGS
export LDFLAGS

AM_CONDITIONAL([HAVE_CLANG], [test x$CLANG = xyes])
AM_CONDITIONAL([BUILD_DARWIN], [test x$BUILD_OS = xdarwin])

AC_CONFIG_FILES(Makefile
		cppForSwig/Makefile
		cppForSwig/lmdb/Makefile
		BitcoinArmory.spec)

AM_CONDITIONAL([BUILD_TESTS], [test "x$want_tests" = "xyes"])
if test "x$want_tests" = "xyes"; then
AC_CONFIG_FILES(cppForSwig/gtest/Makefile)
fi

AC_OUTPUT

echo "  CC            = $CC"
echo "  CFLAGS        = $CFLAGS"
echo "  CPP           = $CPP"
echo "  CPPFLAGS      = $CPPFLAGS"
echo "  CXX           = $CXX"
echo "  CXXFLAGS      = $CXXFLAGS"
echo "  LDFLAGS       = $LDFLAGS"
echo "  LD            = $LD"
echo "  with tests    = $want_tests"
echo "  debug symbols = $want_debug"
echo "  with GUI      = $with_gui"
