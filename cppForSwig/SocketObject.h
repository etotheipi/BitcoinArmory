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

#ifdef _WIN32
#include <WinSock2.h>
#include <ws2tcpip.h>

#define WRITETOSOCKET(a, b, c) send(a, b, c, NULL)
#define READFROMSOCKET(a, b, c) recv(a, b, c, NULL)

#else
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#define closesocket close

#define WRITETOSOCKET(a, b, c) send(a, b, c, 0)
#define READFROMSOCKET(a, b, c) recv(a, b, c, 0)

typedef int SOCKET;
#endif

using namespace std;

///////////////////////////////////////////////////////////////////////////////
class BinarySocket
{
   friend class HttpSocket;
   friend class FcgiSocket;

private:
   const size_t maxread_ = 1024*1024*1024;
   
   struct sockaddr serv_addr_;
   const string addr_;
   const string port_;

private:   
   SOCKET open(void);
   void close(SOCKET);
   void write(SOCKET, const char*, uint32_t);
   void read(SOCKET, vector<char>& buffer);

public:
   BinarySocket(const string& addr, const string& port);

   virtual string writeAndRead(const string&);
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
   virtual string writeAndRead(const string&);
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
   string writeAndRead(const string&);
   SocketType type(void) const { return SocketFcgi; }
};

#endif
