////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "nodeRPC.h"
#include "BlockDataManagerConfig.h"

#ifdef _WIN32
#include "leveldb_windows_port\win32_posix\dirent_win32.h"
#else
#include "dirent.h"
#endif

////////////////////////////////////////////////////////////////////////////////
//
// NodeRPC
//
////////////////////////////////////////////////////////////////////////////////
NodeRPC::NodeRPC(
   BlockDataManagerConfig& config) :
   bdmConfig_(config)
{
   socket_ = make_unique<HttpSocket>(
      BinarySocket("127.0.0.1", bdmConfig_.rpcPort_));
}

////////////////////////////////////////////////////////////////////////////////
RpcStatus NodeRPC::setupConnection()
{
   ReentrantLock lock(this);

   //test the socket
   if (!socket_->testConnection())
      return RpcStatus_Disabled;

   auto&& authString = getAuthString();
   if (authString.size() == 0)
      return RpcStatus_BadAuth;

   basicAuthString_ = move(authString);
   auto&& b64_ba = BtcUtils::base64_encode(basicAuthString_);

   socket_->resetHeaders();
   stringstream auth_header;
   auth_header << "Authorization: Basic " << b64_ba;
   socket_->addHeader(auth_header.str());

   goodNode_ = true;
   nodeChainState_.reset();

   auto status = testConnection();
   if (status == RpcStatus_Online)
      LOGINFO << "RPC connection established";

   return status;
}

////////////////////////////////////////////////////////////////////////////////
RpcStatus NodeRPC::testConnection()
{
   ReentrantLock lock(this);

   RpcStatus state = RpcStatus_Disabled;

   if (!goodNode_)
   {
      state = setupConnection();
   }
   else
   {
      goodNode_ = false;


      JSON_object json_obj;
      json_obj.add_pair("method", "getblockcount");

      try
      {
         auto&& serializedPacket = JSON_encode(json_obj);
         auto&& response = socket_->writeAndRead(serializedPacket);
         auto&& response_obj = JSON_decode(response);

         if (response_obj.isResponseValid(json_obj.id_))
         {
            goodNode_ = true;
            state = RpcStatus_Online;
         }
         else
         {
            auto error_ptr = response_obj.getValForKey("error");
            auto error_obj = dynamic_pointer_cast<JSON_object>(error_ptr);
            auto error_code_ptr = error_obj->getValForKey("code");
            auto error_code = dynamic_pointer_cast<JSON_number>(error_code_ptr);

            if (error_code == nullptr)
               throw JSON_Exception("failed to get error code");

            if ((int)error_code->val_ == -28)
            {
               state = RpcStatus_Error_28;
            }
         }
      }
      catch (SocketError&)
      {
         state = RpcStatus_Disabled;
      }
      catch (JSON_Exception& e)
      {
         LOGERR << "RPC connection test error: " << e.what();
         state = RpcStatus_BadAuth;
      }
   }

   bool doCallback = false;
   if (state != previousState_)
      doCallback = true;

   previousState_ = state;

   if (doCallback)
      callback();

   return state;
}

////////////////////////////////////////////////////////////////////////////////
string NodeRPC::getDatadir()
{
   string datadir = bdmConfig_.blkFileLocation_;
   auto len = bdmConfig_.blkFileLocation_.size();

   if (len >= 6)
   {
      auto&& term = bdmConfig_.blkFileLocation_.substr(len - 6, 6);
      if (term == "blocks")
         datadir = bdmConfig_.blkFileLocation_.substr(0, len - 6);
   }

   return datadir;
}

////////////////////////////////////////////////////////////////////////////////
string NodeRPC::getAuthString()
{
   auto&& datadir = getDatadir();

   auto confPath = datadir;
   BlockDataManagerConfig::appendPath(confPath, "bitcoin.conf");

   auto getAuthStringFromCookieFile = [&datadir](void)->string
   {
      BlockDataManagerConfig::appendPath(datadir, ".cookie");
      auto&& lines = BlockDataManagerConfig::getLines(datadir);
      if (lines.size() != 1)
      {
         throw runtime_error("unexpected cookie file content");
      }

      auto&& keyVals = BlockDataManagerConfig::getKeyValsFromLines(lines, ':');
      auto keyIter = keyVals.find("__cookie__");
      if (keyIter == keyVals.end())
      {
         throw runtime_error("unexpected cookie file content");
      }

      return lines[0];
   };

   //open and parse .conf file
   try
   {
      auto&& lines = BlockDataManagerConfig::getLines(confPath);
      auto&& keyVals = BlockDataManagerConfig::getKeyValsFromLines(lines, '=');
      
      //get rpcuser
      auto userIter = keyVals.find("rpcuser");
      if (userIter == keyVals.end())
         return getAuthStringFromCookieFile();

      string authStr = userIter->second;

      //get rpcpassword
      auto passIter = keyVals.find("rpcpassword");
      if (passIter == keyVals.end())
         return getAuthStringFromCookieFile();

      authStr.append(":");
      authStr.append(passIter->second);

      return authStr;
   }
   catch (...)
   {
      return string();
   }
}

