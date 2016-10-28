////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef BLOCKDATAMANAGERCONFIG_H
#define BLOCKDATAMANAGERCONFIG_H

#include <exception>
#include <thread>
#include "bdmenums.h"
#include "BinaryData.h"

#ifdef _WIN32
#include <ShlObj.h>
#else
#include <wordexp.h>
#endif

struct BlockDataManagerConfig
{
   ARMORY_DB_TYPE armoryDbType_ = ARMORY_DB_FULL;
   BDM_INIT_MODE initMode_ = INIT_RESUME;

   static const string dbDirExtention_;
   static const string defaultDataDir_;
   static const string defaultBlkFileLocation_;
   static const string defaultTestnetDataDir_;
   static const string defaultTestnetBlkFileLocation_;
   static const string defaultRegtestDataDir_;
   static const string defaultRegtestBlkFileLocation_;

   string dataDir_;
   string blkFileLocation_;
   string dbDir_;

   bool testnet_ = false;
   bool regtest_ = false;

   string logFilePath_;

   string spawnID_;
   
   BinaryData genesisBlockHash_;
   BinaryData genesisTxHash_;
   BinaryData magicBytes_;

   NodeType nodeType_ = Node_BTC;
   string btcPort_;
   string fcgiPort_;


   unsigned ramUsage_ = 4;
   unsigned threadCount_ = thread::hardware_concurrency();

   exception_ptr exceptionPtr_ = nullptr;

   bool reportProgress_ = true;

   bool checkChain_ = false;

   /////////////
   static uint8_t pubkeyHashPrefix_;
   static uint8_t scriptHashPrefix_;

   /////////////
   static uint8_t getPubkeyHashPrefix(void) { return pubkeyHashPrefix_; }
   static uint8_t getScriptHashPrefix(void) { return scriptHashPrefix_; }

   /////////////
   void setGenesisBlockHash(const BinaryData &h)
   {
      genesisBlockHash_ = h;
   }
   void setGenesisTxHash(const BinaryData &h)
   {
      genesisTxHash_ = h;
   }
   void setMagicBytes(const BinaryData &h)
   {
      magicBytes_ = h;
   }

   BlockDataManagerConfig();
   void selectNetwork(const std::string &netname);

   void appendPath(string& base, const string& add);
   void parseArgs(int argc, char* argv[]);
   void printHelp(void);
   string stripQuotes(const string& input);
   static string portToString(unsigned);
};

#endif
// kate: indent-width 3; replace-tabs on;
