////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "FcgiMessage.h"
#include <cstring>
#include <stdexcept>
#include <algorithm>
#if defined(__APPLE__)
#include <cstdlib>
#endif

///////////////////////////////////////////////////////////////////////////////
//
// FcgiPacket
//
///////////////////////////////////////////////////////////////////////////////
void FcgiPacket::buildHeader(uint8_t header_type, uint16_t requestID_)
{
   header_.data_.resize(8);
   uint8_t* header = &header_.data_[0];

   header[0] = 1; //fcgi version
   header[1] = header_type;

   uint16_t requestID16 = (uint16_t)requestID_;
   header[2] = *((char*)(&requestID16) + 1); //requestId B1
   header[3] = *((char*)(&requestID16)); //requestId B0

   //content length in 16bits
   uint32_t contentLength = 0;
   for (auto& data : data_)
      contentLength += data.size();

   if (contentLength > UINT16_MAX)
      throw runtime_error("data is too large for fcgi packet");

   header[4] = *((uint8_t*)(&contentLength) + 1); //contentLength B1
   header[5] = *((uint8_t*)(&contentLength)); //contentLength B0

   header[6] = 0; //padding length B1
   header[7] = 0; //padding length B0
}

///////////////////////////////////////////////////////////////////////////////
void FcgiPacket::addParam(const string& name, const string& val)
{
   data_.push_back(FcgiData());
   FcgiData& data = data_.back();

   uint32_t namelength = name.size();
   uint32_t vallength = val.size();

   data.data_.reserve(namelength + vallength + 8);

   if (namelength < 128)
   {
      data.data_.push_back((uint8_t)namelength);
   }
   else
   {
      uint8_t* lengthptr = (uint8_t*)&namelength;
      data.data_.push_back(lengthptr[3]);
      data.data_.push_back(lengthptr[2]);
      data.data_.push_back(lengthptr[1]);
      data.data_.push_back(lengthptr[0]);
   }

   if (vallength < 128)
   {
      data.data_.push_back((uint8_t)vallength);
   }
   else
   {
      uint8_t* lengthptr = (uint8_t*)&vallength;
      data.data_.push_back(lengthptr[3]);
      data.data_.push_back(lengthptr[2]);
      data.data_.push_back(lengthptr[1]);
      data.data_.push_back(lengthptr[0]);
   }

   data.data_.insert(data.data_.end(), name.begin(), name.end());
   data.data_.insert(data.data_.end(), val.begin(), val.end());
}

///////////////////////////////////////////////////////////////////////////////
void FcgiPacket::addData(const char* msg, size_t length)
{
   data_.push_back(FcgiData());
   FcgiData& data = data_.back();

   if (length == 0)
      return;

   data.data_.resize(length);
   memcpy(&data.data_[0], msg, length);
}


///////////////////////////////////////////////////////////////////////////////
//
// FcgiMessage
//
///////////////////////////////////////////////////////////////////////////////
uint8_t* FcgiMessage::serialize(void)
{
   for (auto& packet : packets_)
   {
      serData_.data_.insert(serData_.data_.end(),
         packet.header_.data_.begin(), packet.header_.data_.end());

      for (auto& data : packet.data_)
      {
         serData_.data_.insert(serData_.data_.end(),
            data.data_.begin(), data.data_.end());
      }
   }

   return &serData_.data_[0];
}

///////////////////////////////////////////////////////////////////////////////
void FcgiMessage::clear(void)
{
   packets_.clear();
   serData_.clear();
   requestID_ = -1;
}

///////////////////////////////////////////////////////////////////////////////
FcgiPacket& FcgiMessage::getNewPacket(void)
{
   packets_.push_back(FcgiPacket());
   return packets_.back();
}

///////////////////////////////////////////////////////////////////////////////
uint16_t FcgiMessage::beginRequest(void)
{
   //randomize requestID
   requestID_ = 1 + rand() % 65534; //cannot be 0

   //make begin_request packet
   auto& packet = getNewPacket();
   packet.data_.resize(1);
   FcgiData& data = packet.data_.back();

   data.data_.resize(8);
   uint8_t* msg = &data.data_[0];

   memset(msg, 0, 8);
   msg[1] = FCGI_RESPONDER; //request role B0

   packet.buildHeader(FCGI_BEGIN_REQUEST, requestID_);

   return requestID_;
}
///////////////////////////////////////////////////////////////////////////////
FcgiMessage FcgiMessage::makePacket(const char *msg)
{
   FcgiMessage fcgiMsg;
   auto requestID = fcgiMsg.beginRequest();

   stringstream msglength;
   msglength << strlen(msg);

   //params
   auto& params = fcgiMsg.getNewPacket();
   params.addParam("CONTENT_TYPE", "text/html; charset=UTF-8");
   params.addParam("CONTENT_LENGTH", msglength.str());
   params.buildHeader(FCGI_PARAMS, requestID);

   //terminate fcgi_param
   auto& paramterminator = fcgiMsg.getNewPacket();
   paramterminator.buildHeader(FCGI_PARAMS, requestID);

   //data
   auto msglen = strlen(msg);
   size_t offset = 0;
   size_t uint16max = UINT16_MAX;
   while (msglen > offset)
   {
      size_t currentlen = min(msglen - offset, uint16max);
      auto& data = fcgiMsg.getNewPacket();
      data.addData(msg + offset, currentlen);
      data.buildHeader(FCGI_STDIN, requestID);

      offset += currentlen;
   }

   //terminate fcgi_stdin
   auto& dataterminator = fcgiMsg.getNewPacket();
   dataterminator.buildHeader(FCGI_STDIN, requestID);

   return fcgiMsg;
}
