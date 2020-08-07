////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_NODERPC_
#define _H_NODERPC_

#include <mutex>
#include <memory>
#include <string>
#include <functional>

#include "SocketObject.h"
#include "StringSockets.h"
#include "BtcUtils.h"

#include "JSON_codec.h"
#include "BlockDataManagerConfig.h"

#include "ReentrantLock.h"

////////////////////////////////////////////////////////////////////////////////
struct FeeEstimateResult
{
   bool smartFee_ = false;
   float feeByte_ = 0;

   string error_;
};

////////////////////////////////////////////////////////////////////////////////
class NodeRPC : protected Lockable
{
private:
   const BlockDataManagerConfig& bdmConfig_;
   unique_ptr<HttpSocket> socket_;
   string basicAuthString_;

   //set to true if node is connected and identified
   bool goodNode_ = false; 

   NodeChainState nodeChainState_;
   function<void(void)> nodeStatusLambda_;

   RpcStatus previousState_ = RpcStatus_Disabled;

private:
   string getAuthString(void);
   string getDatadir(void);

   void callback(void)
   {
      if (nodeStatusLambda_)
         nodeStatusLambda_();
   }

public:
   NodeRPC(BlockDataManagerConfig&);
   
   RpcStatus testConnection();
   RpcStatus setupConnection(void);
   float getFeeByte(unsigned);
   FeeEstimateResult getFeeByteSmart(
      unsigned confTarget, string& strategy);
   void shutdown(void);

   bool updateChainStatus(void);
   const NodeChainState& getChainStatus(void) const;   
   void waitOnChainSync(function<void(void)>);
   string broadcastTx(const BinaryData&) const;

   void registerNodeStatusLambda(function<void(void)> lbd) { nodeStatusLambda_ = lbd; }

   virtual bool canPool(void) const { return true; }
};

////////////////////////////////////////////////////////////////////////////////
class NodeRPC_UnitTest : public NodeRPC
{
public:

   NodeRPC_UnitTest(BlockDataManagerConfig& bdmc) :
      NodeRPC(bdmc)
   {}

   bool canPool(void) const { return false; }
};

#endif