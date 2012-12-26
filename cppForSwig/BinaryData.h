////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _BINARYDATA_H_
#define _BINARYDATA_H_

#include <stdio.h>
#if defined(_MSC_VER) || defined(__MINGW32__)
   //#include <cstdint>
   typedef          __int8  int8_t;
   typedef          __int16 int16_t;
   typedef          __int32 int32_t;
   typedef          __int64 int64_t;
   typedef unsigned __int8  uint8_t;
   typedef unsigned __int16 uint16_t;
   typedef unsigned __int32 uint32_t;
   typedef unsigned __int64 uint64_t;
   #define INT8_MIN     ((int8_t)_I8_MIN)
   #define INT8_MAX     _I8_MAX
   #define INT16_MIN    ((int16_t)_I16_MIN)
   #define INT16_MAX    _I16_MAX
   #define INT32_MIN    ((int32_t)_I32_MIN)
   #define INT32_MAX    _I32_MAX
   #define INT64_MIN    ((int64_t)_I64_MIN)
   #define INT64_MAX    _I64_MAX
   #define UINT8_MAX    _UI8_MAX
   #define UINT16_MAX   _UI16_MAX
   #define UINT32_MAX   _UI32_MAX
   #define UINT64_MAX   _UI64_MAX

#else
   #include <stdlib.h>
   #include <inttypes.h>   
   #include <cstring>
   #include <stdint.h>

   #ifndef PAGESIZE
      #include <unistd.h>
      #define PAGESIZE sysconf(_SC_PAGESIZE)
   #endif

   #ifndef PAGEFLOOR
      // "Round" a ptr down to the beginning of the memory page containing it
      // PAGERANGE gives us a size to lock/map as a multiple of the PAGESIZE
      #define PAGEFLOOR(ptr,sz) ((void*)(((size_t)(ptr)) & (~(PAGESIZE-1))  ))
      #define PAGERANGE(ptr,sz) (  (((size_t)(ptr)+(sz)-1) | (PAGESIZE-1)) + 1 - PAGEFLOOR(ptr,sz)  )
   #endif
   

#endif

#include <iostream>
#include <vector>
#include <string>
#include <assert.h>

// We can remove these includes (Crypto++ ) if we remove the GenerateRandom()
#include "cryptlib.h"
#include "osrng.h"

#define DEFAULT_BUFFER_SIZE 64*1048576

#include "UniversalTimer.h"


using namespace std;

