#include "BDM_mainthread.h"

//#include <readline/readline.h>
//#include <readline/history.h>
/*
class Pager
{
   std::string pagerFile;
   std::ofstream stream_;
   pid_t child;
   
public:
   Pager()
   {
      for (int i=0; i < 1000; i++)
      {
         std::ostringstream ss;
         ss << "/tmp/armory-pager-" << getpid() << i;
      
         if (0==mkfifo(ss.str().c_str(), 0600))
         {
            pagerFile = ss.str();
            break;
         }
         else if (errno == EEXIST)
         {
            // ok
         }
         else
         {
            throw std::runtime_error("Failed to create pager fifo");
         }
      }
      
      
      child = vfork();
      if (child == 0)
      {
         execlp("less", "less", "-f", "-r", pagerFile.c_str(), nullptr);
         exit(1);
      }
      else if (child == -1)
      {
         throw std::runtime_error("Failed to run pager");
      }
      stream_.open(pagerFile);
   }
   
   std::ostream &stream() { return stream_; }
   
   ~Pager()
   {
      if (child != -1)
      {
         kill(child, SIGHUP);
         wait();
      }
   }
   
   void wait()
   {
      stream_.close();
      int r;
      waitpid(child, &r, 0);
      child=-1;
      unlink(pagerFile.c_str());
   }


};
*/
static std::string formattedBtc(uint64_t satoshis)
{
   std::ostringstream ss;
   ss << satoshis;
   std::string s = ss.str();
   s.insert(s.length()-8, ".");
   return s;
}

class Callback : public BDM_CallBack
{
public:
   bool ready=false;
   
   virtual void run(BDMAction action, void* ptr, int block=0)
   {
      if (action==BDMAction_Ready)
         ready=true;
   }
   virtual void progress(
      BDMPhase phase,
      const string &walletId,
      float progress, unsigned secondsRem,
      unsigned progressNumeric
   )
   {
   
   }
};



class Inject : public BDM_Inject
{
public:
   virtual void run()
   {
   
   }
};

int main()
{
   Log::SetLogFile("/dev/null");
   Log::SetLogLevel(LogLvlDebug4);
   
   //signal(SIGINT, SIG_IGN);
   //signal(SIGPIPE, SIG_IGN);

   BlockDataManagerConfig config;
   config.armoryDbType = ARMORY_DB_SUPER;
   config.pruneType = DB_PRUNE_NONE;
   config.blkFileLocation = std::string(getenv("HOME")) + "/.bitcoin/testnet3/blocks";
   config.levelDBLocation = "/mnt/home/charles/tmp/blockchain2";
   config.selectNetwork("Test");

   BlockDataManagerThread bdmthread(config);

   Callback cb;
   Inject in;
   bdmthread.start(0, &cb, &in);

   while (!cb.ready)
   {
      in.wait(1000);
   }
   
   bdmthread.shutdownAndWait();
   
   return 0;
}

// kate: indent-width 3; replace-tabs on;
