////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockDataManagerConfig.h"
#include "BtcUtils.h"
#include "DBUtils.h"
#include "DbHeader.h"
#include "EncryptionUtils.h"
#include "JSON_codec.h"
#include "SocketObject.h"

#ifndef _WIN32
#include "sys/stat.h"
#endif

////////////////////////////////////////////////////////////////////////////////
//
// NodeStatusStruct
//
////////////////////////////////////////////////////////////////////////////////
uint8_t BlockDataManagerConfig::pubkeyHashPrefix_;
uint8_t BlockDataManagerConfig::scriptHashPrefix_;
string BlockDataManagerConfig::bech32Prefix_;

////////////////////////////////////////////////////////////////////////////////
const string BlockDataManagerConfig::dbDirExtention_ = "/databases";
#if defined(_WIN32)
const string BlockDataManagerConfig::defaultDataDir_ = 
   "~/Armory";
const string BlockDataManagerConfig::defaultBlkFileLocation_ = 
   "~/Bitcoin/blocks";

const string BlockDataManagerConfig::defaultTestnetDataDir_ = 
   "~/Armory/testnet3";
const string BlockDataManagerConfig::defaultTestnetBlkFileLocation_ = 
   "~/Bitcoin/testnet3/blocks";

const string BlockDataManagerConfig::defaultRegtestDataDir_ = 
   "~/Armory/regtest";
const string BlockDataManagerConfig::defaultRegtestBlkFileLocation_ = 
   "~/Bitcoin/regtest/blocks";
#elif defined(__APPLE__)
const string BlockDataManagerConfig::defaultDataDir_ = 
   "~/Library/Application Support/Armory";
const string BlockDataManagerConfig::defaultBlkFileLocation_ = 
   "~/Library/Application Support/Bitcoin/blocks";

const string BlockDataManagerConfig::defaultTestnetDataDir_ = 
   "~/Library/Application Support/Armory/testnet3";
const string BlockDataManagerConfig::defaultTestnetBlkFileLocation_ =   
   "~/Library/Application Support/Bitcoin/testnet3/blocks";

const string BlockDataManagerConfig::defaultRegtestDataDir_ = 
   "~/Library/Application Support/Armory/regtest";
const string BlockDataManagerConfig::defaultRegtestBlkFileLocation_ = 
   "~/Library/Application Support/Bitcoin/regtest/blocks";
#else
const string BlockDataManagerConfig::defaultDataDir_ = 
   "~/.armory";
const string BlockDataManagerConfig::defaultBlkFileLocation_ = 
   "~/.bitcoin/blocks";

const string BlockDataManagerConfig::defaultTestnetDataDir_ = 
   "~/.armory/testnet3";
const string BlockDataManagerConfig::defaultTestnetBlkFileLocation_ = 
   "~/.bitcoin/testnet3/blocks";

const string BlockDataManagerConfig::defaultRegtestDataDir_ = 
   "~/.armory/regtest";
const string BlockDataManagerConfig::defaultRegtestBlkFileLocation_ = 
   "~/.bitcoin/regtest/blocks";
#endif

////////////////////////////////////////////////////////////////////////////////
BlockDataManagerConfig::BlockDataManagerConfig() :
   cookie_(SecureBinaryData().GenerateRandom(32).toHexStr())
{
   selectNetwork("Main");
}