class BinaryDataRef;

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BinaryData
{
public:


   /////////////////////////////////////////////////////////////////////////////
   BinaryData(void) : data_(0)                 {                         }
   BinaryData(size_t sz)                       { alloc(sz);              }
   BinaryData(uint8_t const * inData, size_t sz)      
                                               { copyFrom(inData, sz);   }
   BinaryData(uint8_t const * dstart, uint8_t const * dend ) 
                                               { copyFrom(dstart, dend); }
   BinaryData(string const & str)              { copyFrom(str);          }
   BinaryData(BinaryData const & bd)           { copyFrom(bd);           }

   BinaryData(BinaryDataRef const & bdRef);
   size_t getSize(void) const               { return data_.size(); }

   /////////////////////////////////////////////////////////////////////////////
   uint8_t const * getPtr(void) const       
   { 
      if(getSize()==0)
         return NULL;
      else
         return &(data_[0]); 
   }

   /////////////////////////////////////////////////////////////////////////////
   uint8_t* getPtr(void)                   
   { 
      if(getSize()==0)
         return NULL;
      else
         return &(data_[0]); 
   }  

   BinaryDataRef getRef(void) const;
   //uint8_t const * getConstPtr(void) const  { return &(data_[0]); }
   
   /////////////////////////////////////////////////////////////////////////////
   // We allocate space as necesssary
   // TODO:  Got a problem when copying an empty/uninitialized BD object...
   void copyFrom(uint8_t const * start, uint8_t const * end) 
                  { copyFrom( start, (end-start)); }  // [start, end)
   void copyFrom(string const & str)                         
                  { copyFrom( (uint8_t*)str.c_str(), str.size()); } 
   void copyFrom(BinaryData const & bd)                      
                  { copyFrom( bd.getPtr(), bd.getSize() ); }
   void copyFrom(BinaryDataRef const & bdr);
   void copyFrom(uint8_t const * inData, size_t sz)          
   { 
      if(inData==NULL || sz == 0)
         alloc(0);
      else
      {
         alloc(sz); 
         memcpy( &(data_[0]), inData, sz);
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   // UNSAFE -- you don't know if outData holds enough space for this
   void copyTo(uint8_t* outData) const { memcpy( outData, &(data_[0]), getSize()); }
   void copyTo(uint8_t* outData, size_t sz) const { memcpy( outData, &(data_[0]), (size_t)sz); }
   void copyTo(uint8_t* outData, size_t offset, size_t sz) const { memcpy( outData, &(data_[offset]), (size_t)sz); }

   void fill(uint8_t ch) { if(getSize()>0) memset(getPtr(), ch, getSize()); }
               
   uint8_t & operator[](size_t i)       { return data_[i]; }
   uint8_t   operator[](size_t i) const { return data_[i]; } 

   /////////////////////////////////////////////////////////////////////////////
   BinaryData operator+(BinaryData const & bd2) const
   {
      BinaryData out(getSize() + bd2.getSize());
      memcpy(out.getPtr(), getPtr(), getSize());
      memcpy(out.getPtr()+getSize(), bd2.getPtr(), bd2.getSize());
      return out;
   }

   /////////////////////////////////////////////////////////////////////////////
   // This is about as efficient as we're going to get...
   BinaryData & append(BinaryData const & bd2)
   {
      if(bd2.getSize()==0) 
         return (*this);
   
      if(getSize()==0) 
         copyFrom(bd2.getPtr(), bd2.getSize());
      else
         data_.insert(data_.end(), bd2.data_.begin(), bd2.data_.end());
      return (*this);
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData & append(BinaryDataRef const & bd2);

   /////////////////////////////////////////////////////////////////////////////
   BinaryData & append(uint8_t const * str, uint32_t sz);

   /////////////////////////////////////////////////////////////////////////////
   BinaryData & append(uint8_t byte)
   {
      data_.insert(data_.end(), byte);
      return (*this);
   }


   /////////////////////////////////////////////////////////////////////////////
   int32_t find(BinaryDataRef const & matchStr, uint32_t startPos=0);
   /////////////////////////////////////////////////////////////////////////////
   int32_t find(BinaryData const & matchStr, uint32_t startPos=0);

   /////////////////////////////////////////////////////////////////////////////
   bool contains(BinaryDataRef const & matchStr, uint32_t startPos=0);
   /////////////////////////////////////////////////////////////////////////////
   bool contains(BinaryData const & matchStr, uint32_t startPos=0);


   /////////////////////////////////////////////////////////////////////////////
   bool startsWith(BinaryDataRef const & matchStr) const;
   /////////////////////////////////////////////////////////////////////////////
   bool startsWith(BinaryData const & matchStr) const;

   /////////////////////////////////////////////////////////////////////////////
   bool endsWith(BinaryDataRef const & matchStr) const;
   /////////////////////////////////////////////////////////////////////////////
   bool endsWith(BinaryData const & matchStr) const;

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef getSliceRef(int32_t start_pos, uint32_t nChar) const;
   /////////////////////////////////////////////////////////////////////////////
   BinaryData    getSliceCopy(int32_t start_pos, uint32_t nChar) const;

   /////////////////////////////////////////////////////////////////////////////
   bool operator<(BinaryData const & bd2) const
   {
      int minLen = min(getSize(), bd2.getSize());
      for(int i=0; i<minLen; i++)
      {
         if( data_[i] == bd2.data_[i] )
            continue;
         return data_[i] < bd2.data_[i];
      }
      return (getSize() < bd2.getSize());
   }

   /////////////////////////////////////////////////////////////////////////////
   bool operator==(BinaryData const & bd2) const
   {
      if(getSize() != bd2.getSize())
         return false;
      for(unsigned int i=0; i<getSize(); i++)
         if( data_[i] != bd2.data_[i] )
            return false;
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   bool operator!=(BinaryData const & bd2) const { return (!((*this)==bd2)); }

   /////////////////////////////////////////////////////////////////////////////
   bool operator==(BinaryDataRef const & bd2) const;

   /////////////////////////////////////////////////////////////////////////////
   bool operator!=(BinaryDataRef const & bd2) const { return (!((*this)==bd2)); }

   /////////////////////////////////////////////////////////////////////////////
   bool operator>(BinaryData const & bd2) const
   {
      int minLen = min(getSize(), bd2.getSize());
      for(int i=0; i<minLen; i++)
      {
         if( data_[i] == bd2.data_[i] )
            continue;
         return data_[i] > bd2.data_[i];
      }
      return (getSize() > bd2.getSize());
   }

   /////////////////////////////////////////////////////////////////////////////
   // These are always memory-safe
   void copyTo(string & str) { str.assign( (char const *)(&(data_[0])), getSize()); }

   /////////////////////////////////////////////////////////////////////////////
   string toBinStr(void) const 
   { 
      if(getSize()==0)
         return string("");

      return string((char const *)(&(data_[0])), getSize());
   }

   char* toCharPtr(void) const  { return  (char*)(&(data_[0])); }
   unsigned char* toUCharPtr(void) const { return (unsigned char*)(&(data_[0])); }

   void resize(size_t sz) { data_.resize(sz); }
   void reserve(size_t sz) { data_.reserve(sz); }

   /////////////////////////////////////////////////////////////////////////////
   // Swap endianness of the bytes in the index range [pos1, pos2)
   BinaryData& swapEndian(size_t pos1=0, size_t pos2=0)
   {
      if(getSize()==0)
         return (*this);

      if(pos2 <= pos1)
         pos2 = getSize();

      size_t totalBytes = pos2-pos1;
      for(size_t i=0; i<(totalBytes/2); i++)
      {
         uint8_t d1    = data_[pos1+i];
         data_[pos1+i] = data_[pos2-(i+1)];
         data_[pos2-(i+1)] = d1;
      }
      return (*this);
   }

   /////////////////////////////////////////////////////////////////////////////
   // Swap endianness of the bytes in the index range [pos1, pos2)
   BinaryData copySwapEndian(size_t pos1=0, size_t pos2=0) const
   {
      BinaryData bdout(*this);
      bdout.swapEndian(pos1, pos2);
      return bdout;
   }

   /////////////////////////////////////////////////////////////////////////////
   string toHexStr(bool bigEndian=false) const
   {
      if(getSize()==0)
         return string("");

      static char hexLookupTable[16] = {'0','1','2','3',
                                        '4','5','6','7',
                                        '8','9','a','b',
                                        'c','d','e','f' };
      BinaryData bdToHex(*this);
      if(bigEndian)
         bdToHex.swapEndian();

      vector<int8_t> outStr(2*getSize());
      for( size_t i=0; i<getSize(); i++)
      {
         uint8_t nextByte = bdToHex.data_[i];
         outStr[2*i  ] = hexLookupTable[ (nextByte >> 4) & 0x0F ];
         outStr[2*i+1] = hexLookupTable[ (nextByte     ) & 0x0F ];
      }
         
      return string((char const *)(&(outStr[0])), 2*getSize());
   }

   static BinaryData CreateFromHex(string const & str)
   {
      BinaryData out;
      out.createFromHex(str);
      return out;
   }

   /////////////////////////////////////////////////////////////////////////////
   void createFromHex(string const & str)
   {
      static uint8_t binLookupTable[256] = { 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x0a, 0x0b, 0x0c, 0x0d, 
         0x0e, 0x0f, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0             };

      assert(str.size()%2 == 0);
      int newLen = str.size() / 2;
      alloc(newLen);

      for(int i=0; i<newLen; i++)
      {
         uint8_t char1 = binLookupTable[ (uint8_t)str[2*i  ] ];
         uint8_t char2 = binLookupTable[ (uint8_t)str[2*i+1] ];
         data_[i] = (char1 << 4) | char2;
      }
   }


   // Can remove this method if we don't have crypto++ linked
   static BinaryData GenerateRandom(size_t numBytes)
   {
      static CryptoPP::AutoSeededRandomPool prng;
      BinaryData randData(numBytes);
      prng.GenerateBlock(randData.getPtr(), numBytes);
      return randData;
   }


   // Absorb a binary file's data into a new BinaryData object
   int32_t readBinaryFile(string filename)
   {
      ifstream is(filename.c_str(), ios::in | ios::binary );
      if( !is.is_open() )
         return -1;

      is.seekg(0, ios::end);
      uint32_t filesize = (size_t)is.tellg();
      is.seekg(0, ios::beg);
      
      data_.resize(getSize());
      is.read((char*)getPtr(), getSize());
      return getSize();
   }

   // For deallocating all the memory that is currently used by this BD
   void clear(void) { data_.clear(); }

private:
   vector<uint8_t> data_;

private:
   void alloc(size_t sz) 
   { 
      if(sz != getSize())
      {
         data_.clear();
         data_.resize(sz);
      }

   }

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BinaryDataRef
{
public:
   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef(void) : ptr_(NULL), nBytes_(0)     
   {
      // Nothing to put here
   }
   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef(uint8_t const * inData, size_t sz) 
   { 
      setRef(inData, sz); 
   }
   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef(uint8_t const * dstart, uint8_t const * dend )
   { 
      setRef(dstart,dend); 
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef(BinaryDataRef const & bdr)
   { 
      ptr_ = bdr.ptr_;
      nBytes_ = bdr.nBytes_;
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef(BinaryData const & bd)
   { 
      if(bd.getSize()!=0) 
      {
         ptr_ = bd.getPtr();
         nBytes_ = bd.getSize();
      }
      else
      {
         ptr_= NULL;
         nBytes_ = 0;
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   uint8_t const * getPtr(void) const       { return ptr_;    }
   size_t getSize(void) const               { return nBytes_; }

   /////////////////////////////////////////////////////////////////////////////
   void setRef(uint8_t const * inData, size_t sz)          
   { 
      ptr_ = inData; 
      nBytes_ = sz;
   }
   void setRef(uint8_t const * start, uint8_t const * end) 
                  { setRef( start, (end-start)); }  // [start, end)
   void setRef(string const & str)                         
                  { setRef( (uint8_t*)str.c_str(), str.size()); } 
   void setRef(BinaryData const & bd)                      
                  { setRef( bd.getPtr(), bd.getSize() ); }

   /////////////////////////////////////////////////////////////////////////////
   // UNSAFE -- you don't know if outData holds enough space for this
   void copyTo(uint8_t* outData) const { memcpy( outData, ptr_, (size_t)nBytes_); }
   void copyTo(uint8_t* outData, size_t sz) const { memcpy( outData, ptr_, (size_t)sz); }
   void copyTo(uint8_t* outData, size_t offset, size_t sz) const { memcpy( outData, ptr_+offset, (size_t)sz); }
   void copyTo(BinaryData & bd) const 
   {
      bd.resize(nBytes_);
      memcpy( bd.getPtr(), ptr_, (size_t)nBytes_);
   }

   BinaryData copy(void) const 
   {
      BinaryData outData(nBytes_);
      copyTo(outData);
      return outData;
   }

   /////////////////////////////////////////////////////////////////////////////
   // These are always memory-safe
   void copyTo(string & str) { str.assign( (char const *)(ptr_), nBytes_); }
   string toBinStr(void) const 
   { 
      if(getSize()==0)
         return string("");
      return string((char const *)(ptr_), nBytes_); 
   }
   char* toCharPtr(void) const  { return  (char*)(ptr_); }
   unsigned char* toUCharPtr(void) const { return (unsigned char*)(ptr_); }

   uint8_t const & operator[](size_t i) const      { return ptr_[i]; }
   //uint8_t   operator[](size_t i) const { return ptr_[i]; } 
   bool isValid(void) const { return ptr_ != NULL; }

   /////////////////////////////////////////////////////////////////////////////
   int32_t find(BinaryDataRef const & matchStr, uint32_t startPos=0)
   {
      int32_t finalAnswer = -1;
      for(int32_t i=startPos; i<=(int32_t)nBytes_-(int32_t)matchStr.nBytes_; i++)
      {
         if(matchStr.ptr_[0] != ptr_[i])
            continue;

         for(uint32_t j=0; j<matchStr.nBytes_; j++)
         {
            if(matchStr.ptr_[j] != ptr_[i+j])
               break;

            // If we are at this instruction and is the last index, it's a match
            if(j==matchStr.nBytes_-1)
               finalAnswer = i;
         }

         if(finalAnswer != -1)
            break;
      }

      return finalAnswer;
   }

   /////////////////////////////////////////////////////////////////////////////
   int32_t find(BinaryData const & matchStr, uint32_t startPos=0)
   {
      BinaryDataRef bdr(matchStr);
      return find(bdr, startPos);
   }

   /////////////////////////////////////////////////////////////////////////////
   bool contains(BinaryDataRef const & matchStr, uint32_t startPos=0)
   {
      return (find(matchStr, startPos) != -1);
   }

   /////////////////////////////////////////////////////////////////////////////
   bool contains(BinaryData const & matchStr, uint32_t startPos=0)
   {
      BinaryDataRef bdr(matchStr);
      return (find(bdr, startPos) != -1);
   }


   /////////////////////////////////////////////////////////////////////////////
   bool startsWith(BinaryDataRef const & matchStr) const
   {
      if(matchStr.getSize() > nBytes_)
         return false;
   
      for(uint32_t i=0; i<matchStr.getSize(); i++)
         if(matchStr[i] != (*this)[i])
            return false;
   
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   bool startsWith(BinaryData const & matchStr) const
   {
      if(matchStr.getSize() > nBytes_)
         return false;
   
      for(uint32_t i=0; i<matchStr.getSize(); i++)
         if(matchStr[i] != (*this)[i])
            return false;
   
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   bool endsWith(BinaryDataRef const & matchStr) const
   {
      uint32_t sz = matchStr.getSize();
      if(sz > nBytes_)
         return false;
   
      for(uint32_t i=0; i<sz; i++)
         if(matchStr[sz-(i+1)] != (*this)[nBytes_-(i+1)])
            return false;
   
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   bool endsWith(BinaryData const & matchStr) const
   {
      uint32_t sz = matchStr.getSize();
      if(sz > nBytes_)
         return false;
   
      for(uint32_t i=0; i<sz; i++)
         if(matchStr[sz-(i+1)] != (*this)[nBytes_-(i+1)])
            return false;
   
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef getSliceRef(int32_t start_pos, uint32_t nChar) const
   {
      if(start_pos < 0) 
         start_pos = nBytes_ + start_pos;

      if(start_pos + nChar > nBytes_)
      {
         cerr << "getSliceRef: Invalid BinaryData access" << endl;
         return BinaryDataRef();
      }
      return BinaryDataRef( getPtr()+start_pos, nChar);
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData getSliceCopy(int32_t start_pos, uint32_t nChar) const
   {
      if(start_pos < 0) 
         start_pos = nBytes_ + start_pos;

      if(start_pos + nChar > nBytes_)
      {
         cerr << "getSliceRef: Invalid BinaryData access" << endl;
         return BinaryDataRef();
      }
      return BinaryData( getPtr()+start_pos, nChar);
   }

   /////////////////////////////////////////////////////////////////////////////
   bool isSameRefAs(BinaryDataRef const & bdRef2)
   {
      return (ptr_ == bdRef2.ptr_ && nBytes_ == bdRef2.nBytes_);
   }

   /////////////////////////////////////////////////////////////////////////////
   bool operator<(BinaryDataRef const & bd2) const
   {
      int minLen = min(nBytes_, bd2.nBytes_);
      for(int i=0; i<minLen; i++)
      {
         if( ptr_[i] == bd2.ptr_[i] )
            continue;
         return ptr_[i] < bd2.ptr_[i];
      }
      return (nBytes_ < bd2.nBytes_);
   }

   /////////////////////////////////////////////////////////////////////////////
   bool operator==(BinaryDataRef const & bd2) const
   {
      if(nBytes_ != bd2.nBytes_)
         return false;
      else if(ptr_ == bd2.ptr_)
         return true;
      
      for(unsigned int i=0; i<nBytes_; i++)
         if( ptr_[i] != bd2.ptr_[i] )
            return false;
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   bool operator==(BinaryData const & bd2) const
   {
      if(nBytes_ != bd2.getSize())
         return false;
      else if(ptr_ == bd2.getPtr())
         return true;

      for(unsigned int i=0; i<nBytes_; i++)
         if( ptr_[i] != bd2[i])
            return false;
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   bool operator>(BinaryDataRef const & bd2) const
   {
      int minLen = min(nBytes_, bd2.nBytes_);
      for(int i=0; i<minLen; i++)
      {
         if( ptr_[i] == bd2.ptr_[i] )
            continue;
         return ptr_[i] > bd2.ptr_[i];
      }
      return (nBytes_ > bd2.nBytes_);
   }


   /////////////////////////////////////////////////////////////////////////////
   string toHexStr(bool bigEndian=false) const
   {
      if(getSize() == 0)
         return string("");

      static char hexLookupTable[16] = {'0','1','2','3',
                                        '4','5','6','7',
                                        '8','9','a','b',
                                        'c','d','e','f' };
      BinaryData bdToHex(*this);
      if(bigEndian)
         bdToHex.swapEndian();

      vector<int8_t> outStr(2*nBytes_);
      for(size_t i=0; i<nBytes_; i++)
      {
         uint8_t nextByte = *(bdToHex.getPtr()+i);
         outStr[2*i  ] = hexLookupTable[ (nextByte >> 4) & 0x0F ];
         outStr[2*i+1] = hexLookupTable[ (nextByte     ) & 0x0F ];
      }
      return string((char const *)(&(outStr[0])), 2*nBytes_);
   }



/*
#ifdef USE_CRYPTOPP

   static void getHash256(uint8_t const * strToHash,
                          uint32_t        nBytes,
                          BinaryData    & hashOutput)
   {
      static CryptoPP::SHA256 sha256_;
      if(hashOutput.getSize() != 32)
         hashOutput.resize(32);

      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash, nBytes);
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
   }

   static void getHash256(BinaryDataRef const & strToHash, 
                          BinaryData          & hashOutput)
   {
      static CryptoPP::SHA256 sha256_;
      if(hashOutput.getSize() != 32)
         hashOutput.resize(32);

      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);

   }

   static BinaryData getHash256(BinaryDataRef const & strToHash)
   {
      static CryptoPP::SHA256 sha256_;
      
      BinaryData hashOutput(32);
      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
      return hashOutput;
   }

   BinaryData getHash256(void)
   {
      static CryptoPP::SHA256 sha256_;
      BinaryData hashOutput(32);
      sha256_.CalculateDigest(hashOutput.getPtr(), ptr_,                 nBytes_);
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
      return hashOutput;
   }

#endif
*/

private:
   uint8_t const * ptr_;
   uint32_t nBytes_;

private:

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BinaryReader
{
public:
   /////////////////////////////////////////////////////////////////////////////
   BinaryReader(int sz=0) :
      bdStr_(sz),
      pos_(0)
   {
      // Nothing needed here
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryReader(BinaryData const & toRead) :
      bdStr_(toRead),
      pos_(0)
   {
      // Nothing needed here
   }

   /////////////////////////////////////////////////////////////////////////////
   void advance(uint32_t nBytes) 
   { 
      pos_ += nBytes;  
      pos_ = min(pos_, getSize());
   }

   /////////////////////////////////////////////////////////////////////////////
   void rewind(uint32_t nBytes) 
   { 
      pos_ -= nBytes;  
      pos_ = max(pos_, (uint32_t)0);
   }

   /////////////////////////////////////////////////////////////////////////////
   void resize(uint32_t nBytes)
   {
      bdStr_.resize(nBytes);
      pos_ = min(nBytes, pos_);
   }

   /////////////////////////////////////////////////////////////////////////////
   uint64_t get_var_int(uint8_t* nRead=NULL);


   /////////////////////////////////////////////////////////////////////////////
   uint8_t get_uint8_t(void)
   {
      uint8_t outVal = bdStr_[pos_];
      pos_ += 1;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   uint16_t get_uint16_t(void)
   {
      uint16_t outVal = *(uint16_t*)(bdStr_.getPtr() + pos_);
      pos_ += 2;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t get_uint32_t(void)
   {
      uint32_t outVal = *(uint32_t*)(bdStr_.getPtr() + pos_);
      pos_ += 4;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   uint64_t get_uint64_t(void)
   {
      uint64_t outVal = *(uint64_t*)(bdStr_.getPtr() + pos_);
      pos_ += 8;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   void get_BinaryData(BinaryData & bdTarget, uint32_t nBytes)
   {
      bdTarget.copyFrom( bdStr_.getPtr() + pos_, nBytes);
      pos_ += nBytes;
   }

   /////////////////////////////////////////////////////////////////////////////
   void get_BinaryData(uint8_t* targPtr, uint32_t nBytes)
   {
      bdStr_.copyTo(targPtr, pos_, nBytes);
      pos_ += nBytes;
   }


   /////////////////////////////////////////////////////////////////////////////
   // Take the remaining buffer and shift it to the front
   // then return a pointer to where the old data ends
   //
   //                                      
   //  Before:                             pos
   //                                       |
   //                                       V
   //             [ a b c d e f g h i j k l m n o p q r s t]
   //
   //  After:      pos           return*
   //               |               |
   //               V               V
   //             [ m n o p q r s t - - - - - - - - - - - -]
   //                                 
   //
   pair<uint8_t*, int> rotateRemaining(void)
   {
      uint32_t nRemain = getSizeRemaining();
      //if(pos_ > nRemain+1)
         //memcpy(bdStr_.getPtr(), bdStr_.getPtr() + pos_, nRemain);
      //else
         memmove(bdStr_.getPtr(), bdStr_.getPtr() + pos_, nRemain);

      pos_ = 0;

      return make_pair(bdStr_.getPtr() + nRemain, getSize() - nRemain);
   }

   /////////////////////////////////////////////////////////////////////////////
   void     resetPosition(void)           { pos_ = 0; }
   uint32_t getPosition(void) const       { return pos_; }
   uint32_t getSize(void) const           { return bdStr_.getSize(); }
   uint32_t getSizeRemaining(void) const  { return getSize() - pos_; }
   bool     isEndOfStream(void) const     { return pos_ >= getSize(); }
   uint8_t* exposeDataPtr(void)           { return bdStr_.getPtr(); }
   uint8_t const * getCurrPtr(void)       { return bdStr_.getPtr() + pos_; }

private:
   BinaryData bdStr_;
   uint32_t pos_;

};


class BinaryRefReader
{
public:
   /////////////////////////////////////////////////////////////////////////////
   BinaryRefReader(int sz=0) :
      bdRef_(),
      totalSize_(sz),
      pos_(0)
   {
      // Nothing needed here
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryRefReader(BinaryData const & toRead) :
      bdRef_(toRead),
      totalSize_(toRead.getSize()),
      pos_(0)
   {
      // Nothing needed here
   }

   BinaryRefReader(BinaryDataRef const & toRead) :
      bdRef_(toRead),
      totalSize_(toRead.getSize()),
      pos_(0)
   {
      // Nothing needed here
   }

   // Default to INF size -- leave it to the user to guarantee that he's
   // not reading past the end of rawPtr
   BinaryRefReader(uint8_t const * rawPtr, uint32_t nBytes=UINT32_MAX) : 
      bdRef_(rawPtr, nBytes),
      totalSize_(nBytes),
      pos_(0)
   {
      // Nothing needed here
   }

   /////////////////////////////////////////////////////////////////////////////
   void advance(uint32_t nBytes) 
   { 
      pos_ += nBytes;  
      pos_ = min(pos_, totalSize_);
   }

   /////////////////////////////////////////////////////////////////////////////
   void rewind(uint32_t nBytes) 
   { 
      pos_ -= nBytes;  
      pos_ = max(pos_, (uint32_t)0);
   }


   /////////////////////////////////////////////////////////////////////////////
   uint64_t get_var_int(uint8_t* nRead=NULL);


   /////////////////////////////////////////////////////////////////////////////
   uint8_t get_uint8_t(void)
   {
      uint8_t outVal = bdRef_[pos_];
      pos_ += 1;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   uint16_t get_uint16_t(void)
   {
      uint16_t outVal = *(uint16_t*)(bdRef_.getPtr() + pos_);
      pos_ += 2;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t get_uint32_t(void)
   {
      uint32_t outVal = *(uint32_t*)(bdRef_.getPtr() + pos_);
      pos_ += 4;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   uint64_t get_uint64_t(void)
   {
      uint64_t outVal = *(uint64_t*)(bdRef_.getPtr() + pos_);
      pos_ += 8;
      return outVal;
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef get_BinaryDataRef(uint32_t nBytes)
   {
      BinaryDataRef bdrefout(bdRef_.getPtr() + pos_, nBytes);
      pos_ += nBytes;
      return bdrefout;
   }

   /////////////////////////////////////////////////////////////////////////////
   void get_BinaryData(BinaryData & bdTarget, uint32_t nBytes)
   {
      bdTarget.copyFrom( bdRef_.getPtr() + pos_, nBytes);
      pos_ += nBytes;
   }

   /////////////////////////////////////////////////////////////////////////////
   void get_BinaryData(uint8_t* targPtr, uint32_t nBytes)
   {
      bdRef_.copyTo(targPtr, pos_, nBytes);
      pos_ += nBytes;
   }


   /////////////////////////////////////////////////////////////////////////////
   void     resetPosition(void)           { pos_ = 0; }
   uint32_t getPosition(void) const       { return pos_; }
   uint32_t getSize(void) const           { return totalSize_; }
   uint32_t getSizeRemaining(void) const  { return totalSize_ - pos_; }
   bool     isEndOfStream(void) const     { return pos_ >= totalSize_; }
   uint8_t const * exposeDataPtr(void)    { return bdRef_.getPtr(); }
   uint8_t const * getCurrPtr(void)       { return bdRef_.getPtr() + pos_; }

private:
   BinaryDataRef bdRef_;
   uint32_t totalSize_;
   uint32_t pos_;

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BinaryWriter
{
public:
   /////////////////////////////////////////////////////////////////////////////
   // Using the argument to pre-allocate a certain amount of capacity.  Not 
   // required, but will improve performance if you can take a reasonable guess
   // about the final size of the output data
   BinaryWriter(uint32_t reserveSize=0) :
      theString_(0)
   {
      if(reserveSize != 0)
         theString_.reserve(reserveSize);
   }

   /////////////////////////////////////////////////////////////////////////////
   void reserve(size_t sz) { theString_.reserve(sz); }


   /////////////////////////////////////////////////////////////////////////////
   void put_uint8_t (uint8_t  val) { theString_.append( val ); }
   void put_uint16_t(uint16_t val) { theString_.append( (uint8_t*)(&val), 2); }
   void put_uint32_t(uint32_t val) { theString_.append( (uint8_t*)(&val), 4); }
   void put_uint64_t(uint64_t val) { theString_.append( (uint8_t*)(&val), 8); }

   //void put_int8_t  (  int8_t val) { theString_.append( val ); }
   //void put_int16_t ( int16_t val) { theString_.append( (uint8_t*)(&val), 2); }
   //void put_int32_t ( int32_t val) { theString_.append( (uint8_t*)(&val), 4); }
   //void put_int64_t ( int64_t val) { theString_.append( (uint8_t*)(&val), 8); }

   /////////////////////////////////////////////////////////////////////////////
   uint8_t put_var_int(uint64_t val)
   {

      if(val < 0xfd)
      {
         put_uint8_t((uint8_t)val);
         return 1;
      }
      else if(val <= UINT16_MAX)
      {
         put_uint8_t(0xfd);
         put_uint16_t((uint16_t)val);
         return 3;
      }
      else if(val <= UINT32_MAX)
      {
         put_uint8_t(0xfe);
         put_uint32_t((uint32_t)val);
         return 5;
      }
      else 
      {
         put_uint8_t(0xff);
         put_uint64_t(val);
         return 9;
      }
   }



   /////////////////////////////////////////////////////////////////////////////
   void put_BinaryData(BinaryData const & str, uint32_t offset=0, uint32_t sz=0)
   {
      if(offset==0)
      {
         if(sz==0)
            theString_.append(str);
         else
            theString_.append(str.getPtr(), sz);
      }
      else
      {
         if(sz==0)
            theString_.append(str.getPtr() + offset, str.getSize() - offset);
         else
            theString_.append(str.getPtr() + offset, sz);
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   void put_BinaryData(uint8_t* targPtr, uint32_t nBytes)
   {
      theString_.append(targPtr, nBytes);
   }


   /////////////////////////////////////////////////////////////////////////////
   BinaryData const & getData(void)
   {
      return theString_;
   }

private:
   BinaryData theString_;


};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BinaryStreamBuffer
{

public:

   /////////////////////////////////////////////////////////////////////////////
   BinaryStreamBuffer(string filename="", uint32_t bufSize=DEFAULT_BUFFER_SIZE) :
      binReader_(bufSize),
      streamPtr_(NULL),
      weOwnTheStream_(false),
      bufferSize_(bufSize),
      fileBytesRemaining_(0)
   {
      if( filename.size() > 0 )
      {
         streamPtr_ = new ifstream;
         weOwnTheStream_ = true;
         ifstream* ifstreamPtr = static_cast<ifstream*>(streamPtr_);
         ifstreamPtr->open(filename.c_str(), ios::in | ios::binary);
         if( !ifstreamPtr->is_open() )
         {
            cerr << "Could not open file for reading!  File: " << filename.c_str() << endl;
            cerr << "Aborting!" << endl;
            assert(false);
         }

         ifstreamPtr->seekg(0, ios::end);
         totalStreamSize_  = (uint32_t)ifstreamPtr->tellg();
         fileBytesRemaining_ = totalStreamSize_;
         ifstreamPtr->seekg(0, ios::beg);
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   void attachAsStreamBuffer(istream & is, 
                             uint32_t streamSize,
                             uint32_t bufSz=DEFAULT_BUFFER_SIZE)
   {
      if(streamPtr_ != NULL && weOwnTheStream_)
      {
         static_cast<ifstream*>(streamPtr_)->close();
         delete streamPtr_;
      }

      streamPtr_           = &is;
      fileBytesRemaining_  = streamSize;
      totalStreamSize_     = streamSize;
      bufferSize_          = bufSz;
      binReader_.resize(bufferSize_);
   }


   
   /////////////////////////////////////////////////////////////////////////////
   // Refills the buffer from the stream, returns true if there is more data 
   // left in the stream
   bool streamPull(void)
   {
      SCOPED_TIMER("StreamPull");

      uint32_t prevBufSizeRemain = binReader_.getSizeRemaining();
      if(fileBytesRemaining_ == 0)
         return false;

      if( binReader_.getPosition() <= 0)
      {
         // No data to shuffle, just pull from the stream buffer
         if(fileBytesRemaining_ > binReader_.getSize())
         {
            // Enough left in the stream to fill the entire buffer
            streamPtr_->read((char*)(binReader_.exposeDataPtr()), binReader_.getSize());
            fileBytesRemaining_ -= binReader_.getSize();
         }
         else
         {
            // The buffer is bigger than the remaining stream size
            streamPtr_->read((char*)(binReader_.exposeDataPtr()), fileBytesRemaining_);
            binReader_.resize(fileBytesRemaining_);
            fileBytesRemaining_ = 0;
         }
         
      }
      else
      {
         // The buffer needs to be refilled but has leftover data at the end
         pair<uint8_t*, int> leftover = binReader_.rotateRemaining();
         uint8_t* putNewDataPtr = leftover.first;
         uint32_t numBytes      = leftover.second;

         if(fileBytesRemaining_ > numBytes)
         {
            // Enough data left in the stream to fill the entire buffer
            streamPtr_->read((char*)putNewDataPtr, numBytes);
            fileBytesRemaining_ -= numBytes;
         }
         else
         {
            // The buffer is bigger than the remaining stream size
            streamPtr_->read((char*)putNewDataPtr, fileBytesRemaining_);
            binReader_.resize(fileBytesRemaining_+ prevBufSizeRemain); 
            fileBytesRemaining_ = 0;
         }
      }

      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryReader& reader(void)
   {
      return binReader_;
   }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t getFileByteLocation(void)
   {
      return totalStreamSize_ - (fileBytesRemaining_ + binReader_.getSizeRemaining());
   }


   uint32_t getBufferSizeRemaining(void) { return binReader_.getSizeRemaining(); }
   uint32_t getFileSizeRemaining(void)   { return fileBytesRemaining_; }
   uint32_t getBufferSize(void)          { return binReader_.getSize(); }

private:

   BinaryReader binReader_;
   istream* streamPtr_;
   bool     weOwnTheStream_;
   uint32_t bufferSize_;
   uint32_t totalStreamSize_;
   uint32_t fileBytesRemaining_;

};


#endif
