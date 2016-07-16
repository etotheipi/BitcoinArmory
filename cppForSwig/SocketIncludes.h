////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_SOCKET_INCLUDES
#define _H_SOCKET_INCLUDES

#ifdef _WIN32
#include <WinSock2.h>
#include <ws2tcpip.h>

#define WRITETOSOCKET(a, b, c) send(a, b, c, NULL)
#define READFROMSOCKET(a, b, c) recv(a, b, c, NULL)

#define SOCK_MAX SIZE_MAX

#else
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#include <fcntl.h>
#include <limits.h>
#define closesocket close

#define WRITETOSOCKET(a, b, c) send(a, b, c, 0)
#define READFROMSOCKET(a, b, c) recv(a, b, c, 0)

typedef int SOCKET;
#define SOCK_MAX INT_MAX
#endif

////////////////////////////////////////////////////////////////////////////////
#include <string>

struct SocketError
{
private:
   const string error_;

public:
   SocketError(const string& e) : error_(e)
   {}

   const string& what(void) const { return error_; }

};

#endif