////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_FCGI_MESSAGE_
#define _H_FCGI_MESSAGE_

#include <stdint.h>
#include <vector>
#include <string>
#include <sstream>
#include "./fcgi/include/fastcgi.h"

using namespace std;

struct FcgiData
{
   vector<uint8_t> data_;

   void clear(void)
   {
      data_.clear();
   }

   inline size_t size(void) const
   {
      return data_.size();
   }
};

class FcgiPacket
{
   friend class FcgiMessage;

private:
   FcgiData header_;
   vector<FcgiData> data_;

public:
   void buildHeader(uint8_t header_type, uint16_t requestID_);
   void addParam(const string& name, const string& val);
   void addData(const char*, size_t);
};

class FcgiMessage
{
private:
   vector<FcgiPacket> packets_;
   FcgiData serData_;

   int requestID_ = -1;

public:
   static FcgiMessage makePacket(const char* msg);

   uint8_t* serialize(void);
   size_t getSerializedDataLength(void) const { return serData_.size(); }
   
   void clear(void);

   FcgiPacket& getNewPacket(void);
   uint16_t beginRequest(void);
   void endRequest(void) {}
   int id(void) const { return requestID_; }
};

#endif
