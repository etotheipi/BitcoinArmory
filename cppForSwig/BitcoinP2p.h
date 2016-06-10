////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_BITCOINP2P
#define _H_BITCOINP2P

#include <string>
#include <mutex>
#include <future>
#include <set>
#include <stdint.h>

/***TODO: replace the use of BinaryData with self written class***/
#include "ThreadSafeClasses.h"
#include "BinaryData.h"
#include "EncryptionUtils.h"

#include "SocketIncludes.h"

using namespace std;

//reconnect constants
#define RECONNECT_INCREMENT_MS 1000

//message header
#define MESSAGE_HEADER_LEN    24
#define MAGIC_WORD_OFFSET     0
#define MESSAGE_TYPE_OFFSET   4
#define MESSAGE_TYPE_LEN      12
#define PAYLOAD_LENGTH_OFFSET 16
#define CHECKSUM_OFFSET       20

//netaddr
#define NETADDR_WITHTIME   30
#define NETADDR_NOTIME     26

#define VERSION_MINLENGTH  85
#define USERAGENT_OFFSET   80

//inv
#define INV_MAX 50000
#define INV_ENTRY_LEN 36

enum PayloadType
{
   Payload_tx = 1,
   Payload_version,
   Payload_verack,
   Payload_ping,
   Payload_pong,
   Payload_inv,
   Payload_getdata
};

enum InvType
{
   Inv_Error = 0,
   Inv_Msg_Tx,
   Inv_Msg_Block,
   Inv_Msg_Filtered_Block
};

int get_varint(uint64_t& val, uint8_t* ptr, uint32_t size);
int make_varint(const uint64_t& value, vector<uint8_t>& varint);
int get_varint_len(const int64_t& value);

////////////////////////////////////////////////////////////////////////////////
struct fdset_except_safe
{
   fd_set set_;

   fdset_except_safe(void) { zero(); }
   ~fdset_except_safe(void) { zero(); }

   void set(SOCKET sockfd) { FD_SET(sockfd, &set_); }
   void zero(void) { FD_ZERO(&set_); }
   fd_set* get(void) { return &set_; }
};

////////////////////////////////////////////////////////////////////////////////
struct BitcoinNetAddr
{
   uint64_t services_;
   char ipV6_[16]; //16 bytes long
   uint16_t port_;

   void deserialize(BinaryRefReader);
   void serialize(uint8_t* ptr) const;

   void setIPv4(uint64_t services, const sockaddr& nodeaddr)
   {
      services_ = services;
      memset(ipV6_, 0, 16);
      ipV6_[10] = (char)255;
      ipV6_[11] = (char)255;

      memcpy(ipV6_ + 12, nodeaddr.sa_data + 2, 4);
      char* portptr = (char*)&port_;
      portptr[0] = nodeaddr.sa_data[1];
      portptr[1] = nodeaddr.sa_data[0];
   }
};

////////////////////////////////////////////////////////////////////////////////
class BitcoinP2P_Exception
{
private:
   const string error_;

public:
   BitcoinP2P_Exception(const string& e) : error_(e)
   {}

   const string& what(void) const { return error_; }

};

struct SocketError : public BitcoinP2P_Exception
{
   SocketError(const string& e) : BitcoinP2P_Exception(e)
   {}
};

struct BitcoinMessageDeserError : public BitcoinP2P_Exception
{
   BitcoinMessageDeserError(const string& e) : BitcoinP2P_Exception(e)
   {}
};

struct BitcoinMessageUnknown : public BitcoinP2P_Exception
{
   BitcoinMessageUnknown(const string& e) : BitcoinP2P_Exception(e)
   {}
};

struct PayloadDeserError : public BitcoinP2P_Exception
{
   PayloadDeserError(const string& e) : BitcoinP2P_Exception(e)
   {}
};

struct GetDataException : public BitcoinP2P_Exception
{
   GetDataException(const string& e) : BitcoinP2P_Exception(e)
   {}
};

////////////////////////////////////////////////////////////////////////////////
class Payload
{
protected:
   virtual size_t serialize_inner(uint8_t*) const = 0;
  
public:
   static vector<unique_ptr<Payload>> deserialize(
      vector<uint8_t>& data, uint32_t magic_word);

public:
   virtual ~Payload() 
   {}

   virtual vector<uint8_t> serialize(uint32_t magic_word) const;

   virtual PayloadType type(void) const = 0;
   virtual string typeStr(void) const = 0;

   virtual void deserialize(uint8_t* dataptr, size_t len) = 0;
};

////
struct Payload_Version : public Payload
{
private:
   size_t serialize_inner(uint8_t*) const;

public:
   struct version_header
   {
      uint32_t version_;
      uint64_t services_;
      int64_t timestamp_;
      BitcoinNetAddr addr_recv_;
      BitcoinNetAddr addr_from_;
      uint64_t nonce_;
   };

   version_header vheader_;
   string userAgent_;
   uint32_t startHeight_;

   Payload_Version() {}
   Payload_Version(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType type(void) const { return Payload_version; }
   string typeStr(void) const { return "version"; }

   void setVersionHeaderIPv4(uint32_t version, uint64_t services,
      int64_t timestamp,
      const sockaddr& recvaddr,
      const sockaddr& fromAddr);
};

////
struct Payload_Verack : public Payload
{
private:
   size_t serialize_inner(uint8_t*) const { return 0; }

public:
   Payload_Verack() {}
   Payload_Verack(vector<uint8_t>* dataptr)
   {}

