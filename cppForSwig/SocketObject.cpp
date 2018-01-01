////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "SocketObject.h"
#include <cstring>
#include <stdexcept>

///////////////////////////////////////////////////////////////////////////////
//
// BinarySocket
//
///////////////////////////////////////////////////////////////////////////////
BinarySocket::BinarySocket(const string& addr, const string& port) :
   addr_(addr), port_(port)
{
   //resolve address
   struct addrinfo hints;
   struct addrinfo *result;
   memset(&hints, 0, sizeof(hints));
   hints.ai_family = AF_UNSPEC;
   hints.ai_socktype = SOCK_STREAM;
   hints.ai_protocol = IPPROTO_TCP;

#ifdef _WIN32
   //somehow getaddrinfo doesnt handle localhost on Windows
   string addrstr = addr;
   if(addr == "localhost")
      addrstr = "127.0.0.1"; 
#else
   auto& addrstr = addr;
#endif

   getaddrinfo(addrstr.c_str(), port.c_str(), &hints, &result);
   for (auto ptr = result; ptr != nullptr; ptr = ptr->ai_next)
   {
      if (ptr->ai_family == AF_INET)
      {
         memcpy(&serv_addr_, ptr->ai_addr, sizeof(sockaddr_in));
         memcpy(&serv_addr_.sa_data, &ptr->ai_addr->sa_data, 14);
         break;
      }

      throw runtime_error("unsupported remote address format");
   }
   freeaddrinfo(result);
}

///////////////////////////////////////////////////////////////////////////////
SOCKET BinarySocket::openSocket(bool blocking)
{
   SOCKET sockfd = SOCK_MAX;
   try
   {
      sockfd = socket(serv_addr_.sa_family, SOCK_STREAM, 0);
      if (sockfd < 0)
         throw SocketError("failed to create socket");

      auto result = connect(sockfd, &serv_addr_, sizeof(serv_addr_));
      if (result < 0)
      {
         closeSocket(sockfd);
         throw SocketError("failed to connect to server");
      }
   
      setBlocking(sockfd, blocking);
   }
   catch (SocketError &)
   {
      closeSocket(sockfd);
      sockfd = SOCK_MAX;
   }

   return sockfd;
}

///////////////////////////////////////////////////////////////////////////////
void BinarySocket::closeSocket(SOCKET& sockfd)
{
   if (sockfd == SOCK_MAX)
      return;

#ifdef WIN32
   closesocket(sockfd);
#else
   close(sockfd);
#endif

   sockfd = SOCK_MAX;
}

