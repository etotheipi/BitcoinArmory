dnl require autoconf 2.60 (AS_ECHO/AS_ECHO_N)
AC_PREREQ([2.60])
define(_CLIENT_VERSION_IS_RELEASE, false)
define(_COPYRIGHT_YEAR, 2015)
AC_INIT([Armory],m4_esyscmd([grep "^BTCARMORY_VERSION" armoryengine/ArmoryUtils.py | cut -d "(" -f2 | cut -d ")" -f1 | tr -d '[[:space:]]' | tr ',' '.']))
AC_CONFIG_SRCDIR([cppForSwig/BlockObj.cpp])
AC_CONFIG_AUX_DIR([build-aux])
AC_CONFIG_MACRO_DIR([build-aux/m4])

AC_CANONICAL_HOST

dnl faketime breaks configure and is only needed for make. Disable it here.
unset FAKETIME

case $host in
    *mingw*)
        TARGET_OS=windows
        ;;
    *darwin*)
        TARGET_OS=darwin
        ;;
    *linux*)
        TARGET_OS=linux
        ;;
    *)
        ;;
esac

case $build_os in
    *mingw*)
        BUILD_OS=windows
        ;;
    *darwin*)
        BUILD_OS=darwin
        ;;
    *linux*)
        BUILD_OS=linux
        ;;
    *)
        ;;
esac

dnl Automake init set-up and checks
AM_INIT_AUTOMAKE([no-define subdir-objects foreign])

# Enable debug
AC_ARG_ENABLE([debug],
    [AS_HELP_STRING([--enable-debug],
                    [use debug compiler flags and macros (default is no)])],
    [enable_debug=$enableval],
    [enable_debug=no])

dnl Define variables
AC_ARG_VAR([PYVER], [Defines the version of Python to use (e.g. python2.7)])
if test "x$PYVER" = "x"; then
    PYVER="python"
fi

PYTHON_INCLUDES=`$PYVER-config --includes`
PYTHON_LIBS=`$PYVER-config --libs`


dnl Make variables available to Makefiles
AC_SUBST(PYTHON_INCLUDES)
AC_SUBST(PYTHON_LIBS)

AM_CONDITIONAL([TARGET_LINUX], [test x$TARGET_OS = xlinux])
AM_CONDITIONAL([TARGET_DARWIN], [test x$TARGET_OS = xdarwin])
AM_CONDITIONAL([TARGET_WINDOWS], [test x$TARGET_OS = xwindows])
AM_CONDITIONAL([BUILD_LINUX], [test x$BUILD_OS = xlinux])
AM_CONDITIONAL([BUILD_DARWIN], [test x$BUILD_OS = xdarwin])
AM_CONDITIONAL([BUILD_WINDOWS], [test x$BUILD_OS = xwindows])

dnl Set compiler flags
if test "x$enable_debug" = xyes; then
    CFLAGS='-g3 -Wall -pipe -fPIC'
    CXXFLAGS='-g3 -Wall -pipe -fPIC'
else
    CFLAGS='-O2 -pipe -fPIC'
    CXXFLAGS='-O2 -pipe -fPIC'
fi

dnl Compiler checks
AM_PROG_AR
AC_PROG_CC
AC_PROG_CXX
AC_PROG_RANLIB

dnl Check for C++11 strict conformance mode (-std=c++11)
AX_CXX_COMPILE_STDCXX_11([noext])

AC_CONFIG_FILES([Makefile cppForSwig/Makefile])
AC_OUTPUT