   PayloadType type(void) const { return Payload_verack; }
   string typeStr(void) const { return "verack"; }

   void deserialize(uint8_t*, size_t) {}
};

////
struct Payload_Ping : public Payload
{
private:
   size_t serialize_inner(uint8_t*) const;

public:
   uint64_t nonce_= UINT64_MAX;

public:
   Payload_Ping() {}

   Payload_Ping(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType type(void) const { return Payload_ping; }
   string typeStr(void) const { return "ping"; }
};

////
struct Payload_Pong : public Payload
{
private:
   size_t serialize_inner(uint8_t*) const;

public:
   uint64_t nonce_ = UINT64_MAX;

public:
   Payload_Pong() {}

   Payload_Pong(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType type(void) const { return Payload_pong; }
   string typeStr(void) const { return "pong"; }
};

////
struct InvEntry
{
   InvType invtype_ = Inv_Error;
   uint8_t hash[32];
};

struct Payload_Inv : public Payload
{
private:
   size_t serialize_inner(uint8_t*) const;

public:
   vector<InvEntry> invVector_;

public:
   Payload_Inv() {}

   Payload_Inv(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType type(void) const { return Payload_inv; }
   string typeStr(void) const { return "inv"; }

   void setInvVector(vector<InvEntry> invvec)
   {
      invVector_ = move(invvec);
   }
};

////
struct Payload_GetData : public Payload
{
private:
   vector<InvEntry> invVector_;

private:
   size_t serialize_inner(uint8_t*) const;

public:
   Payload_GetData() {}

   Payload_GetData(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   Payload_GetData(const InvEntry& inventry)
   {
      invVector_.push_back(inventry);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType type(void) const { return Payload_getdata; }
   string typeStr(void) const { return "getdata"; }

   const vector<InvEntry>& getInvVector(void) const
   {
      return invVector_;
   }
};

////
struct Payload_Tx : public Payload
{
private:
   vector<uint8_t> rawTx_;
   BinaryData txHash_;

private:
   size_t serialize_inner(uint8_t*) const;

public:
   Payload_Tx() {}

   Payload_Tx(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType type(void) const { return Payload_tx; }
   string typeStr(void) const { return "tx"; }

   const BinaryData& getHash256()
   {
      if (txHash_.getSize() == 0)
         txHash_ = move(BtcUtils::getHash256(&rawTx_[0], rawTx_.size()));

      return txHash_;
   }

   const vector<uint8_t>& getRawTx(void) const
   {
      return rawTx_;
   }

   void setRawTx(vector<uint8_t> rawtx)
   {
      rawTx_ = move(rawtx);
   }
};


////////////////////////////////////////////////////////////////////////////////
class BitcoinP2P
{
private:
   const string addr_v4_;
   const string port_;
   const uint32_t magic_word_;
   struct sockaddr node_addr_;
   SOCKET sockfd_ = -1;

   mutex connectMutex_, pollMutex_, writeMutex_;
   unique_ptr<promise<bool>> connectedPromise_ = nullptr;
   unique_ptr<promise<bool>> verackPromise_ = nullptr;

   //to pass payloads between the poll thread and the processing one
   BlockingStack<vector<uint8_t>> dataStack_;

   exception_ptr select_except_ = nullptr;
   exception_ptr process_except_ = nullptr;

   //callback lambdas
   Stack<function<void(const vector<InvEntry>&)>> invBlockLambdas_;
   function<void(vector<InvEntry>&)> invTxLambda_ = {};

   typedef function<void(Payload_Tx)> getTxCallback;

   //stores callback by txhash for getdata packet we send to the node
   TransactionalMap<BinaryData, getTxCallback> getTxCallbackMap_;

   //stores payloads by hash for inv packets we sent to the node,
   //expecting a getdata response

public:
   struct getDataPayload
   {
      shared_ptr<Payload> payload_;
      shared_ptr<promise<bool>> promise_;
   };

   TransactionalMap<BinaryData, getDataPayload> getDataPayloadMap_;

public:
   static const map<string, PayloadType> strToPayload_;

private:
   void connectLoop(void);

   void setBlocking(SOCKET, bool);
   void pollSocketThread();
   void processDataStackThread(void);
   void processPayload(vector<unique_ptr<Payload>>);
   
   void gotVerack(void);
   void returnVerack(void);

   void replyPong(unique_ptr<Payload>);

   void processInv(unique_ptr<Payload>);
   void processInvBlock(vector<InvEntry>);
   void processInvTx(vector<InvEntry>);
   void processGetData(unique_ptr<Payload>);
   void processGetTx(unique_ptr<Payload>);

   int64_t getTimeStamp() const;

   void registerGetTxCallback(const BinaryDataRef&, getTxCallback);
   void unregisterGetTxCallback(const BinaryDataRef&);

public:
   BitcoinP2P(const string& addr, const string& port, uint32_t magic_word);
   ~BitcoinP2P();

   void connectToNode(void);
   void sendMessage(Payload&&);

   Payload_Tx getTx(const InvEntry&, uint32_t timeout = 60);

   void registerInvBlockLambda(function<void(const vector<InvEntry>)> func)
   {
      invBlockLambdas_.push_back(move(func));
   }

   void registerInvTxLambda(function<void(vector<InvEntry>)> func)
   {
      invTxLambda_ = move(func);
   }
};

#endif
