////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BDM_ENUMS_H
#define _BDM_ENUMS_H

#define NODE_PORT_MAINNET 8333
#define NODE_PORT_TESTNET 18333
#define NODE_PORT_REGTEST 18444

#define FCGI_PORT_MAINNET 9001
#define FCGI_PORT_TESTNET 19001
#define FCGI_PORT_REGTEST 19002

#define RPC_PORT_MAINNET 8332
#define RPC_PORT_TESTNET 18332

enum BDMPhase
{
   BDMPhase_DBHeaders = 1,
   BDMPhase_OrganizingChain,
   BDMPhase_BlockHeaders,
   BDMPhase_BlockData,
   BDMPhase_Rescan,
   BDMPhase_Balance,
   BDMPhase_SearchHashes,
   BDMPhase_ResolveHashes
};

enum BDMAction
{
   BDMAction_Ready=1,
   BDMAction_NewBlock,
   BDMAction_ZC,
   BDMAction_Refresh,
   BDMAction_Exited,
   BDMAction_ErrorMsg,
   BDMAction_NodeStatus,
   BDMAction_BDV_Error
};

enum ARMORY_DB_TYPE
{
   ARMORY_DB_BARE,
   ARMORY_DB_FULL,
   ARMORY_DB_SUPER
};

enum BDM_INIT_MODE
{
   INIT_RESUME,
   INIT_RESCAN,
   INIT_REBUILD,
   INIT_SSH
};

enum SocketType
{
   SocketBinary,
   SocketHttp,
   SocketFcgi
};

enum NodeType
{
   Node_BTC,
   Node_UnitTest
};

enum BDV_Action
{
   BDV_Init,
   BDV_NewBlock,
   BDV_Refresh,
   BDV_ZC,
   BDV_Progress,
   BDV_NodeStatus,
   BDV_Error
};

enum BDV_refresh
{
   BDV_dontRefresh,
   BDV_refreshSkipRescan,
   BDV_refreshAndRescan,
   BDV_filterChanged
};

enum BDV_ErrorType
{
   Error_ZC
};


#endif
