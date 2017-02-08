////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_STRING_SOCKETS
#define _H_STRING_SOCKETS

#include <string.h>
#include "SocketObject.h"
#include "FcgiMessage.h"

///////////////////////////////////////////////////////////////////////////////
struct HttpError : public SocketError
{
public:
   HttpError(const string& e) : SocketError(e)
   {}
};

///////////////////////////////////////////////////////////////////////////////
struct FcgiError : public SocketError
{
public:
   FcgiError(const string& e) : SocketError(e)
   {}
};

///////////////////////////////////////////////////////////////////////////////
class HttpSocket : public BinarySocket
{
   friend class FcgiSocket;

   vector<string> headers_;

private:
   struct packetData
   {
      vector<uint8_t> httpData;
      int content_length = -1;
      size_t header_len = 0;

      void clear(void)
      {
         httpData.clear();
         content_length = -1;
         header_len = 0;
      }

      void get_content_len(const string& header_str)
      {
         string err504("HTTP/1.1 504");
         if (header_str.compare(0, err504.size(), err504) == 0)
            throw HttpError("connection timed out");

         string search_tok_caps("Content-Length: ");
         auto tokpos = header_str.find(search_tok_caps);
         if (tokpos != string::npos)
         {
            content_length = atoi(header_str.c_str() +
               tokpos + search_tok_caps.size());
            return;
         }

         string search_tok("content-length: ");
         tokpos = header_str.find(search_tok);
         if (tokpos != string::npos)
         {
            content_length = atoi(header_str.c_str() +
               tokpos + search_tok.size());
            return;
         }
      }
   };

private:
   int32_t makePacket(char** packet, const char* msg);
   string getBody(vector<uint8_t>);
   void setupHeaders(void);

public:
   HttpSocket(const BinarySocket&);

   void resetHeaders(void);
   void addHeader(string);

   virtual string writeAndRead(const string&, SOCKET sockfd = SOCK_MAX);
   virtual SocketType type(void) const { return SocketHttp; }
};

///////////////////////////////////////////////////////////////////////////////
class FcgiSocket : public HttpSocket
{
private:
   void addStringParam(const string& name, const string& val);

   struct packetStruct
   {
      vector<uint8_t> fcgidata;
      vector<uint8_t> httpData;

      int endpacket = 0;
      size_t ptroffset = 0;
      uint16_t fcgiid = 0;

      void clear(void)
      {
         fcgidata.clear();
         httpData.clear();

         endpacket = 0;
         ptroffset = 0;
      }
   };

public:
   FcgiSocket(const HttpSocket&);
   string writeAndRead(const string&, SOCKET sfd = SOCK_MAX);
   SocketType type(void) const { return SocketFcgi; }
};

#endif
