#include <string>
#include <iostream>
#include <sstream>


using namespace std;

#include "BlockDataManagerConfig.h"
#include "BDM_mainthread.h"
#include "BDM_Server.h"

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
   FCGI_Server server(&bdmThread);
   
   server.checkSocket();
   server.init();
   bdmThread.start(bdmConfig.initMode_);
   
   server.enterLoop();

   //stop all threads and clean up
   server.shutdown();

   return 0;
}
