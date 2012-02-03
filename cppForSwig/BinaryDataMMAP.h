////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>             //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _BINARYDATAMMAP_H_
#define _BINARYDATAMMAP_H_

#include <stdio.h>

#if defined(_MSC_VER) || defined(__MINGW32__)
   #include <windows.h>
#else
   #include <sys/mman.h>
   size_t page_size = (size_t)sysconf(_SC_PAGESIZE);
#endif
