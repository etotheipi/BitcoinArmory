#ifdef __linux__

#include <signal.h>
#include <execinfo.h>
#include <unistd.h>
#include <stdio.h>

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
   
   // crash again, so that the user sees the pretty "Segmentation fault"
   signal(SIGSEGV, 0);
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
