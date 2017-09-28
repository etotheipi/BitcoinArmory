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

#ifdef _WIN32
   WSADATA wsaData;
   WORD wVersion = MAKEWORD(2, 0);
   WSAStartup(wVersion, &wsaData);
#endif

   BlockDataManagerConfig bdmConfig;
   bdmConfig.parseArgs(argc, argv);
   
   cout << "logging in " << bdmConfig.logFilePath_ << endl;
   STARTLOGGING(bdmConfig.logFilePath_, LogLvlDebug);
   if (!bdmConfig.useCookie_)
      LOGENABLESTDOUT();
   else
      LOGDISABLESTDOUT();

   LOGINFO << "Running on " << bdmConfig.threadCount_ << " threads";
   LOGINFO << "Ram usage level: " << bdmConfig.ramUsage_;

   if (FCGX_Init())
      throw runtime_error("failed to initialize FCGI engine");


   //init db
   BlockDataManagerThread bdmThread(bdmConfig);
   bdmThread.start(bdmConfig.initMode_);

   //init listen loop
   FCGI_Server server(&bdmThread, bdmConfig.fcgiPort_, bdmConfig.listen_all_);
   
   if (!bdmConfig.checkChain_)
   {
      //start listening
      server.checkSocket();
      server.init();
   }


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
