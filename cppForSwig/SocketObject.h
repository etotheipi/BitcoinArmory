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
#include <memory>

#ifndef _WIN32
#include <poll.h>
#endif

#include "ThreadSafeClasses.h"
#include "bdmenums.h"
#include "log.h"

#include "SocketIncludes.h"

using namespace std;

///////////////////////////////////////////////////////////////////////////////
class BinarySocket
{
protected:
   const size_t maxread_ = 4*1024*1024;
   
   struct sockaddr serv_addr_;
   const string addr_;
   const string port_;

private:
   void readFromSocketThread(SOCKET sockfd,
      shared_ptr<BlockingStack<vector<uint8_t>>>);

protected:   
   void closeSocket(SOCKET&);
   void writeToSocket(SOCKET&, void*, size_t);
   void readFromSocket(SOCKET& sockfd,
      shared_ptr<BlockingStack<vector<uint8_t>>>);
   void setBlocking(SOCKET&, bool);
   
   vector<uint8_t> writeAndRead(
      SOCKET& sfd, void* data, size_t datalen, 
      shared_ptr<BlockingStack<vector<uint8_t>>>);

public:
   SOCKET openSocket(bool blocking);

   BinarySocket(const string& addr, const string& port);
   bool testConnection(void);

   virtual string writeAndRead(const string&, SOCKET sock = SOCK_MAX)
   {
      throw SocketError("not implemened, use the protected method instead");
   }

   virtual SocketType type(void) const { return SocketBinary; }
};

///////////////////////////////////////////////////////////////////////////////
class DedicatedBinarySocket : public BinarySocket
{
private:
   SOCKET sockfd_ = SOCK_MAX;

public:
   DedicatedBinarySocket(const string& addr, const string& port) :
      BinarySocket(addr, port)
   {}

   ~DedicatedBinarySocket(void) { BinarySocket::closeSocket(sockfd_); }

   vector<uint8_t> writeAndRead(
      SOCKET& sfd, void* data, size_t datalen,
      shared_ptr<BlockingStack<vector<uint8_t>>> readStack)
   {
      return BinarySocket::writeAndRead(sockfd_, data, datalen, readStack);
   }

   void closeSocket()
   {
      BinarySocket::closeSocket(sockfd_);
   }

   void writeToSocket(void* data, size_t len)
   {
      BinarySocket::writeToSocket(sockfd_, data, len);
   }

   void readFromSocket(
      shared_ptr<BlockingStack<vector<uint8_t>>> readStack)
   {
      BinarySocket::readFromSocket(sockfd_, readStack);
   }

   bool openSocket(bool blocking)
   {
      sockfd_ = BinarySocket::openSocket(blocking);
      
      return isValid();
   }

   int getSocketName(struct sockaddr& sa)
   {
#ifdef _WIN32
      int namelen = sizeof(sa);
#else
      unsigned int namelen = sizeof(sa);
#endif

      return getsockname(sockfd_, &sa, &namelen);
   }

   bool isValid(void) const { return sockfd_ != SOCK_MAX; }
};

#endif
