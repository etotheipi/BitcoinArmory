////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "StringSockets.h"

///////////////////////////////////////////////////////////////////////////////
//
// HttpSocket
//
///////////////////////////////////////////////////////////////////////////////
HttpSocket::HttpSocket(const BinarySocket& obj) :
BinarySocket(obj)
{
   stringstream ss;
   ss << "POST / HTTP/1.1" << "\r\n";
   ss << "Host: " << addr_ << "\r\n";
   ss << "Content-type: text/html; charset=UTF-8" << "\r\n";
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

   return pos;
}

///////////////////////////////////////////////////////////////////////////////
string HttpSocket::getBody(vector<uint8_t> msg)
{
   /***
   Always expect text data (null terminated)
   ***/

   //look for double crlf http header end, return everything after that
   typedef vector<uint8_t>::iterator vcIter;

   //let's use a move iterator, enough copies already as it is
   string htmlstr(
      move_iterator<vcIter>(msg.begin()),
      move_iterator<vcIter>(msg.end()));

   size_t pos = htmlstr.find("\r\n\r\n");
   if (pos == string::npos)
   {
      //no html break, check for error marker
      pos = htmlstr.find("error:");
      if (pos != string::npos)
         throw runtime_error(htmlstr);

      throw runtime_error("unexpected return value");
   }

   return htmlstr.substr(pos + 4);
}

