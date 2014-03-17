#ifdef __linux__

#include "log.h"

#include <signal.h>
#include <execinfo.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

       
static void sigsegv(int, siginfo_t *info, void*)
{
   const int stderr=2;
   {
      const char e1[] =
         "\nArmory has crashed. Please provide the following "
         "in your bug report:\n"
         "Failed to dereference address ";
      ::write(stderr, e1, sizeof(e1)-1);
   }
   
   {
      char addr[64];
      int num = snprintf(addr, sizeof(addr), "%p", info->si_addr);
      ::write(stderr, addr, num);
      ::write(stderr, "\n", 1);
   }

   void* bt_buffer[64];
   int n = backtrace(bt_buffer, sizeof(bt_buffer)/sizeof(bt_buffer[0]));
   
   backtrace_symbols_fd(bt_buffer, n, stderr);
   
   // allow crash again, so that the user sees the pretty "Segmentation fault"
   signal(SIGSEGV, 0);
   
   // now try to write that same error to the log file
   // since Log::filename accesses what might be corrupt memory,
   // we have to repeat some of the stuff above. So it can crash
   // here and we still get a log on stderr
   int log = open(Log::filename().c_str(), O_APPEND, O_WRONLY);
   if (log != -1)
   {
      {
         const char e1[] =
            "\n\nSIGSEGV\n"
            "Failed to dereference address ";
         ::write(log, e1, sizeof(e1)-1);
      }
      {
         char addr[64];
         int num = snprintf(addr, sizeof(addr), "%p", info->si_addr);
         ::write(log, addr, num);
         ::write(log, "\n", 1);
      }
      backtrace_symbols_fd(bt_buffer, n, log);
      ::close(log);
   }
      
   // now actually crash again so the user sees the error
   
   int *crash = (int*)0;
   *crash = 0;
}

static void installSignalHandler()
{
   static bool installed=false;
   if (installed)
      return;
   installed = true;
   
   struct sigaction action;
   action.sa_sigaction = sigsegv;
   action.sa_flags = SA_SIGINFO | SA_NODEFER;
   
   sigaction(SIGSEGV, &action, 0);
}

namespace
{
class Init
{
public:
   Init()
   {
      installSignalHandler();
   }
};
}

static Init install;

// kate: indent-width 3; replace-tabs on;
#endif
