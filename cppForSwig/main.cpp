#include <string>
#include <iostream>
#include <sstream>


using namespace std;

#include "BlockDataManagerConfig.h"
#include "BDM_mainthread.h"
#include "BDM_Server.h"

int main(int argc, char* argv[])
{
   ScrAddrFilter::init();

   BlockDataManagerConfig bdmConfig;
   bdmConfig.parseArgs(argc, argv);
   
   cout << "logging in " << bdmConfig.logFilePath_ << endl;
   STARTLOGGING(bdmConfig.logFilePath_, LogLvlDebug);
   LOGENABLESTDOUT();

   LOGINFO << "Running on " << bdmConfig.threadCount_ << " threads";
   LOGINFO << "Ram usage level: " << bdmConfig.ramUsage_;

   if (FCGX_Init())
      throw runtime_error("failed to initialize FCGI engine");


   BlockDataManagerThread bdmThread(bdmConfig);
   FCGI_Server server(&bdmThread, bdmConfig.fcgiPort_);
   
   if (!bdmConfig.checkChain_)
   {
      //start listening
      server.checkSocket();
      server.init();
   }

   //start db init
   bdmThread.start(bdmConfig.initMode_);

   //create cookie file if applicable
   bdmConfig.createCookie();
   
   if (!bdmConfig.checkChain_)
   {
      //process incoming connections
      server.enterLoop();
   }
   else
   {
      bdmThread.join();
   }

   //stop all threads and clean up
   server.shutdown();

   return 0;
}
