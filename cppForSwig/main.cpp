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
            getline(ss, bdmConfig.dbLocation, '=');
         }
         else if (str == "--satoshi-datadir")
         {
            getline(ss, bdmConfig.blkFileLocation, '=');
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
   DataMeta::initTypeMap();

   auto&& bdmConfig = parseArgs(argc, argv);

   STARTLOGGING("./supernodeTest.txt", LogLvlDebug);
   LOGENABLESTDOUT();

   if (FCGX_Init())
      throw runtime_error("failed to initialize FCGI engine");

   BlockDataManagerThread bdmThread(bdmConfig);

   //get mode from bdmConfig and start BDM maintenance thread
   bdmThread.start(bdmConfig.initMode);

   FCGI_Server server(&bdmThread);
   server.init();
   server.enterLoop();

   //stop all threads and clean up


   return 0;
}
