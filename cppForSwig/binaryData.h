#ifndef _binaryData_H_
#define _binaryData_H_

#include <stdio.h>
#include <cstdint>
#include <iostream>
#include <vector>
#include <string>
#include <assert.h>


using namespace std;

class binaryData
{
public:


   binaryData(void) : data_(0), nBytes_(0)     {                         }
   binaryData(size_t sz)                       { alloc(sz);              }
   binaryData(uint8_t* inData, size_t sz)      { copyFrom(inData, sz);   }
   binaryData(uint8_t* dstart, uint8_t* dend ) { copyFrom(dstart, dend); }
   binaryData(string str)                      { copyFrom(str);          }
   binaryData(binaryData const & bd)           { copyFrom(bd);           }

   uint8_t * getPtr(void)                   { return &(data_[0]); }
   size_t getSize(void) const               { return nBytes_; }
   uint8_t const * getConstPtr(void) const  { return &(data_[0]); }

   // We allocate space as necesssary
   void copyFrom(uint8_t const * inData) { memcpy( &(data_[0]), inData, (size_t)nBytes_); }
   void copyFrom(uint8_t const * inData, size_t sz) { alloc(sz); memcpy( &(data_[0]), inData, nBytes_); }
   void copyFrom(uint8_t const * start, uint8_t const * end) { copyFrom( start, (end-start)); }
   void copyFrom(string const & str) { copyFrom( (uint8_t*)str.c_str(), str.size()); } 
   void copyFrom(binaryData const & bd) { copyFrom( bd.getConstPtr(), bd.getSize() ); }

   // UNSAFE -- you don't know if outData holds enough space for this
   void copyTo(uint8_t* outData) const { memcpy( outData, &(data_[0]), (size_t)nBytes_); }
   void copyTo(uint8_t* outData, size_t sz) const { memcpy( outData, &(data_[0]), (size_t)sz); }
   void copyTo(uint8_t* outData, size_t offset, size_t sz) const { memcpy( outData, &(data_[offset]), (size_t)sz); }

   uint8_t & operator[](size_t i)       { return data_[i]; }
   uint8_t   operator[](size_t i) const { return data_[i]; } 

   bool operator<(binaryData const & bd2) const
   {
      return (toString().compare(bd2.toString()) < 0);
   }
   bool operator==(binaryData const & bd2) const
   {
      return (toString().compare(bd2.toString()) == 0);
   }

   bool operator>(binaryData const & bd2) const
   {
      return (toString().compare(bd2.toString()) > 0);
   }

   // These are always memory-safe
   void copyTo(string & str) { str.assign( (char const *)(&(data_[0])), nBytes_); }
   string toString(void) const { return string((char const *)(&(data_[0])), nBytes_); }

   void resize(size_t sz) { data_.resize(sz); nBytes_ = sz;}

   // Swap endianness of the bytes in the index range [pos1, pos2)
   void swapEndianness(size_t pos1=0, size_t pos2=0)
   {
      if(pos2 <= pos1)
         pos2 = nBytes_;

      size_t totalBytes = pos2-pos1;
      for(size_t i=0; i<(totalBytes/2); i++)
      {
         uint8_t d1    = data_[pos1+i];
         data_[pos1+i] = data_[pos2-i];
         data_[pos2-i] = d1;
      }
   }

   string toHex(void)
   {
      static char hexLookupTable[16] = {'0','1','2','3',
                                        '4','5','6','7',
                                        '8','9','a','b',
                                        'c','d','e','f' };
      vector<int8_t> outStr(2*nBytes_);
      for( size_t i=0; i<nBytes_; i++)
      {
         uint8_t nextByte = data_[i];
         outStr[2*i  ] = hexLookupTable[ (nextByte >> 4) & 0x0F ];
         outStr[2*i+1] = hexLookupTable[ (nextByte     ) & 0x0F ];
      }
      return string((char const *)(&(outStr[0])), 2*nBytes_);
   }

   void createFromHex(string const & str)
   {
      static uint8_t binLookupTable[256] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

      assert(str.size()%2 == 0);
      size_t newLen = str.size() / 2;
      alloc(newLen);

      for( size_t i=0; i<newLen; i++)
      {
         uint8_t char1 = binLookupTable[ str[2*i  ] ];
         uint8_t char2 = binLookupTable[ str[2*i+1] ];
         data_[i] = (char1 << 4) | char2;
      }
   }

private:
   vector<uint8_t> data_;
   size_t nBytes_;


private:
   void alloc(size_t sz)
   {
      if(nBytes_ != sz)
      {
         data_ = vector<uint8_t>(sz);
         nBytes_ = sz;
      }
   }

};


#endif
