////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include <iostream>
#include <fstream>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include "BinaryData.h"
#include "BinaryDataMMAP_Windows.h"

#include <windows.h>
#include <memory.h>


void BinaryDataMMAP::init(void)
{
   ptr_  = NULL;
   size_ = UINT64_MAX;
   filename_ = string("");
   fileDescriptor_ = -1;
}

BinaryDataMMAP::BinaryDataMMAP(string filename)
{
   init();
   createMMAP(filename);
}


////////////////////////////////////////////////////////////////////////////////
uint64_t BinaryDataMMAP::getFilesize(string filename)
{
   ifstream is(filename.c_str(), ios::in|ios::binary);
   if(!is.is_open())
      return UINT64_MAX;

   is.seekg(0, ios::end);
   uint64_t filesize = (size_t)is.tellg();
   is.close();
   return filesize;
}



////////////////////////////////////////////////////////////////////////////////
// We need to "advise" the system about our expected access patterns
void BinaryDataMMAP::setAdvice(int advice)
{
   // Do nothing, until I figure out how to set advice similarly...
   if(advice==MADV_SEQUENTIAL)
   {
   }
   else if(advice==MADV_RANDOM)
   {
   }
}


////////////////////////////////////////////////////////////////////////////////
bool BinaryDataMMAP::createMMAP(string filename)
{
   size_ = getFilesize(filename);
   if( size_==FILE_DOES_NOT_EXIST )
      return false;


   // *********************************************************************** //
   // Open the file to be mapped
   hFile_ =  CreateFile(
                     filename.c_str(),
                     GENERIC_READ,
                     FILE_SHARE_READ,
                     NULL,
                     OPEN_EXISTING,
                     FILE_ATTRIBUTE_NORMAL,
                     NULL);

   if(hFile_ == INVALID_HANDLE_VALUE)
   {
      cout << "***ERROR: CreateFile failed!" << endl;
      return false;
   }


   // *********************************************************************** //
   // Create the file-mapping object/handle
   hFileMapping_ = CreateFileMapping( 
                                 hFile_,
                                 NULL,
                                 PAGE_READONLY,
                                 0,
                                 0,
                                 NULL);
   if(hFileMapping == NULL)
   {
      cout << "***ERROR: CreateFileMapping failed!" << endl;
      return false;
   }


   // *********************************************************************** //
   // Associate the handle with a pointer and access flags
   ptr_ = (uint8_t*)MapViewOfFile(
                              hFileMapping,
                              FILE_MAP_READ,
                              0,
                              0,
                              (SIZE_T)size_);

   if(ptr_ == NULL)
   {
      cout << "***ERROR: mmap'ing file failed, despite exist w/ read access." << endl;
      return false;
   }

   
   // Usually we will be scanning the whole file sequentially, after creation
   setAdvice(MADV_SEQUENTIAL);
   return true; 
}


////////////////////////////////////////////////////////////////////////////////
/*  There may be issues with all my pointers becoming invalid if the mapping 
 *  is moved during a remap.  If i use MAP_FIXED, then it may return an error
 *  instead of succeeding.  Since I already have a working implementation with
 *  list<BinaryData> for file updates, I'll just use list<BinaryDataMMAP>.
bool BinaryDataMMAP::remapMMAP(void)
{
   if(ptr_ == NULL || fileDescriptor_==-1 || size_==FILE_DOES_NOT_EXIST)
   {
      cout << "***ERROR:  attempting to remap a non-existent mmap" << endl;
      return false;
   }
   
   uint64_t newSize = getFilesize(filename_);
   if( newSize==FILE_DOES_NOT_EXIST )
      return false;

   int successCode = mremap(ptr_, size_, newSize, MAP_SHARED);
   if(successCode == MAP_FAILED)
   {
      close(fileDescriptor_);
      cout << "***ERROR: file exists, but remapping failed" << endl;
      return false;
   }
   size_ = newSize;
   return true;
}
*/


////////////////////////////////////////////////////////////////////////////////
void BinaryDataMMAP::deleteMMAP(void)
{
   if(ptr_ != NULL)
   {
      UnmapViewOfFile((LPVOID*)ptr_);
      CloseHandle(hFileMapping_);
   }

   filename_ = string("");
   size_ = FILE_DOES_NOT_EXIST;
}





/* 
This code was placed in the public domain by the author, 
Sean Barrett, in November 2007. Do with it as you will. 
(Seee the page for stb_vorbis or the mollyrocket source 
page for a longer description of the public domain non-license). 
#define WIN32_LEAN_AND_MEAN 
#include <windows.h> 

typedef struct 
{ 
   HANDLE f; 
   HANDLE m; 
   void *p; 
} SIMPLE_UNMMAP; 

// For madvise, can use FILE_FLAG_RANDOM_ACCESS or FILE_FLAG_SEQUENTIAL_SCAN
// in the call to CreateFile

// map 'filename' and return a pointer to it. fill out *length and *un if not-NULL 
void *simple_mmap(const char *filename, int *length, SIMPLE_UNMMAP *un) 
{ 
   HANDLE f = CreateFile(filename, GENERIC_READ, FILE_SHARE_READ,  NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL); 
   HANDLE m; 
   void *p; 
   if (!f) return NULL; 
   m = CreateFileMapping(f, NULL, PAGE_READONLY, 0,0, NULL); 
   if (!m) { CloseHandle(f); return NULL; } 
   p = MapViewOfFile(m, FILE_MAP_READ, 0,0,0); 
   if (!p) { CloseHandle(m); CloseHandle(f); return NULL; } 
   if (n) *n = GetFileSize(f, NULL); 
   if (un) { 
      un->f = f; 
      un->m = m; 
      un->p = p; 
   } 
   return p; 
} 

void simple_unmmap(SIMPLE_UNMMAP *un) 
{ 
   UnmapViewOfFile(un->p); 
   CloseHandle(un->m); 
   CloseHandle(un->f); 
} 
*/ 


