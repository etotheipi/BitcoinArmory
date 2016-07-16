////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_STRING_SOCKETS
#define _H_STRING_SOCKETS

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

private:
   string http_header_;

private:
   int32_t makePacket(char** packet, const char* msg);
   string getBody(vector<uint8_t>);

public:
   HttpSocket(const BinarySocket&);
   virtual string writeAndRead(const string&, SOCKET sockfd = SOCK_MAX);
   virtual SocketType type(void) const { return SocketHttp; }
};

///////////////////////////////////////////////////////////////////////////////
class FcgiSocket : public HttpSocket
{
private:
   void addStringParam(const string& name, const string& val);
   FcgiMessage makePacket(const char*);

public:
   FcgiSocket(const HttpSocket&);
   string writeAndRead(const string&, SOCKET sfd = SOCK_MAX);
   SocketType type(void) const { return SocketFcgi; }
};

#endif