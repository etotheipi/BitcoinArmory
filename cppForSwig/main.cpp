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

int main(int argc, char* argv[])
{

   DataMeta::initTypeMap();
   ScrAddrFilter::init();

   BlockDataManagerConfig bdmConfig;
   bdmConfig.parseArgs(argc, argv);
   
   STARTLOGGING(bdmConfig.logFilePath_, LogLvlDebug);
   LOGENABLESTDOUT();

   LOGINFO << "Running on " << bdmConfig.threadCount_ << " threads";
   LOGINFO << "Ram usage level: " << bdmConfig.ramUsage_;

   if (FCGX_Init())
      throw runtime_error("failed to initialize FCGI engine");

   BlockDataManagerThread bdmThread(bdmConfig);

   //get mode from bdmConfig and start BDM maintenance thread
   bdmThread.start(bdmConfig.initMode_);

   FCGI_Server server(&bdmThread);
   server.init();
   server.enterLoop();

   //stop all threads and clean up
   server.shutdown();

   return 0;
}
