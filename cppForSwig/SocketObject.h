////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _SOCKETOBJ_H
#define _SOCKETOBJ_H

#include <sys/types.h>
#include <string>
#include <sstream>
#include <stdint.h>
#include <functional>

#include "FcgiMessage.h"
#include "bdmenums.h"

#include "SocketIncludes.h"

using namespace std;

///////////////////////////////////////////////////////////////////////////////
class BinarySocket
{
protected:
   const size_t maxread_ = 1024*1024*1024;
   
   struct sockaddr serv_addr_;
   const string addr_;
   const string port_;

protected:   
   void closeSocket(SOCKET);
   void writeToSocket(SOCKET, const char*, uint32_t);
   void readFromSocket(SOCKET, vector<char>& buffer);

public:
   SOCKET openSocket(void);
   BinarySocket(const string& addr, const string& port);
   bool testConnection(void);

   virtual string writeAndRead(const string&, SOCKET sfd = SOCK_MAX);
   virtual SocketType type(void) const { return SocketBinary; }
};

///////////////////////////////////////////////////////////////////////////////
class HttpSocket : public BinarySocket
{
   friend class FcgiSocket;

private:
   string http_header_;

private:
   int32_t makePacket(char** packet, const char* msg);
   string getMessage(vector<char>&);

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
   string getMessage(const vector<char>&, const FcgiMessage&);

public:
   FcgiSocket(const HttpSocket&);
   string writeAndRead(const string&, SOCKET sfd = SOCK_MAX);
   SocketType type(void) const { return SocketFcgi; }
};

#endif
