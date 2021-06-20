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

#include "TxClasses.h"
#include "SocketObject.h"

using namespace std;

//reconnect constants
#define RECONNECT_INCREMENT_MS 500

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

// Node witness
#define NODE_WITNESS 1 << 3
extern bool PEER_USES_WITNESS;

enum PayloadType
{
   Payload_tx = 1,
   Payload_version,
   Payload_verack,
   Payload_ping,
   Payload_pong,
   Payload_inv,
   Payload_getdata,
   Payload_reject,
   Payload_unknown
};

enum InvType
{
   Inv_Error = 0,
   Inv_Msg_Tx,
   Inv_Msg_Block,
   Inv_Msg_Filtered_Block,
   Inv_Terminate,
   Inv_Witness = 1 << 30,
   Inv_Msg_Witness_Tx = Inv_Msg_Tx | Inv_Witness,
   Inv_Msg_Witness_Block = Inv_Msg_Block | Inv_Witness
};

int get_varint(uint64_t& val, uint8_t* ptr, uint32_t size);
int make_varint(const uint64_t& value, vector<uint8_t>& varint);
int get_varint_len(const int64_t& value);


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
      auto ptr = (uint8_t*)nodeaddr.sa_data;
      port_ = (unsigned)ptr[0] * 256 + (unsigned)ptr[1];
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

struct BitcoinMessageDeserError : public BitcoinP2P_Exception
{
   const size_t offset_;

   BitcoinMessageDeserError(const string& e, size_t off) : 
      BitcoinP2P_Exception(e), offset_(off)
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
   static vector<size_t> processPacket(
      vector<uint8_t>& data, uint32_t magic_word);

public:
   struct DeserializedPayloads
   {
      vector<uint8_t> data_;
      vector<unique_ptr<Payload>> payloads_;
      size_t spillOffset_ = SIZE_MAX;
      int iterCount_ = 0;
   };

public:
   static shared_ptr<DeserializedPayloads> deserialize(
      vector<uint8_t>& data, uint32_t magic_word, 
      shared_ptr<DeserializedPayloads> prevPacket);

public:
   virtual ~Payload() 
   {}

   virtual vector<uint8_t> serialize(uint32_t magic_word) const;

   virtual PayloadType type(void) const = 0;
   virtual string typeStr(void) const = 0;

   virtual void deserialize(uint8_t* dataptr, size_t len) = 0;
};

////
struct Payload_Unknown : public Payload
{
private:
   vector<uint8_t> data_;

private:
   size_t serialize_inner(uint8_t*) const;

public:
   Payload_Unknown(void)
   {}

   Payload_Unknown(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType type(void) const { return Payload_unknown; }
   string typeStr(void) const { return "unknown"; }	
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
      {
         Tx thisTx(&rawTx_[0], rawTx_.size());

         txHash_ = move(thisTx.getThisHash());
      }

      return txHash_;
   }

   const vector<uint8_t>& getRawTx(void) const
   {
      return rawTx_;
   }

   void moveFrom(Payload_Tx& ptx)
   {
      rawTx_ = move(ptx.rawTx_);
   }

   void setRawTx(vector<uint8_t> rawtx)
   {
      rawTx_ = move(rawtx);
   }

   size_t getSize(void) const { return rawTx_.size(); }
};

////reject
struct Payload_Reject : public Payload
{
private:
   PayloadType rejectType_;
   char code_;
   string reasonStr_;
   vector<uint8_t> extra_;

private:
   size_t serialize_inner(uint8_t*) const 
   { throw runtime_error("not implemened"); }

public:

   Payload_Reject(void)
   {}

   Payload_Reject(uint8_t* dataptr, size_t len)
   {
      deserialize(dataptr, len);
   }

   void deserialize(uint8_t* dataptr, size_t len);

   PayloadType rejectType(void) const { return rejectType_; }
   const vector<uint8_t>& getExtra(void) const { return extra_; }
   const string& getReasonStr(void) const { return reasonStr_; }

   PayloadType type(void) const { return Payload_reject; }
   string typeStr(void) const { return "reject"; }
};

////////////////////////////////////////////////////////////////////////////////
class GetDataStatus
{
private:
   bool received_ = true;
   string msg_;

   shared_ptr<promise<shared_ptr<Payload>>> prom_;
   shared_future<shared_ptr<Payload>> fut_;


public:
   GetDataStatus(const GetDataStatus&) = delete;
   
   GetDataStatus(void)
   {
      prom_ = make_shared<promise<shared_ptr<Payload>>>();
      fut_ = prom_->get_future();
   }

   shared_future<shared_ptr<Payload>> getFuture(void) const
   {
      return fut_;
   }