////////////////////////////////////////////////////////////////////////////////
string BlockDataManagerConfig::portToString(unsigned port)
{
   stringstream ss;
   ss << port;
   return ss.str();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManagerConfig::selectNetwork(const string &netname)
{
   if (netname == "Main")
   {
      genesisBlockHash_ = READHEX(MAINNET_GENESIS_HASH_HEX);
      genesisTxHash_ = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      magicBytes_ = READHEX(MAINNET_MAGIC_BYTES);
      rpcPort_ = portToString(RPC_PORT_MAINNET);
      pubkeyHashPrefix_ = SCRIPT_PREFIX_HASH160;
      scriptHashPrefix_ = SCRIPT_PREFIX_P2SH;
      bech32Prefix_ = "bc";
      
      if (!customFcgiPort_)
         fcgiPort_ = portToString(FCGI_PORT_MAINNET);
      
      if(!customBtcPort_)
         btcPort_ = portToString(NODE_PORT_MAINNET);
   }
   else if (netname == "Test")
   {
      genesisBlockHash_ = READHEX(TESTNET_GENESIS_HASH_HEX);
      genesisTxHash_ = READHEX(TESTNET_GENESIS_TX_HASH_HEX);
      magicBytes_ = READHEX(TESTNET_MAGIC_BYTES);
      rpcPort_ = portToString(RPC_PORT_TESTNET);
      pubkeyHashPrefix_ = SCRIPT_PREFIX_HASH160_TESTNET;
      scriptHashPrefix_ = SCRIPT_PREFIX_P2SH_TESTNET;
      bech32Prefix_ = "tb";

      testnet_ = true;
      
      if (!customFcgiPort_)
         fcgiPort_ = portToString(FCGI_PORT_TESTNET);

      if (!customBtcPort_)
         btcPort_ = portToString(NODE_PORT_TESTNET);
   }
   else if (netname == "Regtest")
   {
      genesisBlockHash_ = READHEX(REGTEST_GENESIS_HASH_HEX);
      genesisTxHash_ = READHEX(REGTEST_GENESIS_TX_HASH_HEX);
      magicBytes_ = READHEX(REGTEST_MAGIC_BYTES);
      rpcPort_ = portToString(RPC_PORT_TESTNET);
      pubkeyHashPrefix_ = SCRIPT_PREFIX_HASH160_TESTNET;
      scriptHashPrefix_ = SCRIPT_PREFIX_P2SH_TESTNET;
      bech32Prefix_ = "tb";

      regtest_ = true;
      
      if (!customFcgiPort_)
         fcgiPort_ = portToString(FCGI_PORT_REGTEST);

      if (!customBtcPort_)
         btcPort_ = portToString(NODE_PORT_REGTEST);
   }
}

////////////////////////////////////////////////////////////////////////////////
string BlockDataManagerConfig::stripQuotes(const string& input)
{
   size_t start = 0;
   size_t len = input.size();

   auto& first_char = input.c_str()[0];
   auto& last_char = input.c_str()[len - 1];

   if (first_char == '\"' || first_char == '\'')
   {
      start = 1;
      --len;
   }

   if (last_char == '\"' || last_char == '\'')
      --len;

   return input.substr(start, len);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManagerConfig::printHelp(void)
{
   //TODO: spit out arg list with description
   exit(0);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManagerConfig::parseArgs(int argc, char* argv[])
{
   /***
   --testnet: run db against testnet bitcoin network

   --regtest: run db against regression test network

   --rescan: delete all processed history data and rescan blockchain from the
   first block

   --rebuild: delete all DB data and build and scan from scratch

   --rescanSSH: delete balance and txcount data and rescan it. Much faster than
   rescan or rebuild.

   --datadir: path to the operation folder

   --dbdir: path to folder containing the database files. If empty, a new db
   will be created there

   --satoshi-datadir: path to blockchain data folder (blkXXXXX.dat files)

   --ram_usage: defines the ram use during scan operations. 1 level averages
   128MB of ram (without accounting the base amount, ~400MB). Defaults at 50.
   Can't be lower than 1. Can be changed in between processes

   --thread-count: defines how many processing threads can be used during db
   builds and scans. Defaults to maximum available CPU threads. Can't be
   lower than 1. Can be changed in between processes

   --zcthread-count: defines the maximum number on threads the zc parser can
   create for processing incoming transcations from the network node

   --db-type: sets the db type:
   DB_BARE: tracks wallet history only. Smallest DB.
   DB_FULL: tracks wallet history and resolves all relevant tx hashes.
   ~750MB DB at the time of 0.95 release. Default DB type.
   DB_SUPER: tracks all blockchain history. XXL DB (100GB+).
   Not implemented yet

   db type cannot be changed in between processes. Once a db has been built
   with a certain type, it will always function according to that type.
   Specifying another type will do nothing. Build a new db to change type.

   --cookie: create a cookie file holding a random authentication key to allow
   local clients to make use of elevated commands, like shutdown.

   --fcgi-port: sets the DB listening port.

   --clear-mempool: delete all zero confirmation transactions from the DB.

   --satoshirpc-port: set node rpc port

   --listen-all: listen to all incoming IPs (not just localhost)

   --satoshi-port: set Bitcoin node port

   ***/

   try
   {
      //parse cli args
      map<string, string> args;
      for (int i = 1; i < argc; i++)
      {
         //check prefix
         if (strlen(argv[i]) < 2)
            throw DbErrorMsg("invalid CLI arg");

         string prefix(argv[i], 2);
         if (prefix != "--")
            throw DbErrorMsg("invalid CLI arg");

         //string prefix and tokenize
         string line(argv[i] + 2);
         auto&& argkeyval = getKeyValFromLine(line, '=');
         args.insert(make_pair(
            argkeyval.first, stripQuotes(argkeyval.second)));
      }

      processArgs(args, true);

      //figure out datadir
      auto argIter = args.find("datadir");
      if (argIter != args.end())
      {
         dataDir_ = argIter->second;
         args.erase(argIter);
      }
      else
      {
         if (!testnet_ && !regtest_)
            dataDir_ = defaultDataDir_;
         else if (!regtest_)
            dataDir_ = defaultTestnetDataDir_;
         else
            dataDir_ = defaultRegtestDataDir_;
      }

      expandPath(dataDir_);

      //get datadir
      auto configPath = dataDir_;
      appendPath(configPath, "armorydb.conf");

      if (DBUtils::fileExists(configPath, 2))
      {
         ConfigFile cf(configPath);
         auto mapIter = cf.keyvalMap_.find("datadir");
         if (mapIter != cf.keyvalMap_.end())
            throw DbErrorMsg("datadir is illegal in .conf file");

         processArgs(cf.keyvalMap_, false);
      }

      processArgs(args, false);

      //figure out defaults
      bool autoDbDir = false;
      if (dbDir_.size() == 0)
      {
         dbDir_ = dataDir_;
         appendPath(dbDir_, dbDirExtention_);
         autoDbDir = true;
      }

      if (blkFileLocation_.size() == 0)
      {
         if (!testnet_)
            blkFileLocation_ = defaultBlkFileLocation_;
         else
            blkFileLocation_ = defaultTestnetBlkFileLocation_;
      }

      //expand paths if necessary
      expandPath(dbDir_);
      expandPath(blkFileLocation_);

      if (blkFileLocation_.size() < 6 ||
         blkFileLocation_.substr(blkFileLocation_.length() - 6, 6) != "blocks")
      {
         appendPath(blkFileLocation_, "blocks");
      }

      logFilePath_ = dataDir_;
      appendPath(logFilePath_, "dbLog.txt");

      //test all paths
      auto testPath = [](const string& path, int mode)
      {
         if (!DBUtils::fileExists(path, mode))
         {
            stringstream ss;
            ss << path << " is not a valid path";

            cout << ss.str() << endl;
            throw DbErrorMsg(ss.str());
         }
      };

      testPath(dataDir_, 6);

      //create dbdir if was set automatically
      if (autoDbDir)
      {
         try
         {
            testPath(dbDir_, 0);
         }
         catch (DbErrorMsg&)
         {
#ifdef _WIN32
            CreateDirectory(dbDir_.c_str(), NULL);
#else
            mkdir(dbDir_.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
#endif
         }
      }

      //now for the regular test, let it throw if it fails
      testPath(dbDir_, 6);

      testPath(blkFileLocation_, 2);

      //fcgi port
      if (useCookie_ && !customFcgiPort_)
      {
         //no custom fcgi port was provided and the db was spawned with a 
         //cookie file, fcgi port will be randomized
         srand(time(0));
         while (1)
         {
            auto port = rand() % 15000 + 49150;
            stringstream portss;
            portss << port;

            if (!testConnection("127.0.0.1", portss.str()))
            {
               fcgiPort_ = portss.str();
               break;
            }
         }
      }
   }
   catch (...)
   {
      exceptionPtr_ = current_exception();
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManagerConfig::processArgs(const map<string, string>& args, 
   bool onlyDetectNetwork)
{
   //server networking
   auto iter = args.find("fcgi-port");
   if (iter != args.end())
   {
      fcgiPort_ = stripQuotes(iter->second);
      int portInt = 0;
      stringstream portSS(fcgiPort_);
      portSS >> portInt;

      if (portInt < 1 || portInt > 65535)
      {
         cout << "Invalid fcgi port, falling back to default" << endl;
         fcgiPort_ = "";
      }
      else
      {
         customFcgiPort_ = true;
      }
   }

   iter = args.find("listen-all");
   if (iter != args.end())
   {
      listen_all_ = true;
   }

   iter = args.find("satoshi-port");
   if (iter != args.end())
   {
      btcPort_ = stripQuotes(iter->second);
      customBtcPort_ = true;
   }

   //network type
   iter = args.find("testnet");
   if (iter != args.end())
   {
      selectNetwork("Test");
   }
   else
   {
      iter = args.find("regtest");
      if (iter != args.end())
      {
         selectNetwork("Regtest");
      }
      else
      {
         selectNetwork("Main");
      }
   }

   //rpc port
   iter = args.find("satoshirpc-port");
   if (iter != args.end())
   {
      auto value = stripQuotes(iter->second);
      int portInt = 0;
      stringstream portSS(value);
      portSS >> portInt;

      if (portInt < 1 || portInt > 65535)
      {
         cout << "Invalid satoshi rpc port, falling back to default" << endl;
      }
      else
      {
         rpcPort_ = value;
      }
   }

   if (onlyDetectNetwork)
      return;

   //db init options
   iter = args.find("rescanSSH");
   if (iter != args.end())
      initMode_ = INIT_SSH;

   iter = args.find("rescan");
   if (iter != args.end())
      initMode_ = INIT_RESCAN;

   iter = args.find("rebuild");
   if (iter != args.end())
      initMode_ = INIT_REBUILD;

   iter = args.find("checkchain");
   if (iter != args.end())
      checkChain_ = true;

   iter = args.find("clear_mempool");
   if (iter != args.end())
      clearMempool_ = true;

   //db type
   iter = args.find("db-type");
   if (iter != args.end())
   {
      if (iter->second == "DB_BARE")
         armoryDbType_ = ARMORY_DB_BARE;
      else if (iter->second == "DB_FULL")
         armoryDbType_ = ARMORY_DB_FULL;
      else if (iter->second == "DB_SUPER")
         armoryDbType_ = ARMORY_DB_SUPER;
      else
      {
         cout << "Error: unexpected DB type: " << iter->second << endl;
         printHelp();
      }
   }

   //paths
   iter = args.find("datadir");
   if (iter != args.end())
      dataDir_ = stripQuotes(iter->second);

   iter = args.find("dbdir");
   if (iter != args.end())
      dbDir_ = stripQuotes(iter->second);

   iter = args.find("satoshi-datadir");
   if (iter != args.end())
      blkFileLocation_ = stripQuotes(iter->second);

   //resource control
   iter = args.find("thread-count");
   if (iter != args.end())
   {
      int val = 0;
      try
      {
         val = stoi(iter->second);
      }
      catch (...)
      {
      }

      if (val > 0)
         threadCount_ = val;
   }

   iter = args.find("ram-usage");
   if (iter != args.end())
   {
      int val = 0;
      try
      {
         val = stoi(iter->second);
      }
      catch (...)
      {
      }

      if (val > 0)
         ramUsage_ = val;
   }

   iter = args.find("zcthread-count");
   if (iter != args.end())
   {
      int val = 0;
      try
      {
         val = stoi(iter->second);
      }
      catch (...)
      {
      }

      if (val > 0)
         zcThreadCount_ = val;
   }

   //cookie
   iter = args.find("cookie");
   if (iter != args.end())
      useCookie_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManagerConfig::appendPath(string& base, const string& add)
{
   if (add.size() == 0)
      return;

   auto firstChar = add.c_str()[0];
   auto lastChar = base.c_str()[base.size() - 1];
   if (firstChar != '\\' && firstChar != '/')
      if (lastChar != '\\' && lastChar != '/')
         base.append("/");

   base.append(add);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManagerConfig::expandPath(string& path)
{
   if (path.c_str()[0] != '~')
      return;

   //resolve ~
#ifdef _WIN32
   char* pathPtr = new char[MAX_PATH + 1];
   if (SHGetFolderPath(0, CSIDL_APPDATA, 0, 0, pathPtr) != S_OK)
   {
      delete[] pathPtr;
      throw runtime_error("failed to resolve appdata path");
   }

   string userPath(pathPtr);
   delete[] pathPtr;
#else
   wordexp_t wexp;
   wordexp("~", &wexp, 0);

   for (unsigned i = 0; i < wexp.we_wordc; i++)
   {
      cout << wexp.we_wordv[i] << endl;
   }

   if (wexp.we_wordc == 0)
      throw runtime_error("failed to resolve home path");

   string userPath(wexp.we_wordv[0]);
   wordfree(&wexp);
#endif

   appendPath(userPath, path.substr(1));
   path = move(userPath);
}

////////////////////////////////////////////////////////////////////////////////
vector<string> BlockDataManagerConfig::getLines(const string& path)
{
   vector<string> output;
   fstream fs(path, ios_base::in);

   while (fs.good())
   {
      string str;
      getline(fs, str);
      output.push_back(move(str));
   }

   return output;
}

////////////////////////////////////////////////////////////////////////////////
map<string, string> BlockDataManagerConfig::getKeyValsFromLines(
   const vector<string>& lines, char delim)
{
   map<string, string> output;
   for (auto& line : lines)
      output.insert(move(getKeyValFromLine(line, delim)));

   return output;
}

////////////////////////////////////////////////////////////////////////////////
pair<string, string> BlockDataManagerConfig::getKeyValFromLine(
   const string& line, char delim)
{
   stringstream ss(line);
   pair<string, string> output;

   //key
   getline(ss, output.first, delim);

   //val
   if (ss.good())
      getline(ss, output.second);

   return output;
}

////////////////////////////////////////////////////////////////////////////////
vector<string> BlockDataManagerConfig::keyValToArgv(
   const map<string, string>& keyValMap)
{
   vector<string> argv;

   for (auto& keyval : keyValMap)
   {
      stringstream ss;
      if (keyval.first.compare(0, 2, "--") != 0)
         ss << "--";
      ss << keyval.first;

      if (keyval.second.size() != 0)
         ss << "=" << keyval.second;

      argv.push_back(ss.str());
   }

   return argv;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManagerConfig::createCookie() const
{
   //cookie file
   if (!useCookie_)
      return;

   auto cookiePath = dataDir_;
   appendPath(cookiePath, ".cookie_");
   fstream fs(cookiePath, ios_base::out | ios_base::trunc);
   fs << cookie_ << endl;
   fs << fcgiPort_;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManagerConfig::testConnection(
   const string& ip, const string& port)
{
   BinarySocket testSock(ip, port);
   return testSock.testConnection();
}

////////////////////////////////////////////////////////////////////////////////
string BlockDataManagerConfig::hasLocalDB(
   const string& datadir, const string& port)
{
   //check db on provided port
   if (testConnection("127.0.0.1", port))
      return port;

   //check db on default port
   if (testConnection("127.0.0.1", portToString(FCGI_PORT_MAINNET)))
      return portToString(FCGI_PORT_MAINNET);

   //check for cookie file
   auto&& cookie_port = getPortFromCookie(datadir);
   if (cookie_port.size() == 0)
      return string();

   if (testConnection("127.0.0.1", cookie_port))
      return cookie_port;

   return string();
}

////////////////////////////////////////////////////////////////////////////////
string BlockDataManagerConfig::getPortFromCookie(const string& datadir)
{
   //check for cookie file
   string cookie_path = datadir;
   appendPath(cookie_path, ".cookie_");
   auto&& lines = getLines(cookie_path);
   if (lines.size() != 2)
      return string();

   return lines[1];
}

////////////////////////////////////////////////////////////////////////////////
string BlockDataManagerConfig::getCookie(const string& datadir)
{
   string cookie_path = datadir;
   appendPath(cookie_path, ".cookie_");
   auto&& lines = getLines(cookie_path);
   if (lines.size() != 2)
      return string();

   return lines[0];
}

////////////////////////////////////////////////////////////////////////////////
//
// ConfigFile
//
////////////////////////////////////////////////////////////////////////////////
ConfigFile::ConfigFile(const string& path)
{
   auto&& lines = BlockDataManagerConfig::getLines(path);

   for (auto& line : lines)
   {
      auto&& keyval = BlockDataManagerConfig::getKeyValFromLine(line, '=');

      if (keyval.first.size() == 0)
         continue;

      if (keyval.first.compare(0, 1, "#") == 0)
         continue;

      keyvalMap_.insert(make_pair(
         keyval.first, BlockDataManagerConfig::stripQuotes(keyval.second)));
   }
}

////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> ConfigFile::fleshOutArgs(
   const string& path, const vector<BinaryData>& argv)
{
   //sanity check
   if (path.size() == 0)
      throw runtime_error("invalid config file path");

   //remove first arg
   auto binaryPath = argv.front();
   vector<string> arg_minus_1;

   auto argvIter = argv.begin() + 1;
   while (argvIter != argv.end())
   {
      string argStr((*argvIter).getCharPtr(), (*argvIter).getSize());
      arg_minus_1.push_back(move(argStr));
      ++argvIter;
   }

   //break down string vector
   auto&& keyValMap = BlockDataManagerConfig::getKeyValsFromLines(arg_minus_1, '=');

   //complete config file path
   string configFile_path = BlockDataManagerConfig::defaultDataDir_;
   auto datadir_iter = keyValMap.find("--datadir");
   if (datadir_iter != keyValMap.end() && datadir_iter->second.size() > 0)
      configFile_path = datadir_iter->second;

   BlockDataManagerConfig::appendPath(configFile_path, path);
   BlockDataManagerConfig::expandPath(configFile_path);

   //process config file
   ConfigFile cfile(configFile_path);
   if (cfile.keyvalMap_.size() == 0)
      return argv;

   //merge with argv
   for (auto& keyval : cfile.keyvalMap_)
   {
      //skip if argv already has this key
      stringstream argss;
      if (keyval.first.compare(0, 2, "--") != 0)
         argss << "--";
      argss << keyval.first;

      auto keyiter = keyValMap.find(argss.str());
      if (keyiter != keyValMap.end())
         continue;

      keyValMap.insert(keyval);
   }

   //convert back to string list format
   auto&& newArgs = BlockDataManagerConfig::keyValToArgv(keyValMap);

   //prepend the binary path and return
   vector<BinaryData> fleshedOutArgs;
   fleshedOutArgs.push_back(binaryPath);
   auto newArgsIter = newArgs.begin();
   while (newArgsIter != newArgs.end())
   {
      BinaryData bdStr(*newArgsIter);
      fleshedOutArgs.push_back(move(bdStr));
      ++newArgsIter;
   }

   return fleshedOutArgs;
}

////////////////////////////////////////////////////////////////////////////////
//
// NodeStatusStruct
//
////////////////////////////////////////////////////////////////////////////////
BinaryData NodeStatusStruct::serialize(void) const
{
   BinaryWriter bw;
   bw.put_uint8_t(uint8_t(status_));
   bw.put_uint8_t(uint8_t(SegWitEnabled_));
   bw.put_uint8_t(uint8_t(rpcStatus_));

   bw.put_BinaryData(chainState_.serialize());

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
void NodeStatusStruct::deserialize(const BinaryData& data)
{
   BinaryRefReader brr(data.getRef());

   status_ = NodeStatus(brr.get_uint8_t());
   SegWitEnabled_ = bool(brr.get_uint8_t());
   rpcStatus_ = RpcStatus(brr.get_uint8_t());

   chainState_.unserialize(brr.get_BinaryData(brr.getSizeRemaining()));
}

////////////////////////////////////////////////////////////////////////////////
NodeStatusStruct NodeStatusStruct::cast_to_NodeStatusStruct(void* ptr)
{
   NodeStatusStruct nss = *(NodeStatusStruct*)ptr;
   return nss;
}

////////////////////////////////////////////////////////////////////////////////
//
// NodeChainState
//
////////////////////////////////////////////////////////////////////////////////
bool NodeChainState::processState(
   shared_ptr<JSON_object> const getblockchaininfo_obj)
{
   if (state_ == ChainStatus_Ready)
      return false;

   //progress status
   auto pct_obj = getblockchaininfo_obj->getValForKey("verificationprogress");
   auto pct_val = dynamic_pointer_cast<JSON_number>(pct_obj);
   if (pct_val == nullptr)
      return false;

   pct_ = min(pct_val->val_, 1.0);
   auto pct_int = unsigned(pct_ * 10000.0);
   
   if (pct_int != prev_pct_int_)
   {
      LOGINFO << "waiting on node sync: " << float(pct_ * 100.0) << "%";
      prev_pct_int_ = pct_int;
   }

   if (pct_ >= 0.9995)
   {
      state_ = ChainStatus_Ready;
      return true;
   }

   //compare top block timestamp to now
   if (heightTimeVec_.size() == 0)
      return false;

   uint64_t now = time(0);
   uint64_t diff = 0;

   auto blocktime = get<1>(heightTimeVec_.back());
   if (now > blocktime)
      diff = now - blocktime;

   //we got this far, node is still syncing, let's compute progress and eta
   state_ = ChainStatus_Syncing;

   //average amount of blocks left to sync based on timestamp diff
   auto blocksLeft = diff / 600;

   //compute block syncing speed based off of the last 20 top blocks
   auto iterend = heightTimeVec_.rbegin();
   auto time_end = get<2>(*iterend);

   auto iterbegin = heightTimeVec_.begin();
   auto time_begin = get<2>(*iterbegin);

   if (time_end <= time_begin)
      return false;

   auto blockdiff = get<0>(*iterend) - get<0>(*iterbegin);
   if (blockdiff == 0)
      return false;

   auto timediff = time_end - time_begin;
   blockSpeed_ = float(blockdiff) / float(timediff);
   eta_ = uint64_t(float(blocksLeft) * blockSpeed_);
   
   blocksLeft_ = blocksLeft;

   return true;
}

////////////////////////////////////////////////////////////////////////////////
unsigned NodeChainState::getTopBlock() const
{
   if (heightTimeVec_.size() == 0)
      throw runtime_error("");

   return get<0>(heightTimeVec_.back());
}

////////////////////////////////////////////////////////////////////////////////
void NodeChainState::appendHeightAndTime(unsigned height, uint64_t timestamp)
{
   try
   {
      if (getTopBlock() == height)
         return;
   }
   catch (...)
   {
   }

   heightTimeVec_.push_back(make_tuple(height, timestamp, time(0)));

   //force the list at 20 max entries
   while (heightTimeVec_.size() > 20)
      heightTimeVec_.pop_front();
}

////////////////////////////////////////////////////////////////////////////////
void NodeChainState::reset()
{
   heightTimeVec_.clear();
   state_ = ChainStatus_Unknown;
   blockSpeed_ = 0.0f;
   eta_ = 0;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData NodeChainState::serialize() const
{
   BinaryWriter bw;

   bw.put_uint8_t(state_);
   bw.put_double(blockSpeed_);
   bw.put_uint64_t(eta_);
   bw.put_double(pct_);
   bw.put_uint32_t(blocksLeft_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
void NodeChainState::unserialize(const BinaryData& bd)
{
   heightTimeVec_.clear();

   BinaryRefReader brr(bd.getRef());

   state_ = ChainStatus(brr.get_uint8_t());
   blockSpeed_ = float(brr.get_double());
   eta_ = brr.get_uint64_t();
   pct_ = brr.get_double();

   if (brr.getSizeRemaining() >= 4)
      blocksLeft_ = brr.get_uint32_t();
}

////////////////////////////////////////////////////////////////////////////////
//
// BDV_Error_Struct
//
////////////////////////////////////////////////////////////////////////////////
BinaryData BDV_Error_Struct::serialize(void) const
{
   BinaryWriter bw;
   bw.put_uint8_t(errType_);

   BinaryDataRef errbdr((const uint8_t*)errorStr_.c_str(), errorStr_.size());
   bw.put_var_int(errorStr_.size());
   bw.put_BinaryData(errbdr);

   BinaryDataRef extbdr((const uint8_t*)extraMsg_.c_str(), extraMsg_.size());
   bw.put_var_int(extraMsg_.size());
   bw.put_BinaryData(extbdr);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
void BDV_Error_Struct::deserialize(const BinaryData& data)
{
   BinaryRefReader brr(data);

   errType_ = BDV_ErrorType(brr.get_uint8_t());
   
   auto len = brr.get_var_int();
   errorStr_ = move(string((char*)brr.get_BinaryDataRef(len).getPtr(), len));

   len = brr.get_var_int();
   extraMsg_ = move(string((char*)brr.get_BinaryDataRef(len).getPtr(), len));
}

////////////////////////////////////////////////////////////////////////////////
BDV_Error_Struct BDV_Error_Struct::cast_to_BDVErrorStruct(void* ptr)
{
   auto obj = (BDV_Error_Struct*)ptr;
   return *obj;
}
