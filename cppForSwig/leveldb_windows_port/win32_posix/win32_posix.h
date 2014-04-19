#include <fstream>
#include <io.h>
#include <mman.h>
#include <file.h>
#include <time.h>
#include <sys/locking.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <Windows.h>
#include <dirent_win32.h>
#include <direct.h>
#include <sys/stat.h>
#include "stdint.h"

#if defined LEVELDB_DLL
#define LEVELDB_EXPORT __declspec(dllimport)
#elif defined DLL_BUILD
#define LEVELDB_EXPORT __declspec(dllexport)
#else
#define LEVELDB_EXPORT 
#endif

#define F_OK 0
typedef int __ssize_t;
typedef __ssize_t ssize_t;

#ifdef small
	#undef small
#endif

#ifdef large
	#undef large
#endif

#ifdef DeleteFile
#undef DeleteFile
#endif

//straight forward ports
#define fread_unlocked _fread_nolock
#define fwrite_unlocked _fwrite_nolock
#define fflush_unlocked _fflush_nolock
#define fsync fsync_win32
#define fdatasync fsync_win32
#define close _close
#define open open_win32
#define access access_win32
#define unlink unlink_win32
#define rmdir rmdir_win32
#define mkdir mkdir_win32
#define rename rename_win32
#define fopen fopen_win32
#define stat stat_win32


/***
Regarding stat: for stat to point at the function and not the struct in win32, sys/types.h has to be declared BEFORE sys/stat.h, which isn't the case with env_posix.cc
This one is a bit painful. In order for the function to be accessible, it has to be defined after the struct. Since the attempt of this port is to limit modification of source file
to a maximum, the idea is to #define stat to stat_win32 and perform all the required handling over here. However life isn't so simple: this #define makes the struct unaccessible
since #define doesn't discriminate between the function and the struct. However, now that stat (the function) has been defined to another name (stat_win32) we can redefine the
structure. However we can't simply use this #define before the sys/stat.h include since stat would then be redefined as a function, cancelling the whole process
***/

struct stat {
        _dev_t     st_dev;
        _ino_t     st_ino;
        unsigned short st_mode;
        short      st_nlink;
        short      st_uid;
        short      st_gid;
        _dev_t     st_rdev;
        _off_t     st_size;
        __time64_t st_atime;
        __time64_t st_mtime;
        __time64_t st_ctime;
        };


int open_win32(const char *path, int flag, int pmode);
int open_win32(const char *path, int flag);
int access_win32(const char *path, int mode);
int unlink_win32(const char *path);
int rmdir_win32(const char *path);
int rmdir_win32(std::string st_in);
int mkdir_win32(const char *path, int mode);
int mkdir_win32(std::string st_in);
int rename_win32(const char *oldname, const char *newname);
int stat_win32(const char *path, struct stat *Sin);
FILE* fopen_win32(const char *path, const char *mode);
int fsync_win32(int fd);
int fread_unlockd(void *_DstBuf, size_t _EleSize, size_t _Count, FILE *_file);


wchar_t *posix_path_to_win32(const char *posix_path);
wchar_t *posix_path_to_win32_full(const char *posix_path);

#define va_copy(d,s) ((d) = (s))

#define pread pread_win32
int pread_win32(int fd, void *buff, unsigned int size, off_t offset);

#define ftruncate ftruncate_win32
int ftruncate_win32(int fd, off_t length);

#define gettimeofday gettimeofday_win32
int gettimeofday_win32(timeval *tv, timeval *tz);

#define localtime_r localtime_r_win32
tm* localtime_r_win32(const time_t *tin, tm *tout);

#define geteuid geteuid_win32
int geteuid_win32();

#define usleep usleep_win32
void usleep_win32(unsigned long long in);

#define getpagesize getpagesize_win32
long getpagesize_win32(); 

#define F_WRLCK		_LK_NBLCK
#define F_UNLCK		_LK_UNLCK
#define F_SETLK		1

struct flock
{
	unsigned _int32 l_type, l_whence, l_start, l_len;
};

#define fcntl fcntl_win32
int fcntl_win32(int fd, unsigned _int32 command, flock *f);

#define strdup _strdup
/***
consider redoing snprintf
***/
#define snprintf c99_snprintf //stick to this for now unless it fucks up horribly
int c99_vsnprintf(char* str, size_t size, const char* format, va_list ap);
int c99_snprintf(char* str, size_t size, const char* format, ...);
