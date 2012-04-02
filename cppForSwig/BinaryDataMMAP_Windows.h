////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _BINARYDATAMMAP_H_
#define _BINARYDATAMMAP_H_

#include <windows.h>
#include <memory.h>
#include "BinaryData.h"

// Memory-Mapped Files.  Unfortunately, completely different between Win & Linux
#define MADV_SEQUENTIAL 0
#define MADV_RANDOM     1

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
   HFILE  hFile_;
   HANDLE hFileMapping_;
};



#endif