////////////////////////////////////////////////////////////////////////////////
float NodeRPC::getFeeByte(unsigned blocksToConfirm)
{
   ReentrantLock lock(this);

   JSON_object json_obj;
   json_obj.add_pair("method", "estimatefee");

   auto json_array = make_shared<JSON_array>();
   json_array->add_value(blocksToConfirm);

   json_obj.add_pair("params", json_array);

   auto&& response = socket_->writeAndRead(JSON_encode(json_obj));
   auto&& response_obj = JSON_decode(response);

   if (!response_obj.isResponseValid(json_obj.id_))
      throw JSON_Exception("invalid response");

   auto feeByteObj = response_obj.getValForKey("result");
   auto feeBytePtr = dynamic_pointer_cast<JSON_number>(feeByteObj);

   if (feeBytePtr == nullptr)
      throw JSON_Exception("invalid response");

   return feeBytePtr->val_;
}

////////////////////////////////////////////////////////////////////////////////
FeeEstimateResult NodeRPC::getFeeByteSmart(
   unsigned confTarget, string& strategy)
{
   auto fallback = [this, &confTarget](void)->FeeEstimateResult
   {
      FeeEstimateResult fer;
      fer.smartFee_ = false;
      auto feeByteSimple = getFeeByte(confTarget);
      if (feeByteSimple == -1.0f)
         fer.error_ = "error";
      else
         fer.feeByte_ = feeByteSimple;

      return fer;
   };

   FeeEstimateResult fer;

   ReentrantLock lock(this);

   JSON_object json_obj;
   json_obj.add_pair("method", "estimatesmartfee");

   auto json_array = make_shared<JSON_array>();
   json_array->add_value(confTarget);
   if(strategy == FEE_STRAT_CONSERVATIVE || strategy == FEE_STRAT_ECONOMICAL)
      json_array->add_value(strategy);

   json_obj.add_pair("params", json_array);

   auto&& response = socket_->writeAndRead(JSON_encode(json_obj));
   auto&& response_obj = JSON_decode(response);

   if (!response_obj.isResponseValid(json_obj.id_))
      return fallback();

   auto resultPairObj = response_obj.getValForKey("result");
   auto resultPairPtr = dynamic_pointer_cast<JSON_object>(resultPairObj);

   if (resultPairPtr != nullptr)
   {
      auto feeByteObj = resultPairPtr->getValForKey("feerate");
      auto feeBytePtr = dynamic_pointer_cast<JSON_number>(feeByteObj);
      if (feeBytePtr != nullptr)
      {
         fer.feeByte_ = feeBytePtr->val_;
         fer.smartFee_ = true;

         auto blocksObj = resultPairPtr->getValForKey("blocks");
         auto blocksPtr = dynamic_pointer_cast<JSON_number>(blocksObj);

         if (blocksPtr != nullptr)
            if (blocksPtr->val_ != confTarget)
               throw JSON_Exception("conf_target mismatch");
      }
   }

   auto errorObj = response_obj.getValForKey("error");
   auto errorPtr = dynamic_pointer_cast<JSON_string>(errorObj);

   if (errorPtr != nullptr)
   {
      if (resultPairPtr == nullptr)
      {
         //fallback to the estimatefee is the method is missing
         return fallback();
      }
      else
      {
         //report smartfee error msg
         fer.error_ = errorPtr->val_;
         fer.smartFee_ = true;
      }
   }

   return fer;
}

