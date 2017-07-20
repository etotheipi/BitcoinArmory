#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.69])
AC_INIT([Cryptopp], [1], [weidai@github])
AM_INIT_AUTOMAKE([1.10 foreign -Wall -Werror])

AM_PROG_AR
LT_INIT

AC_CANONICAL_BUILD
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

# Checks for programs.
AC_PROG_CXX
AC_PROG_CC

AC_CONFIG_MACRO_DIR([m4])
m4_include([m4/ax_check_x86_features.m4])
m4_include([m4/ax_gcc_x86_cpu_supports.m4])

# Checks for header files.
AC_CHECK_HEADERS([arpa/inet.h fcntl.h limits.h malloc.h netdb.h netinet/in.h stddef.h stdlib.h string.h sys/ioctl.h sys/socket.h sys/time.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_CHECK_HEADER_STDBOOL
AC_C_INLINE
AC_TYPE_SIZE_T
AC_TYPE_SSIZE_T
AC_CHECK_TYPES([ptrdiff_t])

# Checks for library functions.
AC_CHECK_FUNCS([gethostbyname gettimeofday memmove memset pow select setlocale socket])

dnl Determine build OS.
BUILD_OS=
case $host in
  *darwin*)
    BUILD_OS=darwin
    ;;
  *linux*)
    BUILD_OS=linux
    ;;
esac

dnl Are we building for X86?
dnl For now, this may break Raspberry Pi cross-compiles. Fix later.
HOST_MACHINE=
AS_CASE([$host_cpu],
  [i?86], [HOST_MACHINE=x86],
  [x86_64], [HOST_MACHINE=x86],
  [AC_MSG_RESULT("No assembler code for CPU $host_cpu")]
)

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

AC_MSG_RESULT([$CLANG])
AC_SUBST([CLANG])

AM_CONDITIONAL([CRYPTOPP_HAVE_CLANG], [test x$CLANG = xyes])
AM_CONDITIONAL([CRYPTOPP_HAVE_GCC], [test $CXX == g++])

#set this otherwise autoconf complains about conditionals never getting defined
AM_CONDITIONAL([GAS210_OR_LATER], [test "a" == "b"])
AM_CONDITIONAL([GAS217_OR_LATER], [test "a" == "b"])
AM_CONDITIONAL([GAS219_OR_LATER], [test "a" == "b"])
AM_CONDITIONAL([HAVE_AES], [test "a" == "b"])
AM_CONDITIONAL([HAVE_PCLMUL], [test "a" == "b"])

if test $CXX == g++; then
AM_CONDITIONAL([GAS210_OR_LATER], [test $(as -v 2>&1 | egrep -c "GNU assembler version (2\.[1-9][0-9]|[3-9])")])
AM_CONDITIONAL([GAS217_OR_LATER], [test $(as -v 2>&1 | egrep -c "GNU assembler version (2\.1[7-9]|2\.[2-9]|[3-9])")])
AM_CONDITIONAL([GAS219_OR_LATER], [test $(as -v 2>&1 | egrep -c "GNU assembler version (2\.19|2\.[2-9]|[3-9])")])
AM_CONDITIONAL([HAVE_AES], [test $(grep -o -m 1 aes /proc/cpuinfo)])
AM_CONDITIONAL([HAVE_PCLMUL], [test $(grep -o -m 1 pclmul /proc/cpuinfo)])
fi

AM_CONDITIONAL([UNAME_LINUX], [test $(uname) == Linux])

AM_CONDITIONAL([BUILD_DARWIN], [test x$BUILD_OS = xdarwin])

AC_MSG_RESULT([cross compiling is set to: $cross_compiling])

if test "x$cross_compiling" != "xyes"; then
	AC_DEFUN_ONCE([_AX_GCC_X86_CPU_INIT],
	 [AC_LANG_PUSH([C])
	  AC_CACHE_CHECK([for gcc __builtin_cpu_init function],
	    [ax_cv_gcc_check_x86_cpu_init],
	    [AC_RUN_IFELSE(
	      [AC_LANG_PROGRAM([#include <stdlib.h>],
	        [__builtin_cpu_init ();])
	      ],
	      [ax_cv_gcc_check_x86_cpu_init=yes],
	      [ax_cv_gcc_check_x86_cpu_init=no])])])

	AS_IF([test "X$ax_cv_gcc_check_x86_cpu_init" = "Xyes"],
	   [AX_CHECK_X86_FEATURES([HAS_X86=true])])
fi	

AM_CONDITIONAL([IS_X86], [test x$HOST_MACHINE = xx86])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
