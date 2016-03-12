////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "SocketObject.h"

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
   string& addrstr = addr;
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
SOCKET BinarySocket::open(void)
{
   int64_t sockfd = socket(serv_addr_.sa_family, SOCK_STREAM, 0);
   if (sockfd < 0)
      throw runtime_error("failed to create socket");

   if (connect(sockfd, &serv_addr_, sizeof(serv_addr_)) < 0)
      throw runtime_error("failed to connect to server");

   return sockfd;
}

///////////////////////////////////////////////////////////////////////////////
void BinarySocket::close(SOCKET sockfd)
{
   if (closesocket(sockfd) != 0)
      throw runtime_error("failed to close socket");
}

///////////////////////////////////////////////////////////////////////////////
void BinarySocket::write(SOCKET sockfd, const char* data, uint32_t size)
{
   if(WRITETOSOCKET(sockfd, data, size) != size)
      throw runtime_error("failed to write to socket");
}

///////////////////////////////////////////////////////////////////////////////
char* BinarySocket::read(SOCKET sockfd)
{
   char* retval = new char[maxread_ + 1];
   memset(retval, 0, maxread_);
   int readcount = maxread_;

   try
   {
      while (1)
      {
         auto bytesread = READFROMSOCKET(sockfd, retval, readcount);
         if (bytesread == 0)
            break;
         if (bytesread < 0)
            throw runtime_error("error while reading socket");

         readcount -= bytesread;
         if (readcount < 0)
            throw runtime_error("too much data to read from socket");
      }
   }
   catch (runtime_error &e)
   {
      delete[] retval;
      throw e;
   }

   return retval;
}

///////////////////////////////////////////////////////////////////////////////
string BinarySocket::writeAndRead(const string& msg)
{
   auto sockfd = this->open();

   this->write(sockfd, msg.c_str(), msg.size());
   auto retval = this->read(sockfd);
   auto&& retmsg = string(retval);

   this->close(sockfd);
   delete[] retval;
   
   return retmsg;
}

///////////////////////////////////////////////////////////////////////////////
//
// HttpSocket
//
///////////////////////////////////////////////////////////////////////////////
HttpSocket::HttpSocket(const BinarySocket& obj) :
   BinarySocket(obj)
{
   stringstream ss;
   ss << "POST index.html HTTP/1.1\r\n";
   ss << "Host: " << addr_ << "\r\n";
   ss << "Content-type: text/html; charset=UTF-8\r\n";
   ss << "Content-Length: ";

   http_header_ = move(ss.str());
}

///////////////////////////////////////////////////////////////////////////////
int32_t HttpSocket::makePacket(char** packet, const char* msg)
{
   if (packet == nullptr)
      return -1;

   stringstream ss;
   ss << strlen(msg);
   ss << "\r\n\r\n";

   *packet = new char[strlen(msg) +
      ss.str().size() +
      http_header_.size() +
      1];

   memcpy(*packet, http_header_.c_str(), http_header_.size());
   size_t pos = http_header_.size();

   memcpy(*packet + pos, ss.str().c_str(), ss.str().size());
   pos += ss.str().size();

   memcpy(*packet + pos, msg, strlen(msg));
   pos += strlen(msg);

   memset(*packet + pos, 0, 1);

   return pos + 1;
}

///////////////////////////////////////////////////////////////////////////////
string HttpSocket::getMessage(const char* msg)
{
   /***
   Always expect text data (null terminated)
   ***/

   //look for double crlf http header end, return everything after that
   string htmlstr(msg);
   size_t pos = htmlstr.find("\r\n\r\n");
   if (pos == string::npos)
   {
      //no html break, check for error marker
      pos = htmlstr.find("error:");
      if (pos != string::npos)
         throw runtime_error(htmlstr);

      throw runtime_error("unexpected return value");
   }

   return htmlstr.substr(pos +4);
}

///////////////////////////////////////////////////////////////////////////////
string HttpSocket::writeAndRead(const string& msg)
{
   auto sockfd = this->open();

   char* packet = nullptr;
   auto packetSize = makePacket(&packet, msg.c_str());
   
   this->write(sockfd, packet, packetSize);

   char* retval = this->read(sockfd);
   auto&& retmsg = getMessage(retval);
   
   this->close(sockfd);
   delete[] retval;
   delete[] packet;
   
   return retmsg;
}

///////////////////////////////////////////////////////////////////////////////
//
// FcgiSocket
//
///////////////////////////////////////////////////////////////////////////////
FcgiSocket::FcgiSocket(const HttpSocket& obj) :
   HttpSocket(obj)
{}

///////////////////////////////////////////////////////////////////////////////
FcgiMessage FcgiSocket::makePacket(const char* msg)
{
   FcgiMessage fcgiMsg;
   auto requestID = fcgiMsg.beginRequest();

   stringstream msglength;
   msglength << strlen(msg);

   //params
   auto& params = fcgiMsg.getNewPacket();
   params.addParam("CONTENT_TYPE", "text/html; charset=UTF-8");
   params.addParam("CONTENT_LENGTH", msglength.str());
   params.buildHeader(FCGI_PARAMS, requestID);

   //terminate fcgi_param
   auto& paramterminator = fcgiMsg.getNewPacket();
   paramterminator.buildHeader(FCGI_PARAMS, requestID);

   //data
   //TODO: break down data into several FCGI_STDIN packets if length > UINT16_MAX
   auto& data = fcgiMsg.getNewPacket();
   data.addData(msg, strlen(msg));
   data.buildHeader(FCGI_STDIN, requestID);

   //terminate fcgi_stdin
   auto& dataterminator = fcgiMsg.getNewPacket();
   dataterminator.buildHeader(FCGI_STDIN, requestID);

   return fcgiMsg;
}

///////////////////////////////////////////////////////////////////////////////
string FcgiSocket::getMessage(const char* msg)
{
   /***
   TODO: check fcgi header content
   ***/

   //get rid of first 8 bytes fcgi header, then strip http header
   auto&& httpbody = HttpSocket::getMessage(msg + 8);

   //check for fcgi_end_request packet

   return httpbody;
}

///////////////////////////////////////////////////////////////////////////////
string FcgiSocket::writeAndRead(const string& msg)
{
   auto sockfd = this->open();

   auto&& fcgiMsg = makePacket(msg.c_str());
   auto serdata = fcgiMsg.serialize();
   auto serdatalength = fcgiMsg.getSerializedDataLength();

   this->write(sockfd, (char*)serdata, serdatalength);

   char* retval = this->read(sockfd);
   auto&& retmsg = getMessage(retval);

   this->close(sockfd);
   delete[] retval;
   fcgiMsg.clear();

   return retmsg;
}
