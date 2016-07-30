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
string HttpSocket::writeAndRead(const string& msg, SOCKET sockfd)
{
   if (sockfd == SOCK_MAX)
      sockfd = openSocket(false);

   char* packet = nullptr;
   auto packetSize = makePacket(&packet, msg.c_str());

   vector<uint8_t> retval;
   typedef vector<char>::iterator vecIterType;

   int content_length = -1;
   size_t header_len = 0;

   auto get_content_len = [&content_length](const string& header_str)
   {
      string err504("HTTP/1.1 504");
      if (header_str.compare(0, err504.size(), err504) == 0)
         throw HttpError("connection timed out");

      string search_tok_caps("Content-Length: ");
      auto tokpos = header_str.find(search_tok_caps);
      if (tokpos != string::npos)
      {
         content_length = atoi(header_str.c_str() +
            tokpos + search_tok_caps.size());
         return;
      }

      string search_tok("content-length: ");
      tokpos = header_str.find(search_tok);
      if (tokpos != string::npos)
      {
         content_length = atoi(header_str.c_str() +
            tokpos + search_tok.size());
         return;
      }
   };

   auto processHttpPacket = [&retval, &content_length, &header_len,
      get_content_len]
      (void)->bool
   {
      if (content_length == -1)
      {
         //if content_length is -1, we have not read the content-length in the
         //http header yet, let's find that
         for (unsigned i = 0; i < retval.size(); i++)
         {
            if (retval[i] == '\r')
            {
               if (retval.size() - i < 3)
                  break;

               if (retval[i + 1] == '\n' &&
                  retval[i + 2] == '\r' &&
                  retval[i + 3] == '\n')
               {
                  header_len = i + 4;
                  break;
               }
            }
         }

         if (header_len == 0)
            throw HttpError("couldn't find http header in response");

         string header_str((char*)&retval[0], header_len);
         get_content_len(header_str);
      }

      if (content_length == -1)
         throw HttpError("failed to find http header response packet");

      //check the total amount of data read matches the advertised
      //data in the http header
      if (retval.size() >= content_length + header_len)
      {
         retval.resize(content_length + header_len);
         return true;
      }

      return false;
   };

   //start select loop before we write to the socket
   auto readStack = make_shared<BlockingStack<vector<uint8_t>>>();
   try
   {
      readFromSocket(sockfd, readStack);
   }
   catch (...)
   {
      //process as much data as we got regardless of failure
   }
   
   writeToSocket(sockfd, packet, packetSize);

   try
   {
      while (1)
      {
         auto&& datavec = readStack->get();
         retval.insert(retval.end(),
            datavec.begin(), datavec.end());

         //break out of loop is we have the data we need
         if (processHttpPacket())
            break;
      }
   }
   catch (HttpError &e)
   {
      LOGERR << "HttpSocket::writeAndRead HttpError: " << e.what();
   }
   catch (IsEmpty&)
   {
      //nothing to do
   }
   catch (exception &e)
   {
      LOGERR << "HttpSocket::writeAndRead exception: " << e.what();
   }
   catch (...)
   {
      LOGERR << "HttpSocket::writeAndRead unknown exception";
   }

   closeSocket(sockfd);
   auto&& retmsg = getBody(move(retval));

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
string FcgiSocket::writeAndRead(const string& msg, SOCKET sockfd)
{
   if (msg == "10907")
      int abc = 0;
   if (msg.size() < 20)
      LOGINFO << msg;
   else
      LOGINFO << msg.substr(20);

   if (sockfd == SOCK_MAX)
      sockfd = openSocket(false);

   auto&& fcgiMsg = makePacket(msg.c_str());
   auto serdata = fcgiMsg.serialize();
   auto serdatalength = fcgiMsg.getSerializedDataLength();


   auto readStack = make_shared<BlockingStack<vector<uint8_t>>>();
   try
   {
      readFromSocket(sockfd, readStack);
   }
   catch (...)
   {
      //process as much data as we got regardless of failure
   }
   
   writeToSocket(sockfd, (char*)serdata, serdatalength);

   vector<uint8_t> fcgidata;
   vector<uint8_t> httpData;

   int endpacket = 0;
   size_t ptroffset = 0;
   auto processFcgiPacket =
      [&endpacket, &ptroffset, &fcgidata, &httpData, &fcgiMsg](void)->void
   {
      while (ptroffset + FCGI_HEADER_LEN <= fcgidata.size())
      {
         //grab fcgi header
         auto* fcgiheader = &fcgidata[ptroffset];

         ptroffset += FCGI_HEADER_LEN;

         //make sure fcgi version and request id match
         if (fcgiheader[0] != FCGI_VERSION_1)
            throw FcgiError("unexpected fcgi header version");

         uint16_t requestid;
         requestid = (uint8_t)fcgiheader[3] + (uint8_t)fcgiheader[2] * 256;
         if (requestid != fcgiMsg.id())
            throw FcgiError("request id mismatch");

         //check packet type
         switch (fcgiheader[1])
         {
         case FCGI_END_REQUEST:
         {
            endpacket++;
            return;
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
               if (packetsize + padding + ptroffset >
                  fcgidata.size())
               {
                  ptroffset -= FCGI_HEADER_LEN;
                  return;
               }

               //extract http data
               httpData.insert(httpData.end(),
                  fcgidata.begin() + ptroffset,
                  fcgidata.begin() + ptroffset + packetsize);

               //advance index to next header
               ptroffset += packetsize + padding;
            }

            break;
         }

         case FCGI_ABORT_REQUEST:
            throw FcgiError("received FCGI_ABORT_REQUEST packet");

         //we do not handle the other request types as a client
         default:
            throw FcgiError("unknown fcgi header request byte");
         }
      }
   };

   try
   {
      while (1)
      {
         auto&& datavec = readStack->get();
         fcgidata.insert(fcgidata.end(),
            datavec.begin(), datavec.end());

         //break out of loop is we have the data we need
         processFcgiPacket();
         if (endpacket >= 1)
            break;
      }
   }
   catch (FcgiError &e)
   {
      LOGERR << "FcgiSocket::writeAndRead FcgiError: " << e.what();
   }
   catch (IsEmpty&)
   {
      //nothing to do
   }
   catch (exception &e)
   {
      LOGERR << "FcgiSocket::writeAndRead exception: " << e.what();
   }
   catch (...)
   {
      LOGERR << "FcgiSocket::writeAndRead unknown exception";
   }

   closeSocket(sockfd);
   fcgiMsg.clear();

   return HttpSocket::getBody(httpData);
}
