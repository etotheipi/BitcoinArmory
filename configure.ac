dnl require autoconf 2.60 (AS_ECHO/AS_ECHO_N)
AC_PREREQ([2.60])
define(_CLIENT_VERSION_IS_RELEASE, false)
define(_COPYRIGHT_YEAR, 2015)
AC_INIT([Armory],m4_esyscmd([grep "^BTCARMORY_VERSION" armoryengine/ArmoryUtils.py | cut -d "(" -f2 | cut -d ")" -f1 | tr -d '[[:space:]]' | tr ',' '.']),[bugs@bitcoinarmory.com])
AC_CONFIG_SRCDIR([cppForSwig/BlockObj.cpp])
AC_CONFIG_AUX_DIR([build-aux])

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

dnl Automake init set-up and checks
AM_INIT_AUTOMAKE([no-define subdir-objects foreign])

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
AM_CONDITIONAL([DEBUG], [test x = y])

dnl Set compiler flags
dnl Use "x" = "y" for now to force non-debug mode until flag is added
if test "x" = "y"; then
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

AC_CONFIG_FILES([Makefile cppForSwig/Makefile])
AC_OUTPUT
