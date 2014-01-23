/*

    Implementation of POSIX directory browsing functions and types for Win32.

    Author:  Kevlin Henney (kevlin@acm.org, kevlin@curbralan.com)
    History: Created March 1997. Updated June 2003 and July 2012.
    Rights:  See end of file.

*/


#include <dirent_win32.h>
#include <errno.h>
#include <io.h> /* _findfirst and _findnext set errno iff they return -1 */
#include <stdlib.h>
#include <string.h>
#include <Windows.h>

typedef ptrdiff_t handle_type; /* C99's intptr_t not sufficiently portable */

struct DIR
{
    handle_type         handle; /* -1 for failed rewind */
    //struct _finddata_t  info;
    struct _wfinddata_t winfo;
    struct dirent       result; /* d_name null iff first time */
    //char                *name;  /* null-terminated char string */
    wchar_t             *wname;  /* null-terminated wchar string */
};

/*DIR *opendir(const char *name)
{
    DIR *dir = 0;

    if(name && name[0])
    {
        size_t base_length = strlen(name);
        const char *all = 
            strchr("/\\", name[base_length - 1]) ? "*" : "/*";

        if((dir = (DIR *) malloc(sizeof *dir)) != 0 &&
           (dir->name = (char *) malloc(base_length + strlen(all) + 2)) != 0)
        {
			//make sure '.' is prepended to paths starting with '/'
			if(name[0]=='/') 
			{
				dir->name[0] = '.';
				dir->name[1] = 0;
			}
			else dir->name[0] = 0;
            
			strcat(strcat(dir->name, name), all);

            if((dir->handle =
                (handle_type) _findfirst(dir->name, &dir->info)) != -1)
            {
                dir->result.d_name = 0;
            }
            else
            {
                free(dir->name);
                free(dir);
                dir = 0;
            }
        }
        else
        {
            free(dir);
            dir   = 0;
            errno = ENOMEM;
        }
    }
    else
    {
        errno = EINVAL;
    }

    return dir;
}*/

DIR *opendir(const char *name)
{
	wchar_t *namew = (wchar_t*)malloc(sizeof(wchar_t)*(strlen(name)+1));
	MultiByteToWideChar(CP_UTF8, 0, name, -1, namew, strlen(name)+1);
	
	DIR *rtdir = opendir(namew);
	free(namew);
	
	return rtdir;
}

DIR *opendir(const wchar_t *name)
{
    DIR *dir = 0;

    if(name && name[0])
    {
        size_t base_length = wcslen(name);
        const wchar_t *all = /* search pattern must end with suitable wildcard */
            wcschr(L"/\\", name[base_length - 1]) ? L"*" : L"/*";

        if((dir = (DIR *) malloc(sizeof *dir)) != 0 &&
           (dir->wname = (wchar_t *) malloc(sizeof(wchar_t)*(base_length + wcslen(all) + 2))) != 0)
        {
			dir->result.d_name = 0;

			//make sure '.' is prepended to paths starting with '/'
			if(name[0]==L'/') 
			{
				dir->wname[0] = L'.';
				dir->wname[1] = 0;
			}
			else dir->wname[0] = 0;
            
			wcscat(wcscat(dir->wname, name), all);

            if((dir->handle =
                (handle_type) _wfindfirst(dir->wname, &dir->winfo)) != -1)
            {
                dir->result.wd_name = 0;
				dir->result.d_name = (char*)malloc(MAX_PATH);
            }
            else /* rollback */
            {
                free(dir->wname);
                free(dir);
                dir = 0;
            }
        }
        else /* rollback */
        {
            free(dir);
            dir   = 0;
            errno = ENOMEM;
        }
    }
    else
    {
        errno = EINVAL;
    }

    return dir;
}

int closedir(DIR *dir)
{
    int result = -1;

    if(dir)
    {
        if(dir->handle != -1)
        {
            result = _findclose(dir->handle);
        }

        if(dir->result.d_name) free(dir->result.d_name);
        free(dir->wname);
       free(dir);
    }

    if(result == -1) /* map all errors to EBADF */
    {
        errno = EBADF;
    }

    return result;
}

struct dirent *readdir(DIR *dir)
{
    struct dirent *result = 0;

    if(dir && dir->handle != -1)
    {
        if(!dir->result.wd_name || _wfindnext(dir->handle, &dir->winfo) != -1)
        {
            result         = &dir->result;
            result->wd_name = dir->winfo.name;
			WideCharToMultiByte(CP_UTF8, 0, dir->winfo.name, -1, result->d_name, MAX_PATH, 0, 0);
        }
    }
    else
    {
        errno = EBADF;
    }

    return result;
}

void rewinddir(DIR *dir)
{
    if(dir && dir->handle != -1)
    {
        _findclose(dir->handle);
        dir->handle = (handle_type) _wfindfirst(dir->wname, &dir->winfo);
        dir->result.wd_name = 0;
		dir->result.d_name[0] = 0;
    }
    else
    {
        errno = EBADF;
    }
}

/*

    Copyright Kevlin Henney, 1997, 2003, 2012. All rights reserved.

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose is hereby granted without fee, provided
    that this copyright and permissions notice appear in all copies and
    derivatives.
    
    This software is supplied "as is" without express or implied warranty.

    But that said, if there are any problems please get in touch.

*/