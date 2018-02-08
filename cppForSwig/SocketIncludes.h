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

#define SOCK_MAX SIZE_MAX

#else
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#include <fcntl.h>
#include <limits.h>
#define closesocket close

typedef int SOCKET;
#define SOCK_MAX INT_MAX
#endif

////////////////////////////////////////////////////////////////////////////////
#include <string>

struct SocketError : public runtime_error
{
public:
   SocketError(const string& e) : runtime_error(e)
   {}

};

#endif