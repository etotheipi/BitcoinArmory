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

enum BDMPhase
{
   BDMPhase_DBHeaders=1,
   BDMPhase_OrganizingChain,
   BDMPhase_BlockHeaders,
   BDMPhase_BlockData,
   BDMPhase_Rescan
};

enum BDMAction
{
   BDMAction_Ready=1,
   BDMAction_NewBlock,
   BDMAction_ZC,
   BDMAction_Refresh,
   BDMAction_Exited,
   BDMAction_ErrorMsg,
   BDMAction_StartedWalletScan
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

#endif