///////////////////////////////////////////////////////////////////////////////
string HttpSocket::writeAndRead(const string msg, SOCKET sockfd)
{

   char* packet = nullptr;
   auto packetSize = makePacket(&packet, msg.c_str());

   typedef vector<char>::iterator vecIterType;

   auto packetPtr = make_shared<packetData>();

   while (1)
   {
      if (sockfd == SOCK_MAX)
         sockfd = openSocket(false);

      if (sockfd == SOCK_MAX)
         throw SocketError("failed to connect socket");

      packetPtr->clear();

      try
      {
         auto readPromise = make_shared<promise<bool>>();
         auto waitOnRead = readPromise->get_future();

         auto processHttpPacket = [readPromise, packetPtr]
            (vector<uint8_t> socketData, exception_ptr ePtr)->bool
         {
            try
            {
               auto& httpData = packetPtr->httpData;

               if (socketData.size() == 0 && ePtr)
               {
                  readPromise->set_value(true);
                  return true;
               }

         {
            httpData.insert(
               httpData.end(), socketData.begin(), socketData.end());

            if (packetPtr->content_length == -1)
            {
               //if content_length is -1, we have not read the content-length in the
               //http header yet, let's find that
               for (unsigned i = 0; i < httpData.size(); i++)
               {
                  if (httpData[i] == '\r')
                  {
                     if (httpData.size() - i < 3)
                        break;

                     if (httpData[i + 1] == '\n' &&
                        httpData[i + 2] == '\r' &&
                        httpData[i + 3] == '\n')
                     {
                        packetPtr->header_len = i + 4;
                        break;
                     }
                  }
               }

               if (packetPtr->header_len == 0)
                  throw HttpError("couldn't find http header in response");

               string header_str((char*)&httpData[0], packetPtr->header_len);
               packetPtr->get_content_len(header_str);
            }

            if (packetPtr->content_length == -1)
               throw HttpError("failed to find http header response packet");

            //check the total amount of data read matches the advertised
            //data in the http header
         }

         bool done = false;
         if (httpData.size() >= packetPtr->content_length + packetPtr->header_len)
         {
            httpData.resize(packetPtr->content_length + packetPtr->header_len);
            done = true;
         }

         if (ePtr != nullptr)
         {
            readPromise->set_exception(ePtr);
            done = true;
         }
         else if (done)
         {
            readPromise->set_value(true);
         }

         return done;
            }
            catch (...)
            {
               readPromise->set_exception(current_exception());
               return true;
            }
         };

         writeToSocket(sockfd, packet, packetSize);
         readFromSocket(sockfd, processHttpPacket);

         waitOnRead.get();
         break;
      }
      catch (HttpError &e)
      {
         LOGERR << "HttpSocket::writeAndRead HttpError: " << e.what();
         continue;
      }
      catch (SocketError &e)
      {
         continue;
      }
   }

   closeSocket(sockfd);
   auto&& retmsg = getBody(move(packetPtr->httpData));

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
string FcgiSocket::writeAndRead(const string msg, SOCKET sockfd)
{

   auto&& fcgiMsg = FcgiMessage::makePacket(msg.c_str());
   auto serdata = fcgiMsg.serialize();
   auto serdatalength = fcgiMsg.getSerializedDataLength();

   auto packetPtr = make_shared<packetStruct>();
   packetPtr->fcgiid = fcgiMsg.id();

   while (1)
   {
      packetPtr->clear();
      
      if (sockfd == SOCK_MAX)
         sockfd = openSocket(false);

      if (sockfd == SOCK_MAX)
         throw SocketError("can't connect socket");

      try
      {
         auto readPromise = make_shared<promise<bool>>();
         auto waitOnRead = readPromise->get_future();

         auto processFcgiPacket =
            [readPromise, packetPtr](
            vector<uint8_t> socketData, exception_ptr ePtr)->bool
         {
            try
            {
               if (ePtr != nullptr)
               {
                  readPromise->set_exception(ePtr);
                  return true;
               }

               if (socketData.size() == 0)
               {
                  readPromise->set_value(true);
                  return true;
               }

               packetPtr->fcgidata.insert(
                  packetPtr->fcgidata.end(), socketData.begin(), socketData.end());

               while (packetPtr->ptroffset + FCGI_HEADER_LEN <=
                  packetPtr->fcgidata.size())
               {
                  //grab fcgi header
                  auto* fcgiheader = &packetPtr->fcgidata[packetPtr->ptroffset];

                  packetPtr->ptroffset += FCGI_HEADER_LEN;

                  //make sure fcgi version and request id match
                  if (fcgiheader[0] != FCGI_VERSION_1)
                     throw FcgiError("unexpected fcgi header version");

                  uint16_t requestid;
                  requestid = (uint8_t)fcgiheader[3] + (uint8_t)fcgiheader[2] * 256;
                  if (requestid != packetPtr->fcgiid)
                     throw FcgiError("request id mismatch");

                  //check packet type
                  bool abortParse = false;
                  switch (fcgiheader[1])
                  {
                  case FCGI_END_REQUEST:
                  {
                     packetPtr->endpacket++;
                     break;
                  }

                  case FCGI_STDOUT:
                  {
                     //get packetsize and padding
                     uint16_t packetsize = 0, padding;

                     packetsize |= (uint8_t)fcgiheader[5];
                     packetsize |= (uint16_t)(fcgiheader[4] << 8);
                     padding = (uint8_t)fcgiheader[6];

                     if (packetsize > 0)
                     {
                        //do not process this fcgi packet if we dont have enough
                        //data in the read buffer to cover the advertized length
                        if (packetsize + padding + packetPtr->ptroffset >
                           packetPtr->fcgidata.size())
                        {
                           packetPtr->ptroffset -= FCGI_HEADER_LEN;
                           abortParse = true;
                           break;
                        }

                        //extract http data
                        packetPtr->httpData.insert(packetPtr->httpData.end(),
                           packetPtr->fcgidata.begin() + packetPtr->ptroffset,
                           packetPtr->fcgidata.begin() + packetPtr->ptroffset + packetsize);

                        //advance index to next header
                        packetPtr->ptroffset += packetsize + padding;
                     }

                     break;
                  }

                  case FCGI_ABORT_REQUEST:
                     throw FcgiError("received FCGI_ABORT_REQUEST packet");

                     //we do not handle the other request types as a client
                  default:
                     throw FcgiError("unknown fcgi header request byte");
                  }

                  if (packetPtr->endpacket >= 1 || abortParse)
                     break;
               }

               if (packetPtr->endpacket >= 1)
               {
                  readPromise->set_value(true);
                  return true;
               }

               return false;
            }
            catch (...)
            {
               readPromise->set_exception(current_exception());
               return true;
            }

         };

         writeToSocket(sockfd, (char*)serdata, serdatalength);
         readFromSocket(sockfd, processFcgiPacket);

         waitOnRead.get();
         
         //if we got this far we're all good
         break;
      }
      catch (FcgiError &e)
      {
         LOGERR << "FcgiSocket::writeAndRead FcgiError: " << e.what();
      }
      catch (SocketError &e)
      {
         //socket error, try again
      }

      closeSocket(sockfd);
   }

   closeSocket(sockfd);
   fcgiMsg.clear();

   return HttpSocket::getBody(move(packetPtr->httpData));
}
