#include <win32_posix.h>

/***Path name resolution: have to preppend a '.' to paths starting with '/' or they'll be resolved as "system disk"/pathname
	
	All files should be opened in binary mode, as it is the posix standard, which Windows doesn't respect. Files opened without the binary flag will only return data up to the
	next null bytes. Not only will this yield messed up reads, CRCs will fail and the DB won't setup, returning with an error.
***/


int pread_win32(int fd, void *buff, unsigned int size, off_t offset)
{
	/***
	pread: reads file stream 'fd' from 'offset', for 'size' bytes, into 'buff', and returns the amount of bytes read, without changing the file pointer
	There is no cstd routine doing this on msvc. Have to use the ReadFile WinAPI, which requires get a WinAPI file handle from fd, which is done by
	_get_osfhandle. There is no need to destroy to handle.

	The main issue of this port is to respect atomicity of pread: it's fair to assume pread doesn't modify the file pointer at all, so a port that would 
	read the file, setting the pointer from the read, then rewind it, wouldn't be atomic regarding the file pointer. 
	
	Unsure if this is what ReadFile does with these OVERLAPPED settings, have to test it.
	***/
	unsigned int rt=-1;
	HANDLE hF = (HANDLE)_get_osfhandle(fd);
	if(hF)
	{
		OVERLAPPED ol;
		memset(&ol, 0, sizeof(OVERLAPPED)); //verify that this works for synchronous files as expected
		ol.Offset = offset;

		ReadFile(hF, buff, size, (DWORD*)&rt, &ol);
	}

	return (int)rt;
}

int ftruncate_win32(int fd, off_t length)
{
	/***
	Set size of file stream 'fd' to 'length'. 
		File pointer isn't modified (undefined behavior on shrinked files beyond the current pointer?)
		Shrinked bytes are lost
		Extended bytes are set to 0
		If file is mapped and shrinked beyond whole mapped pages, the pages are discarded

		In our impementation we ignore all mapping related code as ftruncate is called before a file is mapped or after it's unmapped within leveldb.
		The WinAPI call used, SetEndOfFile, requires that the file is unmapped, however there won't be an issue on this front (at this point).
		
		No extended bytes will be set to 0, as there doesn't seem to be a need for that. In order to perform this task, find the end of the file and add the extra 0s from there on, 
		as necessary.
	***/


	HANDLE hF = (HANDLE)_get_osfhandle(fd);

	if(hF)
	{
		unsigned int cpos = _tell(fd); //save current file pointer pos for restoring later
		if(cpos!= 0xFFFFFFFF)
		{
			if(SetFilePointer((HANDLE)hF, length, 0, FILE_BEGIN)!=0xFFFFFFFF) //set file pointer to length
			{
				if(SetEndOfFile((HANDLE)hF))
				{
					//file size has been changed, set pointer to back to cpos
					SetFilePointer((HANDLE)hF, cpos, 0, FILE_BEGIN);

					//set all new bytes to 0
					/*byte *null_bytes = (byte*)malloc(length);
					memset(null_bytes, 0, length);
					_write(fd, null_bytes, length);
					free(null_bytes);
					
					SetFilePointer((HANDLE)hF, cpos, 0, FILE_BEGIN);*/
					return 0; //returns 0 on success
				}
			}
		}
		
	}

	return -1;
}

int access_win32(const char *path, int mode)
{
	if(path[0]=='/')
	{
		char *win32_path = posix_path_to_win32(path);

		int i = _access(win32_path, mode);
		free(win32_path);
	
		return i;
	}
	else return _access(path, mode);
}

int unlink_win32(const char *path)
{
	if(path[0]=='/')
	{
		char *win32_path = posix_path_to_win32(path);

		int i = _unlink(win32_path);
		free(win32_path);

		return i;
	}
	else return _unlink(path);
}

int open_win32(const char *path, int flag, int pmode)
{
	if(path[0]=='/')
	{
		char *win32_path = posix_path_to_win32(path);

		int i = _open(win32_path, flag | _O_BINARY, pmode);
		free(win32_path);
		
		return i;
	}
	else return _open(path, flag | _O_BINARY, pmode);
}

