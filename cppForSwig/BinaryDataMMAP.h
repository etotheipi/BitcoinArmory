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
#include "BinaryData.h"


// This is used to attempt to keep keying material out of swap
// I am stealing this from bitcoin 0.4.0 src, serialize.h
#if defined(_MSC_VER) || defined(__MINGW32__)
   // Note that VirtualLock does not provide this as a guarantee on Windows,
   // but, in practice, memory that has been VirtualLock'd almost never gets written to
   // the pagefile except in rare circumstances where memory is extremely low.
   #include <windows.h>
   #define mlock(p, n) VirtualLock((p), (n));
   #define munlock(p, n) VirtualUnlock((p), (n));
#else
   #include <sys/mman.h>
   #include <limits.h>
   /* This comes from limits.h if it's not defined there set a sane default */
   #ifndef PAGESIZE
      #include <unistd.h>
      #define PAGESIZE sysconf(_SC_PAGESIZE)
   #endif

   #define    mmap(ptr,sz)     (   mmap(PAGEFLOOR(ptr,sz), PAGERANGE(ptr,sz)))
   #define  munmap(ptr,sz)     ( munmap(PAGEFLOOR(ptr,sz), PAGERANGE(ptr,sz)))
   #define  mremap(ptr,sz)     ( mremap(PAGEFLOOR(ptr,sz), PAGERANGE(ptr,sz)))
   #define madvise(ptr,sz,adv) (madvise(PAGEFLOOR(ptr,sz), PAGERANGE(ptr,sz), adv))
#endif



class BinaryDataMMAP 
{
public:
   BinaryDataMMAP(void) {}
   BinaryDataMMAP(string filename);

   static uint64_t getFilesize(string filename);

   void clear(void) {}
   void getPtr(void)  {return ptr_;}
   void getSize(void) {return size_;}

   void createMMAP(string filename);
   void resizeMMAP(string filename);


private:
   uint8_t* ptr_;
   uint64_t size_;   

   string filename_;
};