////////////////////////////////////////////////////////////////////////////////
void BinarySocket::writeToSocket(SOCKET sockfd, void* data, size_t size)
{
   //don't return we have written and are write ready
   struct pollfd pfd;
   bool haveWritten = false;

   pfd.fd = sockfd;
   pfd.events = POLLOUT;

   size_t total_send = 0;

   while (1)
   {
#ifdef _WIN32
      auto status = WSAPoll(&pfd, 1, 60000);
#else
      auto status = poll(&pfd, 1, 60000);
#endif

      if (status == 0)
         continue;
      else if (status == -1)
      {
#ifdef _WIN32
         auto errornum = WSAGetLastError();
#else
         auto errornum = errno;
#endif
         stringstream ss;
         ss << "poll() error in writeToSocket: " << errornum;

         LOGERR << ss.str();
         throw SocketError(ss.str());
      }

      //exceptions
      if (pfd.revents & POLLERR)
      {
         //break out of poll loop
         LOGERR << "POLLERR in writeToSocket";
         throw SocketError("POLLERR in writeToSocket");
      }

      if (pfd.revents & POLLNVAL)
      {
         //LOGERR << "POLLNVAL in writeToSocket";
         throw SocketError("POLLNVAL in writeToSocket");
      }

      if (pfd.revents & POLLOUT)
      {
         if (!haveWritten)
         {
            auto bytessent = send(
               sockfd, (char*)data + total_send, size - total_send, 0);
            if (bytessent == 0)
               throw SocketError("failed to send data");

            total_send += bytessent;
            if (total_send >= size)
               haveWritten = true;
         }
         else
         {
            //write ready
            break;
         }
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
bool BinarySocket::testConnection(void)
{
   try
   {
      auto sockfd = openSocket(true);
      if (sockfd == SOCK_MAX)
         return false;

      closeSocket(sockfd);
      return true;
   }
   catch (runtime_error&)
   {
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
void BinarySocket::setBlocking(SOCKET sock, bool setblocking)
{
   if (sock < 0)
      throw SocketError("invalid socket");

#ifdef WIN32
   unsigned long mode = (unsigned long)!setblocking;
   if (ioctlsocket(sock, FIONBIO, &mode) != 0)
      throw SocketError("failed to set blocking mode on socket");
#else
   int flags = fcntl(sock, F_GETFL, 0);
   if (flags < 0) return;
   flags = setblocking ? (flags&~O_NONBLOCK) : (flags | O_NONBLOCK);
   int rt = fcntl(sock, F_SETFL, flags);
   if (rt != 0)
   {
      auto thiserrno = errno;
      cout << "fcntl returned " << rt << endl;
      cout << "error: " << strerror(errno);
      throw SocketError("failed to set blocking mode on socket");
   }
#endif
}

///////////////////////////////////////////////////////////////////////////////
void BinarySocket::readFromSocket(SOCKET sockfd, ReadCallback callback)
{
   exception_ptr exceptptr = nullptr;

   auto readLambda = [sockfd, callback, this](void)->void
   {
      try
      {
         readFromSocketThread(sockfd, callback);
      }
      catch (...)
      {
      }
   };

   thread readThr(readLambda);
   if (readThr.joinable())
      readThr.detach();
}

///////////////////////////////////////////////////////////////////////////////
void BinarySocket::readFromSocketThread(SOCKET sockfd, ReadCallback callback)
{
   size_t readIncrement = 8192;
   stringstream errorss;

   exception_ptr exceptptr = nullptr;

   struct pollfd pfd;
   pfd.fd = sockfd;
   pfd.events = POLLIN;

   try
   {
      while (1)
      {
#ifdef _WIN32
         auto status = WSAPoll(&pfd, 1, 60000);
#else
         auto status = poll(&pfd, 1, 60000);
#endif

         if (status == 0)
            continue;

         if (status == -1)
         {
            //select error, process and exit loop
#ifdef _WIN32
            auto errornum = WSAGetLastError();
#else
            auto errornum = errno;
#endif
            errorss << "poll() error in readFromSocketThread: " << errornum;
            LOGERR << errorss.str();
            throw SocketError(errorss.str());
         }

         if (pfd.revents & POLLNVAL)
         {
#ifndef _WIN32
            /*int error = 0;
            socklen_t errlen = sizeof(error);
            getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void *)&error, &errlen);
            LOGERR << "readFromSocketThread poll returned POLLNVAL, errnum: " <<
               error << ", errmsg: " << strerror(error);*/            
#endif
            throw SocketError("POLLNVAL in readFromSocketThread");
         }

         //exceptions
         if (pfd.revents & POLLERR)
         {
            //TODO: grab socket error code, pass error to callback

            //break out of poll loop
            errorss << "POLLERR error in readFromSocketThread";
            LOGERR << errorss.str();
            throw SocketError(errorss.str());
         }

         if (pfd.revents & POLLRDBAND)
         {
            //we dont use OOB data, just grab and dump
            vector<uint8_t> readdata;
            readdata.resize(1024);
            int readAmt;
            size_t totalread = 0;

            while (readAmt =
               recv(sockfd, (char*)&readdata[0] + totalread, 1024, MSG_OOB))
            {
               if (readAmt < 0)
                  break;

               totalread += readAmt;
               if (readAmt < 1024)
                  break;

               readdata.resize(totalread + 1024);
            }
         }

         if (pfd.revents & POLLIN)
         {
            //read socket
            vector<uint8_t> readdata;
            readdata.resize(readIncrement);

            size_t totalread = 0;
            int readAmt;

            while ((readAmt =
               recv(sockfd, (char*)&readdata[0] + totalread , readIncrement, 0))
               != 0)
            {
               if (readAmt < 0)
               {
#ifdef _WIN32
                  auto errornum = WSAGetLastError();
                  if(errornum == WSAEWOULDBLOCK)
                     break;
#else
                  auto errornum = errno;
                  if (errornum == EAGAIN || errornum == EWOULDBLOCK)
                     break;
#endif

                  errorss << "recv error: " << errornum;
                  throw SocketError(errorss.str());
                  break;
               }

               totalread += readAmt;
               if (readAmt < readIncrement)
                  break;

               readdata.resize(totalread + readIncrement);
            }

            if (readAmt == 0)
            {
               LOGINFO << "POLLIN recv return 0";
               break;
            }

            if (totalread > 0)
            {
               readdata.resize(totalread);

               //callback with the new data, exit poll loop on true
               if (callback(move(readdata), nullptr))
                  break;
            }
         }

         //socket was closed
         if (pfd.revents & POLLHUP)
            break;
      }
   }
   catch (...)
   {
      exceptptr = current_exception();
   }

   //cleanup
   closeSocket(sockfd);
   
   //mark read as completed
   callback(vector<uint8_t>(), exceptptr);
}

///////////////////////////////////////////////////////////////////////////////
void BinarySocket::writeAndRead(
   SOCKET sockfd, uint8_t* data, size_t len, SequentialReadCallback callback)
{
   size_t readIncrement = 8192;
   stringstream errorss;
   bool haveWritten = false;

   exception_ptr exceptptr = nullptr;

   struct pollfd pfd;
   pfd.fd = sockfd;
   pfd.events = POLLOUT;

   size_t total_send = 0;

   while (1)
   {
#ifdef _WIN32
      auto status = WSAPoll(&pfd, 1, 60000);
#else
      auto status = poll(&pfd, 1, 60000);
#endif

      if (status == 0)
         continue;

      if (status == -1)
      {
         //select error, process and exit loop
#ifdef _WIN32
         auto errornum = WSAGetLastError();
#else
         auto errornum = errno;
#endif
         errorss << "poll() error in readAndWrite: " << errornum;
         if (verbose_)
            LOGERR << errorss.str();
         throw SocketError(errorss.str());
      }

      if (pfd.revents & POLLNVAL)
      {
#ifndef _WIN32
         /*int error = 0;
         socklen_t errlen = sizeof(error);
         getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void *)&error, &errlen);
         LOGERR << "readFromSocketThread poll returned POLLNVAL, errnum: " <<
         error << ", errmsg: " << strerror(error);*/
#endif
         throw SocketError("POLLNVAL in readAndWrite");
      }

      //exceptions
      if (pfd.revents & POLLERR)
      {
         //TODO: grab socket error code, pass error to callback

         //break out of poll loop
         errorss << "POLLERR error in readAndWrite";
         if (verbose_)
            LOGERR << errorss.str();
         throw SocketError(errorss.str());
      }

      if (pfd.revents & POLLOUT)
      {
         if (!haveWritten)
         {
            auto bytessent = send(
               sockfd, (char*)data + total_send, len - total_send, 0);
            if (bytessent == 0)
               throw SocketError("failed to send data");

            total_send += bytessent;
            if (total_send >= len)
            {
               haveWritten = true;
               pfd.events = POLLIN;
            }
         }
      }

      if (pfd.revents & POLLRDBAND)
      {
         //we dont use OOB data, just grab and dump
         vector<uint8_t> readdata;
         readdata.resize(1024);
         int readAmt;
         size_t totalread = 0;

         while (readAmt =
            recv(sockfd, (char*)&readdata[0] + totalread, 1024, MSG_OOB))
         {
            if (readAmt < 0)
               break;

            totalread += readAmt;
            if (readAmt < 1024)
               break;

            readdata.resize(totalread + 1024);
         }
      }

      if (pfd.revents & POLLIN)
      {
         //read socket
         vector<uint8_t> readdata;
         readdata.resize(readIncrement);

         size_t totalread = 0;
         int readAmt;

         while ((readAmt =
            recv(sockfd, (char*)&readdata[0] + totalread, readIncrement, 0))
            != 0)
         {
            if (readAmt < 0)
            {
#ifdef _WIN32
               auto errornum = WSAGetLastError();
               if (errornum == WSAEWOULDBLOCK)
                  break;
#else
               auto errornum = errno;
               if (errornum == EAGAIN || errornum == EWOULDBLOCK)
                  break;
#endif

               errorss << "recv error: " << errornum;
               throw SocketError(errorss.str());
               break;
            }

            totalread += readAmt;
            if (readAmt < readIncrement)
               break;

            readdata.resize(totalread + readIncrement);
         }

         if (readAmt == 0)
         {
            if (!callback(readdata))
            {
               if (verbose_)
                  LOGINFO << "POLLIN recv return 0";
            }

            break;
         }

         if (totalread > 0)
         {
            readdata.resize(totalread);

            //callback with the new data, exit poll loop on true
            if (callback(readdata))
               break;
         }
      }

      //socket was closed
      if (pfd.revents & POLLHUP)
         break;
   }

   //cleanup
   closeSocket(sockfd);
}

///////////////////////////////////////////////////////////////////////////////
void BinarySocket::listen(AcceptCallback callback)
{
   SOCKET sockfd = SOCK_MAX;
   try
   {
      sockfd = socket(serv_addr_.sa_family, SOCK_STREAM, 0);
      if (sockfd < 0)
         throw SocketError("failed to create socket");

      if (::bind(sockfd, &serv_addr_, sizeof(serv_addr_)) < 0)
      {
         closeSocket(sockfd);
         throw SocketError("failed to bind socket");
      }

      if (::listen(sockfd, 10) < 0)
      {
         closeSocket(sockfd);
         throw SocketError("failed to listen to socket");
      }
   }
   catch (SocketError &)
   {
      closeSocket(sockfd);
      return;
   }

   stringstream errorss;
   exception_ptr exceptptr = nullptr;

   struct pollfd pfd;
   pfd.fd = sockfd;
   pfd.events = POLLIN;

   try
   {
      while (1)
      {
#ifdef _WIN32
         auto status = WSAPoll(&pfd, 1, 60000);
#else
         auto status = poll(&pfd, 1, 60000);
#endif

         if (status == 0)
            continue;

         if (status == -1)
         {
            //select error, process and exit loop
#ifdef _WIN32
            auto errornum = WSAGetLastError();
#else
            auto errornum = errno;
#endif
            errorss << "poll() error in readFromSocketThread: " << errornum;
            LOGERR << errorss.str();
            throw SocketError(errorss.str());
         }

         if (pfd.revents & POLLNVAL)
         {
#ifndef _WIN32
            /*int error = 0;
            socklen_t errlen = sizeof(error);
            getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void *)&error, &errlen);
            LOGERR << "readFromSocketThread poll returned POLLNVAL, errnum: " <<
            error << ", errmsg: " << strerror(error);*/
#endif
            throw SocketError("POLLNVAL in readFromSocketThread");
         }

         //exceptions
         if (pfd.revents & POLLERR)
         {
            //TODO: grab socket error code, pass error to callback

            //break out of poll loop
            errorss << "POLLERR error in readFromSocketThread";
            LOGERR << errorss.str();
            throw SocketError(errorss.str());
         }

         if (pfd.revents & POLLIN)
         {
            //accept socket and trigger callback
            AcceptStruct astruct;
            astruct.sockfd_ = accept(sockfd, &astruct.saddr_, &astruct.addrlen_);
            callback(move(astruct));
         }
      }
   }
   catch (...)
   {
      exceptptr = current_exception();
   }

   //cleanup
   closeSocket(sockfd);
}

///////////////////////////////////////////////////////////////////////////////
ListenServer::ListenServer(const string& addr, const string& port)
{
   listenSocket_ = make_unique<DedicatedBinarySocket>(addr, port);
   listenSocket_->verbose_ = false;
}

///////////////////////////////////////////////////////////////////////////////
void ListenServer::start(ReadCallback callback)
{
   auto listenlbd = [this](ReadCallback clbk)->void
   {
      this->listenThread(clbk);
   };

   listenThread_ = thread(listenlbd, callback);
}

///////////////////////////////////////////////////////////////////////////////
void ListenServer::join()
{
   if (listenThread_.joinable())
      listenThread_.join();
}

///////////////////////////////////////////////////////////////////////////////
void ListenServer::listenThread(ReadCallback callback)
{
   auto acceptldb = [callback, this](AcceptStruct astruct)->void
   {
      astruct.readCallback_ = callback;
      this->acceptProcess(move(astruct));
   };

   listenSocket_->listen(acceptldb);
}

///////////////////////////////////////////////////////////////////////////////
void ListenServer::acceptProcess(AcceptStruct aStruct)
{
   unique_lock<mutex> lock(mu_);

   auto readldb = [this](
      shared_ptr<DedicatedBinarySocket> sock, ReadCallback callback)->void
   {
      sock->readFromSocket(callback);
      auto sockfd = sock->sockfd_;
      this->cleanUpStack_.push_back(move(sockfd));
   };

   auto ss = make_unique<SocketStruct>();

   //create BinarySocket object from sockfd
   ss->sock_ = make_shared<DedicatedBinarySocket>(aStruct.sockfd_);
   ss->sock_->verbose_ = false;

   //start read lambda thread
   ss->thr_ = thread(readldb, ss->sock_, aStruct.readCallback_);

   //record thread id and socket ptr in socketStruct, add to acceptMap_
   acceptMap_.insert(make_pair(aStruct.sockfd_, move(ss)));

   //run through clean up stack, removing flagged entries from acceptMap_
   try
   {
      while (1)
      {
         auto&& sock = cleanUpStack_.pop_front();
         auto iter = acceptMap_.find(sock);
         if (iter != acceptMap_.end())
         {
            auto ssptr = move(iter->second);
            acceptMap_.erase(iter);

            if (ssptr->thr_.joinable())
               ssptr->thr_.join();
         }
      }
   }
   catch (IsEmpty&)
   { 
   }
}

///////////////////////////////////////////////////////////////////////////////
void ListenServer::stop()
{
   listenSocket_->closeSocket();
   if (listenThread_.joinable())
      listenThread_.join();

   for (auto& sockPair : acceptMap_)
   {
      auto& sockstruct = sockPair.second;
      
      sockstruct->sock_->closeSocket();
      if (sockstruct->thr_.joinable())
         sockstruct->thr_.join();
   }
}