////////////////////////////////////////////////////////////////////////////////
bool NodeRPC::updateChainStatus(void)
{
   ReentrantLock lock(this);

   //get top block header
   JSON_object json_getblockchaininfo;
   json_getblockchaininfo.add_pair("method", "getblockchaininfo");

   auto&& response = JSON_decode(
      socket_->writeAndRead(JSON_encode(json_getblockchaininfo)));
   if (!response.isResponseValid(json_getblockchaininfo.id_))
      throw JSON_Exception("invalid response");

   auto getblockchaininfo_result = response.getValForKey("result");
   auto getblockchaininfo_object = dynamic_pointer_cast<JSON_object>(
                                    getblockchaininfo_result);

   auto hash_obj = getblockchaininfo_object->getValForKey("bestblockhash");
   if (hash_obj == nullptr)
      return false;
   
   auto params_obj = make_shared<JSON_array>();
   params_obj->add_value(hash_obj);

   JSON_object json_getheader;
   json_getheader.add_pair("method", "getblockheader");
   json_getheader.add_pair("params", params_obj);

   auto&& block_header = JSON_decode(
      socket_->writeAndRead(JSON_encode(json_getheader)));

   if (!block_header.isResponseValid(json_getheader.id_))
      throw JSON_Exception("invalid response");

   auto block_header_ptr = block_header.getValForKey("result");
   auto block_header_result = dynamic_pointer_cast<JSON_object>(block_header_ptr);
   if (block_header_result == nullptr)
      throw JSON_Exception("invalid response");

   //append timestamp and height
   auto height_obj = block_header_result->getValForKey("height");
   auto height_val = dynamic_pointer_cast<JSON_number>(height_obj);
   if (height_val == nullptr)
      throw JSON_Exception("invalid response");

   auto time_obj = block_header_result->getValForKey("time");
   auto time_val = dynamic_pointer_cast<JSON_number>(time_obj);
   if (time_val == nullptr)
      throw JSON_Exception("invalid response");

   nodeChainState_.appendHeightAndTime(height_val->val_, time_val->val_);

   //figure out state
   return nodeChainState_.processState(getblockchaininfo_object);
}

////////////////////////////////////////////////////////////////////////////////
void NodeRPC::waitOnChainSync(function<void(void)> callbck)
{
   nodeChainState_.reset();
   callbck();

   while (1)
   {
      //keep trying as long as the node is initializing
      auto status = testConnection();
      if (status != RpcStatus_Error_28)
      {
         if (status != RpcStatus_Online)
            return;

         break;
      }

      //sleep for 1sec
      this_thread::sleep_for(chrono::seconds(1));
   }

   callbck();

   while (1)
   {
      float blkSpeed = 0.0f;
      try
      {
         ReentrantLock lock(this);

         if (updateChainStatus())
            callbck();

         auto& chainStatus = getChainStatus();
         if (chainStatus.state() == ChainStatus_Ready)
            break;
      
         blkSpeed = chainStatus.getBlockSpeed();
      }
      catch (...)
      {
         auto status = testConnection();
         if (status == RpcStatus_Online)
            throw runtime_error("unsupported RPC method");
      }

      unsigned dur = 1; //sleep delay in seconds

      if (blkSpeed != 0.0f)
      {
         auto singleBlkEta = max(1.0f / blkSpeed, 1.0f);
         dur = min(unsigned(singleBlkEta), unsigned(5)); //don't sleep for more than 5sec
      }

      this_thread::sleep_for(chrono::seconds(dur));
   }

   LOGINFO << "Node is ready";
}

////////////////////////////////////////////////////////////////////////////////
string NodeRPC::broadcastTx(const BinaryData& rawTx) const
{
   ReentrantLock lock(this);

   JSON_object json_obj;
   json_obj.add_pair("method", "sendrawtransaction");

   auto json_array = make_shared<JSON_array>();
   string rawTxHex = rawTx.toHexStr();
   json_array->add_value(rawTxHex);

   json_obj.add_pair("params", json_array);

   auto&& response = socket_->writeAndRead(JSON_encode(json_obj));
   auto&& response_obj = JSON_decode(response);

   string return_str;
   if (!response_obj.isResponseValid(json_obj.id_))
   {
      auto error_field = response_obj.getValForKey("error");
      auto error_obj = dynamic_pointer_cast<JSON_object>(error_field);
      if (error_obj == nullptr)
         throw JSON_Exception("invalid response");

      auto message_field = error_obj->getValForKey("message");
      auto message_val = dynamic_pointer_cast<JSON_string>(message_field);

      return_str = message_val->val_;
   }
   else
   {
      return_str = string("success");
   }

   return return_str;
}

////////////////////////////////////////////////////////////////////////////////
const NodeChainState& NodeRPC::getChainStatus(void) const
{
   ReentrantLock lock(this);
   
   return nodeChainState_;
}

////////////////////////////////////////////////////////////////////////////////
void NodeRPC::shutdown()
{
   ReentrantLock lock(this);

   JSON_object json_obj;
   json_obj.add_pair("method", "stop");

   auto&& response = socket_->writeAndRead(JSON_encode(json_obj));
   auto&& response_obj = JSON_decode(response);

   if (!response_obj.isResponseValid(json_obj.id_))
      throw JSON_Exception("invalid response");

   auto responseStr_obj = response_obj.getValForKey("result");
   auto responseStr = dynamic_pointer_cast<JSON_string>(responseStr_obj);

   if (responseStr == nullptr)
      throw JSON_Exception("invalid response");

   LOGINFO << responseStr->val_;
}
