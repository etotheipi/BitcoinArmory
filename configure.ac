AC_PREREQ(2.60)
AC_INIT([BitcoinArmory], [0.95.99], [moothecowlord@gmail.com])
AM_INIT_AUTOMAKE([1.10 subdir-objects foreign -Wall -Werror])
LT_INIT

AC_PROG_CC
AC_PROG_CXX

AC_CONFIG_MACRO_DIR([m4])
m4_include([m4/ax_check_compile_flag.m4])

AX_CHECK_COMPILE_FLAG([-std=c++11], [compile_flag_cxx11=yes])
if test "x${compile_flag_cxx11}" = "xyes"; then
	CXXFLAGS="-std=c++11 $CXXFLAGS"
	CXX_STANDARD=201103L
else
    AC_MSG_ERROR([need c++ 11 compiler])
fi

AM_PATH_PYTHON
AC_ARG_VAR([PYTHON_CONFIG], [Path to python-config])
AS_IF([test -z "$PYTHON_INCLUDE"], [
  AS_IF([test -z "$PYTHON_CONFIG"], [
    AC_PATH_PROGS([PYTHON_CONFIG],
                  [python$PYTHON_VERSION-config python-config],
                  [no],
                  [`dirname $PYTHON`])
    AS_IF([test "$PYTHON_CONFIG" = no], [AC_MSG_ERROR([cannot find python-config for $PYTHON.])])
  ])
  AC_MSG_CHECKING([python include flags])
  PYTHON_INCLUDE=`$PYTHON_CONFIG --includes`
  AC_MSG_RESULT([$PYTHON_INCLUDE])
])

AC_SUBST([PYTHONINC], [$PYTHON_INCLUDE])

AC_SUBST([CXX_STANDARD])

AC_CONFIG_SUBDIRS([cppForSwig/fcgi])

AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES(Makefile 
		cppForSwig/Makefile 
		cppForSwig/lmdb/Makefile 
		cppForSwig/fcgi/Makefile)

AC_OUTPUT
