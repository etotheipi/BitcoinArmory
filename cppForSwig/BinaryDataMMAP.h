////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _BINARYDATAMMAP_H_
#define _BINARYDATAMMAP_H_

#include "BinaryData.h"


// Memory-Mapped Files.  Unfortunately, completely different between Win & Linux
#if defined(_MSC_VER) || defined(__MINGW32__)
   // TODO: Add the windows versions of these function calls
   #include <windows.h>
#else
   #include <sys/mman.h>
   #include <limits.h>
   /* This comes from limits.h if it's not defined there set a sane default */
   #ifndef PAGESIZE
      #include <unistd.h>
      #define PAGESIZE sysconf(_SC_PAGESIZE)
   #endif

   // I don't believe any of the below defines are necessary, because we will 
   // always use the ptr = mmap(NULL, ...) version which ALWAYS returns a ptr to the 
   // start of a memory page.
   //#define  munmap(ptr,sz)     ( munmap(PAGEFLOOR(ptr,sz), PAGERANGE(ptr,sz)))
   //#define  mremap(ptr,sz)     ( mremap(PAGEFLOOR(ptr,sz), PAGERANGE(ptr,sz)))
   //#define madvise(ptr,sz,adv) (madvise(PAGEFLOOR(ptr,sz), PAGERANGE(ptr,sz), adv))
   

   #ifdef POSIX
      #define POSIX_MADV_SEQUENTIAL MADV_SEQUENTIAL
      #define POSIX_MADV_RANDOM     MADV_RANDOM
   #endif
#endif


#define FILE_DOES_NOT_EXIST UINT64_MAX


class BinaryDataMMAP 
{
public:
   BinaryDataMMAP(void)     { init(); }
   BinaryDataMMAP(uint64_t) { init(); } 
   BinaryDataMMAP(string filename);

   void init(void);

   static uint64_t getFilesize(string filename);

   void clear(void) {}
   uint8_t* getPtr(void)  {return ptr_;}
   uint64_t getSize(void) {return size_;}

   bool createMMAP(string filename);
   //bool  remapMMAP(string filename);
   void deleteMMAP(void);

   void setAdvice(int advice);


private:
   uint8_t* ptr_;
   uint64_t size_;   

   string filename_;
   int32_t fileDescriptor_;
};



#endif