int open_win32(const char *path, int flag)
{
	/***In leveldb, Open(2) may be called to get a file descriptor for a directory. Win32's _open won't accept directories as entry so you're kebab. This port is particularly 
	annoying as you need to simulate calls to a single posix function that split into 2 different types of routine based on the input.

	This how this shit will go:
	1) try to _open the path
	2) if it fails, check error, if it's complaining about the filename not existing check if it's a directory will GetFileAttributes
	3) if it is, open it with create file and return that
	***/
	HANDLE fHandle;
	DWORD desired_access = GENERIC_READ;
	DWORD disposition = OPEN_EXISTING;
	DWORD attributes = FILE_FLAG_POSIX_SEMANTICS;
	if(flag)
	{
		if(flag && _O_RDWR) desired_access |= GENERIC_WRITE;
		if(flag && _O_CREAT) disposition = CREATE_ALWAYS;
		//if(flag && _O_TRUNC) opening |= TRUNCATE_EXISTING;
	}

	if(path[0]=='/')
	{
		char *win32_path = posix_path_to_win32(path);
		if(GetFileAttributes(win32_path)==FILE_ATTRIBUTE_DIRECTORY) 
		{
			attributes |= FILE_FLAG_BACKUP_SEMANTICS;
			desired_access |= GENERIC_WRITE; //grant additional write access to folders, can't flush the folder without it
		}

		fHandle = CreateFile(win32_path, desired_access, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, disposition, attributes, NULL);
		free(win32_path);
	}
	else 
	{
		if(GetFileAttributes(path)==FILE_ATTRIBUTE_DIRECTORY) 
		{
			attributes |= FILE_FLAG_BACKUP_SEMANTICS;
			desired_access |= GENERIC_WRITE;
		}
		fHandle = CreateFile(path, desired_access, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, disposition, attributes, NULL);
	}

	if(fHandle!=INVALID_HANDLE_VALUE)
	{
		return _open_osfhandle((intptr_t)fHandle, 0);
	}
	else
	{
		//signal errors;
		_set_errno(EBADF);
		return -1;
	}

	/*if(path[0]=='/')
	{
		char *win32_path = posix_path_to_win32(path);

		int i = _open(win32_path, flag | _O_BINARY);
		free(win32_path);
		
		return i;
	}
	else return _open(path, flag | _O_BINARY);*/
}

int mkdir_win32(const char *path, int mode)
{
	/*** POSIX mkdir also sets directory access rights through 'mod'. While this makes sense in UNIX OSs, it's more or less pointless on a Windows platform. Access rights can be
	mimiced on Windows, but the software would require certain rights that I suspect would require running it at admin. Enforcing rights is however irrelevant to proper function
	of mkdir on Windows. Will come back to this later for full implementation if it reveals itself needed.

	Some behavior to pay attention to:
	mkdir can only create a single directory per call. If there are several of them to create in the indicate path, you have to cut down the path name to every single unmade path.
	***/

	int l = strlen(path), s=0, i;
	char *rm_path = (char*)malloc(l+2);
	if(path[0]=='/')
	{
		rm_path[0] = '.';
		strcpy(rm_path +1, path);
		l++;
	}
	else strcpy(rm_path, path);


	while(s<l)
	{
		if(rm_path[s]=='/')
		{
			rm_path[s]=0;
			i = _mkdir(rm_path);
			rm_path[s] = '/';
			
			if(i==-1) 
			{
				errno_t err;
				_get_errno(&err);
				if(err!=EEXIST)
				{
					break;
				}
			}
		}
		s++;
	}

	i = _mkdir(rm_path); //last mkdir in case the the path name doesn't end with a '/'

	free(rm_path);
	
	return i;
}

int rmdir_win32(const char *path)
{
	if(path[0]=='/')
	{
		char *win32_path = posix_path_to_win32(path);

		int i = _rmdir(win32_path);
		free(win32_path);
	
		return i;
	}
	else return _rmdir(path);
}

int rename_win32(const char *oldname, const char *newname)
{
	char *oldname_win32, *newname_win32; 

	oldname_win32 = posix_path_to_win32(oldname);
	newname_win32 = posix_path_to_win32(newname);

	int o=0;
	if(!MoveFileEx(oldname_win32, newname_win32, MOVEFILE_REPLACE_EXISTING)) //posix rename replaces existing files
	{
		DWORD last_error = GetLastError();
		if(last_error==ERROR_FILE_NOT_FOUND) _set_errno(ENOENT);
		else _set_errno(EINVAL); //global error thrown
		o=-1;
	}

	free(oldname_win32);
	free(newname_win32);

	return o;
}

int stat_win32(const char *path, struct stat *Sin)
{
	/***
	Regarding stat: for stat to point at the function and not the struct in win32, sys/types.h has to be declared BEFORE sys/stat.h, which isn't the case with env_posix.cc
	This one is a bit painful. In order for the function to be accessible, it has to be defined after the struct. Since the attempt of this port is to limit modification of source file
	to a maximum, the idea is to #define stat to stat_win32 and perform all the required handling over here. However life isn't so simple: this #define makes the struct unaccessible
	since #define doesn't discriminate between the function and the struct. However, now that stat (the function) has been defined to another name (stat_win32) we can redefine the
	structure. However we can't simply use this #define before the sys/stat.h include since stat would then be redefined as a function, cancelling the whole process
	***/
	if(path[0]=='/')
	{
		char *path_win32 = (char*)malloc(strlen(path)+2);
		path_win32[0] = '.';
		strcpy(path_win32 +1, path);

		int i = _stat(path_win32, (struct _stat64i32*)Sin);
		free(path_win32);

		return i;
	}
	else return _stat(path, (struct _stat64i32*)Sin);
}

