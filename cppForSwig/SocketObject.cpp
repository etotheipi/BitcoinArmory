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

      if (connect(sockfd, &serv_addr_, sizeof(serv_addr_)) < 0)
      {
         closeSocket(sockfd);
         throw SocketError("failed to connect to server");
      }
   
      setBlocking(sockfd, blocking);
   }
   catch (SocketError &e)
   {
      closesocket(sockfd);
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
void BinarySocket::writeToSocket(
   SOCKET& sockfd, void* data, size_t size)
{
   //don't return we have written and are write ready
   fdset_except_safe write_set, except_set;
   bool haveWritten = false;

   while (1)
   {
      timeval tv;
      tv.tv_usec = 0;
      tv.tv_sec = 60; //1min timeout on select

      write_set.zero();
      except_set.zero();
      write_set.set(sockfd);
      except_set.set(sockfd);

      auto retval = select(sockfd + 1, nullptr, write_set.get(), except_set.get(), &tv);

      if (retval == 0)
         continue;
      else if (retval == -1)
      {
#ifdef _WIN32
         auto errornum = WSAGetLastError();
#else
         auto errornum = errno;
#endif
         stringstream ss;
         ss << "select error: " << errornum;
         throw SocketError(ss.str());
      }

      //exceptions
      if (FD_ISSET(sockfd, except_set.get()))
      {
         //grab socket error code

         //break out of poll loop
         throw SocketError("select expection during sendMessage");
         break;
      }

      if (FD_ISSET(sockfd, write_set.get()))
      {
         if (!haveWritten)
         {
            auto bytessent = WRITETOSOCKET(sockfd, (char*)data, size);
            if (bytessent != size)
               throw SocketError("failed to send data");

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
vector<uint8_t> BinarySocket::writeAndRead(
   SOCKET& sockfd, void* data, size_t datalen,
   shared_ptr<BlockingStack<vector<uint8_t>>> readStack)
{
   /***
   After the write, poll the socket and push back data to the readStack as
   it shows. Caller can halt this whole process by closing sockfd.
   Otherwise, the method exist when sockfd is closed by the other side.

   This method can be called from a thread (get() on the BlockingStack object) or
   directly (wait for it to return)
   ***/

   if (sockfd == SOCK_MAX)
      sockfd = this->openSocket(false);
   try
   {
      //TODO: what if the socket is closed before we get into the 
      //readFromSocket select()?
      writeToSocket(sockfd, data, datalen);
      readFromSocket(sockfd, readStack);
   }
   catch (SocketError &e)
   {
      LOGERR << "writeAndRead SocketError: " << e.what();
   }
   catch (exception &e)
   {
      LOGERR << "writeAndRead exception: " << e.what();
   }
   catch (...)
   {
      LOGERR << "writeAndRead unknown exception";
   }

   readStack->completed();
   closeSocket(sockfd);

   vector<uint8_t> dataVec;

   try
   {
      while (1)
      {
         auto&& packet = readStack->get();
         dataVec.insert(dataVec.end(), packet.begin(), packet.end());
      }
   }
   catch (IsEmpty&)
   {
   }

   return dataVec;
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
void BinarySocket::setBlocking(SOCKET& sock, bool setblocking)
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
void BinarySocket::readFromSocket(SOCKET& sockfd,
   shared_ptr<BlockingStack<vector<uint8_t>>> readStack)
{
   exception_ptr exceptptr = nullptr;

   auto readLambda = [sockfd, readStack, this](void)->void
   {
      try
      {
         readFromSocketThread(sockfd, readStack);
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
void BinarySocket::readFromSocketThread(SOCKET sockfd,
   shared_ptr<BlockingStack<vector<uint8_t>>> readStack)
{
   size_t readIncrement = 8192;
   fdset_except_safe read_set, except_set;
   stringstream errorss;

   exception_ptr exceptptr = nullptr;

   try
   {
      while (1)
      {
         timeval tv;
         tv.tv_usec = 0;
         tv.tv_sec = 60; //1min timeout on select

         read_set.zero();
         except_set.zero();

         read_set.set(sockfd);
         except_set.set(sockfd);

         auto status =
            select(sockfd + 1, read_set.get(), nullptr, except_set.get(), &tv);

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
            errorss << "select error: " << errornum;
            throw SocketError(errorss.str());
         }

         //exceptions
         if (FD_ISSET(sockfd, except_set.get()))
         {
            //TODO: grab socket error code, pass error to callback

            //break out of poll loop
            errorss << "socket exception";
            throw SocketError(errorss.str());
         }

         if (FD_ISSET(sockfd, read_set.get()))
         {
            //read socket
            vector<uint8_t> readdata;
            readdata.resize(readIncrement);

            size_t totalread = 0;
            int readAmt;

            while ((readAmt =
               READFROMSOCKET(sockfd, (char*)&readdata[0] + totalread , readIncrement))
               != 0)
            {
               if (readAmt < 0)
               {
                  /*errorss << "read socket error: " << readAmt;
                  throw SocketError(errorss.str());*/
                  break;
               }

               totalread += readAmt;
               if (readAmt < readIncrement)
                  break;

               readdata.resize(totalread + readIncrement);
            }

            if (totalread > 0)
            {
               readdata.resize(totalread);

               //callback with the new data
               readStack->push_back(move(readdata));
            }
            
            //socket closed, exit select loop
            if (readAmt == 0)
               break;
         }
      }
   }
   catch (...)
   {
      exceptptr = current_exception();
   }

   //cleanup
   read_set.zero();
   except_set.zero();
   closeSocket(sockfd);
   
   //mark read as completed
   readStack->completed(exceptptr);

   //rethrow in case of exception
   if (exceptptr != nullptr)
      rethrow_exception(exceptptr);
}
