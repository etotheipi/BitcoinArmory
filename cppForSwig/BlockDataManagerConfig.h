////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef BLOCKDATAMANAGERCONFIG_H
#define BLOCKDATAMANAGERCONFIG_H

#include "bdmenums.h"
#include "BinaryData.h"

struct BlockDataManagerConfig
{
   ARMORY_DB_TYPE armoryDbType;
   DB_PRUNE_TYPE pruneType;
   BDM_INIT_MODE initMode = INIT_RESUME;
   
   string blkFileLocation = "./";
   string dbLocation = "./";
   
   BinaryData genesisBlockHash;
   BinaryData genesisTxHash;
   BinaryData magicBytes;
   
   void setGenesisBlockHash(const BinaryData &h)
   {
      genesisBlockHash = h;
   }
   void setGenesisTxHash(const BinaryData &h)
   {
      genesisTxHash = h;
   }
   void setMagicBytes(const BinaryData &h)
   {
      magicBytes = h;
   }
   
   BlockDataManagerConfig();
   void selectNetwork(const std::string &netname);
};

#endif
// kate: indent-width 3; replace-tabs on;
