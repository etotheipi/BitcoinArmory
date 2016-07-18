#include <string>
#include <iostream>
#include <sstream>


using namespace std;

#include "BlockDataManagerConfig.h"
#include "BDM_mainthread.h"
#include "BDM_Server.h"


void printHelp()
{
   exit(0);
}

BlockDataManagerConfig parseArgs(int argc, char* argv[])
{
   BlockDataManagerConfig bdmConfig;

   auto stripQuotes = [](const string& input)->string
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
   };

   for (int i = 1; i < argc; i++)
   {
      istringstream ss(argv[i]);
      string str;
      getline(ss, str, '=');

      if (str == "--testnet")
      {
         bdmConfig.selectNetwork("Test");
      }
      else if (str == "--rescan")
      {
         bdmConfig.initMode = INIT_RESCAN;
      }
      else if (str == "--rebuild")
      {
         bdmConfig.initMode = INIT_REBUILD;
      }
      else if (str == "--rescanSSH")
      {
         bdmConfig.initMode = INIT_SSH;
      }
      else if (str == "--supernode")
      {
         bdmConfig.armoryDbType = ARMORY_DB_SUPER;
      }
      else
      {
         if (str == "--dbdir")
         {
            string argstr;
            getline(ss, argstr, '=');

            bdmConfig.dbLocation_ = stripQuotes(argstr);
         }
         else if (str == "--satoshi-datadir")
         {
            string argstr;
            getline(ss, argstr, '=');

            bdmConfig.blkFileLocation_ = stripQuotes(argstr);
         }
         else if (str == "--spawnId")
         {
            string argstr;
            getline(ss, argstr, '=');

            bdmConfig.spawnID_ = stripQuotes(argstr);
         }
         else
         {
            cout << "Error: bad argument syntax" << endl;
            printHelp();
         }
      }
   }

   return bdmConfig;
}

int main(int argc, char* argv[])
{
   STARTLOGGING("./dbLog.txt", LogLvlDebug);
   LOGENABLESTDOUT();

   DataMeta::initTypeMap();
   ScrAddrFilter::init();

   auto&& bdmConfig = parseArgs(argc, argv);


   if (FCGX_Init())
      throw runtime_error("failed to initialize FCGI engine");

   BlockDataManagerThread bdmThread(bdmConfig);

   //get mode from bdmConfig and start BDM maintenance thread
   bdmThread.start(bdmConfig.initMode);

   FCGI_Server server(&bdmThread);
   server.init();
   server.enterLoop();

   //stop all threads and clean up
   server.shutdown();

   return 0;
}
