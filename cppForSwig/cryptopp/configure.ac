#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.69])
AC_INIT([Cryptopp], [1], [weidai@github])
AM_INIT_AUTOMAKE([1.10 foreign -Wall -Werror])

AM_PROG_AR
LT_INIT

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
  CFLAGS="$CFLAGS -O2 -D_FORTIFY_SOURCE=2"
  CXXFLAGS="$CXXFLAGS -O2 -D_FORTIFY_SOURCE=2"
fi

# Checks for programs.
AC_PROG_CXX
AC_PROG_CC

AC_CONFIG_MACRO_DIR([m4])
m4_include([m4/ax_check_x86_features.m4])
m4_include([m4/ax_gcc_x86_cpu_supports.m4])

# Checks for header files.
AC_FUNC_ALLOCA
AC_CHECK_HEADERS([arpa/inet.h fcntl.h limits.h malloc.h netdb.h netinet/in.h stddef.h stdlib.h string.h sys/ioctl.h sys/socket.h sys/time.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_CHECK_HEADER_STDBOOL
AC_C_INLINE
AC_TYPE_SIZE_T
AC_TYPE_SSIZE_T
AC_CHECK_TYPES([ptrdiff_t])

# Checks for library functions.
AC_FUNC_MALLOC
AC_CHECK_FUNCS([gethostbyname gettimeofday memmove memset pow select setlocale socket])

AM_CONDITIONAL([CRYPTOPP_HAVE_CLANG], [test $CXX == clang++])
AM_CONDITIONAL([CRYPTOPP_HAVE_GCC], [test $CXX == g++])

AM_CONDITIONAL([UNAME_DARWIN], [test $(uname) == Darwin])
AM_CONDITIONAL([UNAME_LINUX], [test $(uname) == Linux])

AC_SUBST([HAS_X86], [false])

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

AM_CONDITIONAL([IS_X86], [test $HAS_X86 == true])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
