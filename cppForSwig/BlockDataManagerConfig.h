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

#ifndef BLOCKDATAMANAGERCONFIG_H
#define BLOCKDATAMANAGERCONFIG_H

#include <exception>
#include <thread>
#include "bdmenums.h"
#include "BinaryData.h"
#include <tuple>
#include <list>

#ifdef _WIN32
#include <ShlObj.h>
#else
#include <wordexp.h>
#endif

#define DEFAULT_ZCTHREAD_COUNT 100

////////////////////////////////////////////////////////////////////////////////
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
   
   BinaryData genesisBlockHash_;
   BinaryData genesisTxHash_;
   BinaryData magicBytes_;

   NodeType nodeType_ = Node_BTC;
   string btcPort_;
   string fcgiPort_;
   bool listen_all_ = false;
   string rpcPort_;

   bool customFcgiPort_ = false;


   unsigned ramUsage_ = 50;
   unsigned threadCount_ = thread::hardware_concurrency();
   unsigned zcThreadCount_ = DEFAULT_ZCTHREAD_COUNT;

   exception_ptr exceptionPtr_ = nullptr;

   bool reportProgress_ = true;

   bool checkChain_ = false;
   bool clearMempool_ = false;

   const string cookie_;
   bool useCookie_ = false;

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

   void processArgs(const map<string, string>&, bool);
   void parseArgs(int argc, char* argv[]);
   void createCookie(void) const;
   void printHelp(void);
   static string portToString(unsigned);

   static void appendPath(string& base, const string& add);
   static void expandPath(string& path);

   static vector<string> getLines(const string& path);
   static map<string, string> getKeyValsFromLines(
      const vector<string>&, char delim);
   static pair<string, string> getKeyValFromLine(const string&, char delim);
   static string stripQuotes(const string& input);
   static vector<string> keyValToArgv(const map<string, string>&);
   
   static bool testConnection(const string& ip, const string& port);
   static string hasLocalDB(const string& datadir, const string& port);
   static string getPortFromCookie(const string& datadir);
   static string getCookie(const string& datadir);
};

////
enum NodeStatus
{
   NodeStatus_Offline,
   NodeStatus_Online,
   NodeStatus_OffSync
};

////
enum RpcStatus
{
   RpcStatus_Disabled,
   RpcStatus_BadAuth,
   RpcStatus_Online,
   RpcStatus_Error_28
};

////
enum ChainStatus
{
   ChainStatus_Unknown,
   ChainStatus_Syncing,
   ChainStatus_Ready
};

struct JSON_object;

////////////////////////////////////////////////////////////////////////////////
class NodeChainState
{
   friend class NodeRPC;

private:
   list<tuple<unsigned, uint64_t, uint64_t> > heightTimeVec_;
   ChainStatus state_ = ChainStatus_Unknown;
   float blockSpeed_ = 0.0f;
   uint64_t eta_ = 0;
   float pct_ = 0.0f;
   unsigned blocksLeft_ = 0;

   unsigned prev_pct_int_ = 0;

private:
   //so that SWIG 2.0 doesn't try to parse a shared_ptr object (and choke)
   bool processState(shared_ptr<JSON_object> const getblockchaininfo_obj);

public:
   void appendHeightAndTime(unsigned, uint64_t);
   unsigned getTopBlock(void) const;
   ChainStatus state(void) const { return state_; }
   float getBlockSpeed(void) const { return blockSpeed_; }

   BinaryData serialize(void) const;
   void unserialize(const BinaryData&);

   void reset();
   
   float getProgressPct(void) const { return pct_; }
   uint64_t getETA(void) const { return eta_; }
   unsigned getBlocksLeft(void) const { return blocksLeft_; }
};

////////////////////////////////////////////////////////////////////////////////
struct NodeStatusStruct
{
   NodeStatus status_ = NodeStatus_Offline;
   bool SegWitEnabled_ = false;
   RpcStatus rpcStatus_ = RpcStatus_Disabled;
   NodeChainState chainState_;

   BinaryData serialize(void) const;
   void deserialize(const BinaryData&);

   //casting nastiness for python callbacks arg conversion until I 
   //shove it all on the cpp side
   static NodeStatusStruct cast_to_NodeStatusStruct(void* ptr);
};

////////////////////////////////////////////////////////////////////////////////
struct ConfigFile
{
   map<string, string> keyvalMap_;

   ConfigFile(const string& path);

   static vector<BinaryData> fleshOutArgs(
      const string& path, const vector<BinaryData>& argv);
};

////////////////////////////////////////////////////////////////////////////////
struct BDV_Error_Struct
{
   string errorStr_;
   BDV_ErrorType errType_;
   string extraMsg_;

   BinaryData serialize(void) const;
   void deserialize(const BinaryData&);

   static BDV_Error_Struct cast_to_BDVErrorStruct(void* ptr);
};

#endif
// kate: indent-width 3; replace-tabs on;