   shared_ptr<promise<shared_ptr<Payload>>> getPromise(void) const
   {
      return prom_;
   }

   void setMessage(const string& message)
   {
      msg_ = message;
   }

   string getMessage(void) const { return msg_; }

   bool status(void) const { return received_; }
   void setStatus(bool st) { received_ = st; }
};

////////////////////////////////////////////////////////////////////////////////
class BitcoinP2P
{
private:
   const uint32_t magic_word_;
   struct sockaddr node_addr_;
   DedicatedBinarySocket binSocket_;

   mutex connectMutex_, pollMutex_, writeMutex_;
   unique_ptr<promise<bool>> connectedPromise_ = nullptr;
   unique_ptr<promise<bool>> verackPromise_ = nullptr;
   atomic<bool> nodeConnected_;

   //to pass payloads between the poll thread and the processing one
   shared_ptr<BlockingStack<vector<uint8_t>>> dataStack_;

   exception_ptr select_except_ = nullptr;
   exception_ptr process_except_ = nullptr;

   //callback lambdas
   Stack<function<void(const vector<InvEntry>&)>> invBlockLambdas_;
   function<void(vector<InvEntry>&)> invTxLambda_ = {};
   function<void(void)> nodeStatusLambda_;

   //stores callback by txhash for getdata packet we send to the node
   TransactionalMap<BinaryData, shared_ptr<GetDataStatus>> getTxCallbackMap_;

   atomic<bool> run_;
   future<bool> shutdownFuture_;

   uint32_t topBlock_ = UINT32_MAX;

public:
   struct getDataPayload
   {
      shared_ptr<Payload> payload_;
      shared_ptr<promise<bool>> promise_;
   };

   TransactionalMap<BinaryData, getDataPayload> getDataPayloadMap_;

public:
   static const map<string, PayloadType> strToPayload_;

protected:
   void processInvBlock(vector<InvEntry>);

private:
   void connectLoop(void);

   void pollSocketThread();
   void processDataStackThread(void);
   void processPayload(vector<unique_ptr<Payload>>);

   void checkServices(unique_ptr<Payload>);
   
   void gotVerack(void);
   void returnVerack(void);

   void replyPong(unique_ptr<Payload>);

   void processInv(unique_ptr<Payload>);
   void processInvTx(vector<InvEntry>);
   void processGetData(unique_ptr<Payload>);
   void processGetTx(unique_ptr<Payload>);
   void processReject(unique_ptr<Payload>);

   int64_t getTimeStamp() const;

   void callback(void)
   {
      if (nodeStatusLambda_)
         nodeStatusLambda_();
   }

public:
   BitcoinP2P(const string& addr, const string& port, uint32_t magic_word);
   ~BitcoinP2P();

   virtual void connectToNode(bool async);
   virtual void shutdown(void);
   void sendMessage(Payload&&);

   shared_ptr<Payload> getTx(const InvEntry&, uint32_t timeout);

   void registerInvBlockLambda(function<void(const vector<InvEntry>)> func)
   {
      if (!run_.load(memory_order_relaxed))
         throw runtime_error("node has been shutdown");

      invBlockLambdas_.push_back(move(func));
   }

   void registerInvTxLambda(function<void(vector<InvEntry>)> func)
   {
      if (!run_.load(memory_order_relaxed))
         throw runtime_error("node has been shutdown");

      invTxLambda_ = move(func);
   }

   void registerGetTxCallback(const BinaryDataRef&, shared_ptr<GetDataStatus>);
   void unregisterGetTxCallback(const BinaryDataRef&);

   bool connected(void) const { return nodeConnected_.load(memory_order_acquire); }
   bool isSegWit(void) const { return PEER_USES_WITNESS; }

   void updateNodeStatus(bool connected);
   void registerNodeStatusLambda(function<void(void)> lbd) { nodeStatusLambda_ = lbd; }
};

////////////////////////////////////////////////////////////////////////////////
class NodeUnitTest : public BitcoinP2P
{
public:
   NodeUnitTest(const string& addr, const string& port, uint32_t magic_word) :
      BitcoinP2P(addr, port, magic_word)
   {}

   void mockNewBlock(void)
   {
      InvEntry ie;
      ie.invtype_ = Inv_Msg_Block;

      vector<InvEntry> vecIE;
      vecIE.push_back(ie);

      processInvBlock(move(vecIE));
   }

   void connectToNode(bool async)
   {}

   void shutdown(void)
   {
      //clean up remaining lambdas
      vector<InvEntry> ieVec;
      InvEntry entry;
      entry.invtype_ = Inv_Terminate;
      ieVec.push_back(entry);

      processInvBlock(ieVec);
   }
};

#endif
