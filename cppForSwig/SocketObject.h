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
   
typedef function<bool(vector<uint8_t>, exception_ptr)>  ReadCallback;

///////////////////////////////////////////////////////////////////////////////
struct AcceptStruct
{
   SOCKET sockfd_;
   sockaddr saddr_;
   socklen_t addrlen_;
   ReadCallback readCallback_;

   AcceptStruct(void) :
      addrlen_(sizeof(saddr_))
   {}
};

///////////////////////////////////////////////////////////////////////////////
class BinarySocket
{
   friend class FCGI_Server;
   friend class ListenServer;

protected:

public:
   typedef function<bool(const vector<uint8_t>&)>  SequentialReadCallback;
   typedef function<void(AcceptStruct)> AcceptCallback;

protected:
   const size_t maxread_ = 4*1024*1024;
   
   struct sockaddr serv_addr_;
   const string addr_;
   const string port_;

   bool verbose_ = true;

private:
   void readFromSocketThread(SOCKET, ReadCallback);

protected:   
   void writeToSocket(SOCKET, void*, size_t);
   void readFromSocket(SOCKET, ReadCallback);
   void setBlocking(SOCKET, bool);

   void writeAndRead(SOCKET, uint8_t*, size_t, 
      SequentialReadCallback);

   void listen(AcceptCallback);

   BinarySocket(void) :
      addr_(""), port_("")
   {}
   
public:
   BinarySocket(const string& addr, const string& port);

   bool testConnection(void);
   SOCKET openSocket(bool blocking);
   
   static void closeSocket(SOCKET&);

   virtual string writeAndRead(const string&, SOCKET sock = SOCK_MAX)
   {
      throw SocketError("not implemented, use the protected method instead");
   }

   virtual SocketType type(void) const { return SocketBinary; }
};

///////////////////////////////////////////////////////////////////////////////
class DedicatedBinarySocket : public BinarySocket
{
   friend class ListenServer;

private:
   SOCKET sockfd_ = SOCK_MAX;

public:
   DedicatedBinarySocket(const string& addr, const string& port) :
      BinarySocket(addr, port)
   {}

   DedicatedBinarySocket(SOCKET sockfd) :
      BinarySocket(), sockfd_(sockfd)
   {}

   ~DedicatedBinarySocket(void) 
   { BinarySocket::closeSocket(sockfd_); }

   void closeSocket()
   {
      BinarySocket::closeSocket(sockfd_);
   }

   void writeToSocket(void* data, size_t len)
   {
      BinarySocket::writeToSocket(sockfd_, data, len);
   }

   void readFromSocket(ReadCallback callback)
   {
      BinarySocket::readFromSocket(sockfd_, callback);
   }

   bool openSocket(bool blocking)
   {
      if (addr_.size() != 0 && port_.size() != 0)
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

   int getPeerName(struct sockaddr& sa)
   {
#ifdef _WIN32
      int namelen = sizeof(sa);
#else
      unsigned int namelen = sizeof(sa);
#endif

      return getpeername(sockfd_, &sa, &namelen);
   }

   bool isValid(void) const { return sockfd_ != SOCK_MAX; }
};

///////////////////////////////////////////////////////////////////////////////
class ListenServer
{
private:
   struct SocketStruct
   {
   private:
      SocketStruct(const SocketStruct&) = delete;

   public:
      SocketStruct(void)
      {}

      shared_ptr<DedicatedBinarySocket> sock_;
      thread thr_;
   };

private:
   unique_ptr<DedicatedBinarySocket> listenSocket_;
   map<SOCKET, unique_ptr<SocketStruct>> acceptMap_;
   Stack<SOCKET> cleanUpStack_;

   thread listenThread_;
   mutex mu_;

private:
   void listenThread(ReadCallback);
   void acceptProcess(AcceptStruct);
   ListenServer(const ListenServer&) = delete;

public:
   ListenServer(const string& addr, const string& port);
   ~ListenServer(void)
   {
      stop();
   }

   void start(ReadCallback);
   void stop(void);
   void join(void);
};

#endif