FILE* fopen_win32(const char *path, const char *mode)
{
	char *mode_win32 = (char*)malloc(5);
	strcpy(mode_win32, mode);
	strcat(mode_win32, "b");
	
	if(path[0]=='/')
	{
		char *path_win32 = posix_path_to_win32(path);

		FILE *f;
		f = _fsopen(path_win32, mode_win32, _SH_DENYNO);

		free(mode_win32);
		free(path_win32);
		return f;
	}
	else
	{
		FILE *f;
		fopen_s(&f, path, mode_win32);

		free(mode_win32);
		return f;
	}
}

int fsync_win32(int fd)
{
	HANDLE fHandle = (HANDLE)_get_osfhandle(fd);

	if(FlushFileBuffers(fHandle)) return 0; //success
	else
	{
		_set_errno(EBADF);
		return -1;
	}
}

int gettimeofday_win32(timeval *tv, timeval *tz)
{
	/***
	tv: if it is set, fill it with time in seconds and useconds from unix epoch (wtf long?)
	tz: if it is set, fill it with timezone

	tz is usually obsolete and leveldb doesn't use it, not gonna port it for now.
	Only used for loggging purposes in leveldb
	***/

	if(tv)
	{
		time_t tt;
		time(&tt);

		tv->tv_sec = (long)tt;

		DWORD usc = GetTickCount() % 1000; //trollish approach to µs, will do for now
		tv->tv_usec = (long)tt*1000 +usc;
	}

	return -1;
}

tm* localtime_r_win32(const time_t *tin, tm *tout)
{
	//straight forward porting
	if(!localtime_s(tout, tin)) //success
		return tout;

	return 0;
}

int geteuid_win32()
{
	/*** Returns user's ID as an integer. User name can be retrieved for Windows, but that's a string. Closest to it is the SID. Note that leveldb uses this function only for
	logging purposes, same as time functions, so the result is not system critical
	***/

	return 0;
}

void usleep_win32(unsigned long long in)
{
	/*** µsec sleep isn't really meant to be achieved on windows environments. Sleep itself is but a hint to thread scheduler. Possible solutions are to use Sleep() 
		 with millisecond granularity or poll an OS high resolution timer, like QueryPerformanceCounter, until the wait it hit.

		 Either solution aren't any good, the high resolution timer function seems less expensive
	***/
	if(in<10000)
	{
		unsigned long long tick;
		QueryPerformanceCounter((LARGE_INTEGER*)&tick);

		unsigned long long fq;
		QueryPerformanceFrequency((LARGE_INTEGER*)&fq);

		unsigned long long wait = (fq*in)/1000000 +tick;

		while(wait>tick) QueryPerformanceCounter((LARGE_INTEGER*)&tick);
	}
	else
	{
		unsigned int wait = (unsigned int)in/1000;
		Sleep(wait);
	}
}

long getpagesize_win32() 
{
    SYSTEM_INFO system_info;
    GetSystemInfo(&system_info);
    return system_info.dwPageSize;
}

int fcntl_win32(int fd, unsigned int command, flock *f)
{
	if(command==F_SETLK)
	{
		int lm = (f->l_type ? _LK_NBLCK : _LK_UNLCK);
		return _locking(fd, lm, 0);
	}

	return -1;
}

char *posix_path_to_win32(const char *posix_path)
{
	/*** As the name indicates, turns unix path convention to win32. The only necessary task is to turn all '/' directory delimiters into '\\' 
	Don't forget to free the returned char* ***/

	int l = strlen(posix_path) +1, i=0;
	char *win32_path = (char*)malloc(l+1);
	win32_path[0] = '.';
	strcpy(win32_path +1, posix_path);
	
	return win32_path;
}

char *posix_path_to_win32_full(const char *posix_path)
{
	int i=0;
	int l=strlen(posix_path) +1;
	char *win32_path = (char*)malloc(l +2);
	
	if(posix_path[0]=='/')
	{
		strcpy(win32_path, "..");
		l+=2;
	}
	else win32_path[0] = 0;

	strcat(win32_path, posix_path);

	while(i<l)
	{
		if(win32_path[i]=='/')
			win32_path[i++] = '\\';
		
		i++;
	}

	return win32_path;
}


int c99_vsnprintf(char* str, size_t size, const char* format, va_list ap)
{
    int count = -1;

    if (size != 0)
        count = _vsnprintf_s(str, size, _TRUNCATE, format, ap);
    if (count == -1)
        count = _vscprintf(format, ap);

    return count;
}

int c99_snprintf(char* str, size_t size, const char* format, ...)
{
    int count;
    va_list ap;

    va_start(ap, format);
    count = c99_vsnprintf(str, size, format, ap);
    va_end(ap);

    return count;
}
