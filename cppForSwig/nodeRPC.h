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
class NodeRPC : protected Lockable
{
private:
   const BlockDataManagerConfig& bdmConfig_;
   unique_ptr<HttpSocket> socket_;
   string basicAuthString_;

   //set to true if node is connected and identified
   bool goodNode_ = false; 

   NodeChainState nodeChainState_;

private:
   string getAuthString(void);
   string getDatadir(void);

public:
   NodeRPC(BlockDataManagerConfig&);
   
   RpcStatus testConnection(void);
   RpcStatus setupConnection(void);
   float getFeeByte(unsigned);
   void shutdown(void);

   bool updateChainStatus(void);
   const NodeChainState& getChainStatus(void) const;   
   void waitOnChainSync(function<void(void)>);
};

#endif