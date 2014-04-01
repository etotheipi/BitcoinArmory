#ifndef BDM_MAINTHREAD_H
#define BDM_MAINTHREAD_H

#include "BlockUtils.h"

#ifdef _MSC_VER
   #ifndef _WIN32_
      #define _WIN32_
   #endif
#endif

class BDM_CallBack
{
public:
   virtual ~BDM_CallBack();
   virtual void run(int action, int arg)=0;
};

// let an outsider call functions from the BDM thread
class BDM_Inject
{
   struct BDM_Inject_Impl;
   BDM_Inject_Impl *pimpl;
public:
   
   BDM_Inject();
   virtual ~BDM_Inject();
   virtual void run()=0;
   
   // instruct the BDM to wake up and call run() ASAP
   void notify();
   
   // Block for 'ms' milliseconds or until someone
   // notify()es me
   void wait(unsigned ms);
};

BlockDataManager_LevelDB *startBDM(
   int mode,
   BDM_CallBack *callback,
   BDM_Inject *inject
);


#endif
