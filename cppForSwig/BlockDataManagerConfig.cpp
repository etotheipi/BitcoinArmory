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

uint8_t BlockDataManagerConfig::pubkeyHashPrefix_;
uint8_t BlockDataManagerConfig::scriptHashPrefix_;

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
BlockDataManagerConfig::BlockDataManagerConfig()
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
      btcPort_ = portToString(NODE_PORT_MAINNET);
      fcgiPort_ = portToString(FCGI_PORT_MAINNET);
      pubkeyHashPrefix_ = SCRIPT_PREFIX_HASH160;
      scriptHashPrefix_ = SCRIPT_PREFIX_P2SH;
   }
   else if (netname == "Test")
   {
      genesisBlockHash_ = READHEX(TESTNET_GENESIS_HASH_HEX);
      genesisTxHash_ = READHEX(TESTNET_GENESIS_TX_HASH_HEX);
      magicBytes_ = READHEX(TESTNET_MAGIC_BYTES);
      btcPort_ = portToString(NODE_PORT_TESTNET);
      fcgiPort_ = portToString(FCGI_PORT_TESTNET);
      pubkeyHashPrefix_ = SCRIPT_PREFIX_HASH160_TESTNET;
      scriptHashPrefix_ = SCRIPT_PREFIX_P2SH_TESTNET;

      testnet_ = true;
   }
   else if (netname == "Regtest")
   {
      genesisBlockHash_ = READHEX(REGTEST_GENESIS_HASH_HEX);
      genesisTxHash_ = READHEX(REGTEST_GENESIS_TX_HASH_HEX);
      magicBytes_ = READHEX(REGTEST_MAGIC_BYTES);
      btcPort_ = portToString(NODE_PORT_REGTEST);
      fcgiPort_ = portToString(FCGI_PORT_REGTEST);
      pubkeyHashPrefix_ = SCRIPT_PREFIX_HASH160_TESTNET;
      scriptHashPrefix_ = SCRIPT_PREFIX_P2SH_TESTNET;

      regtest_ = true;
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

   --spawnId: id as a string with which the db was spawned. Certain methods like
   shutdown require this id to proceed. Starting with an empty id makes all
   these methods unusable. Currently only used by shutdown()

   --ram_usage: defines the ram use during scan operations. 1 level averages
   128MB of ram (without accounting the base amount, ~400MB). Defaults at 4.
   Can't be lower than 1. Can be changed in between processes

   --thread-count: defines how many processing threads can be used during db
   builds and scans. Defaults to maximum available CPU threads. Can't be
   lower than 1. Can be changed in between processes

   --db-type: sets the db type:
   DB_BARE: tracks wallet history only. Smallest DB.
   DB_FULL: tracks wallet history and resolves all relevant tx hashes.
   ~750MB DB at the time of 0.95 release. Default DB type.
   DB_SUPER: tracks all blockchain history. XXL DB (100GB+).
   Not implemented yet

   db type cannot be changed in between processes. Once a db has been built
   with a certain type, it will always function according to that type.
   Specifying another type will do nothing. Build a new db to change type.

   ***/

   try
   {
      for (int i = 1; i < argc; i++)
      {
         istringstream ss(argv[i]);
         string str;
         getline(ss, str, '=');

         if (str == "--testnet")
         {
            selectNetwork("Test");
         }
         else if (str == "--regtest")
         {
            selectNetwork("Regtest");
         }
         else if (str == "--rescan")
         {
            initMode_ = INIT_RESCAN;
         }
         else if (str == "--rebuild")
         {
            initMode_ = INIT_REBUILD;
         }
         else if (str == "--rescanSSH")
         {
            initMode_ = INIT_SSH;
         }
         else if (str == "--checkchain")
         {
            checkChain_ = true;
         }
         else
         {
            if (str == "--datadir")
            {
               string argstr;
               getline(ss, argstr, '=');

               dataDir_ = stripQuotes(argstr);
            }
            else if (str == "--dbdir")
            {
               string argstr;
               getline(ss, argstr, '=');

               dbDir_ = stripQuotes(argstr);
            }
            else if (str == "--satoshi-datadir")
            {
               string argstr;
               getline(ss, argstr, '=');

               blkFileLocation_ = stripQuotes(argstr);
            }
            else if (str == "--spawnId")
            {
               string argstr;
               getline(ss, argstr, '=');

               spawnID_ = stripQuotes(argstr);
            }
            else if (str == "--db-type")
            {
               string argstr;
               getline(ss, argstr, '=');

               auto&& _str = stripQuotes(argstr);
               if (_str == "DB_BARE")
                  armoryDbType_ = ARMORY_DB_BARE;
               else if (_str == "DB_FULL")
                  armoryDbType_ = ARMORY_DB_FULL;
               else if (_str == "DB_SUPER")
                  armoryDbType_ = ARMORY_DB_SUPER;
               else
               {
                  cout << "Error: bad argument syntax" << endl;
                  printHelp();
               }
            }
            else if (str == "--ram-usage")
            {
               string argstr;
               getline(ss, argstr, '=');

               int val = 0;
               try
               {
                  val = stoi(argstr);
               }
               catch (...)
               {
               }

               if (val > 0)
                  ramUsage_ = val;
            }
            else if (str == "--thread-count")
            {
               string argstr;
               getline(ss, argstr, '=');

               int val = 0;
               try
               {
                  val = stoi(argstr);
               }
               catch (...)
               {
               }

               if (val > 0)
                  threadCount_ = val;
            }
            else
            {
               cout << "Error: bad argument syntax" << endl;
               printHelp();
            }
         }
      }

      //figure out defaults
      if (dataDir_.size() == 0)
      {
         if (!testnet_ && !regtest_)
            dataDir_ = defaultDataDir_;
         else if (!regtest_)
            dataDir_ = defaultTestnetDataDir_;
         else
            dataDir_ = defaultRegtestDataDir_;
      }

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
#endif

      //expand paths if necessary
      if (dataDir_.c_str()[0] == '~')
      {
         auto newPath = userPath;
         appendPath(newPath, dataDir_.substr(1));

         dataDir_ = move(newPath);
      }

      if (dbDir_.c_str()[0] == '~')
      {
         auto newPath = userPath;
         appendPath(newPath, dbDir_.substr(1));

         dbDir_ = move(newPath);
      }

      if (blkFileLocation_.c_str()[0] == '~')
      {
         auto newPath = userPath;
         appendPath(newPath, blkFileLocation_.substr(1));

         blkFileLocation_ = move(newPath);
      }

      if (blkFileLocation_.substr(blkFileLocation_.length() - 6, 6) != "blocks")
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
   }
   catch (...)
   {
      exceptionPtr_ = current_exception();
   }
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
