#ifndef BDM_MAINTHREAD_H
#define BDM_MAINTHREAD_H

#include "pthread.h"

#ifdef _MSC_VER
   #ifndef _WIN32_
      #define _WIN32_
   #endif
#endif

struct BlockDataManagerConfig;

class BDM_CallBack
{
public:
   virtual ~BDM_CallBack();
   virtual void run(int action, int arg, int block=0)=0;
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
   
   // once notify() is called, only returns on your
   // thread after run() is called
   void waitRun();
};

class BlockDataManager_LevelDB;

class BlockDataManagerThread
{
   struct BlockDataManagerThreadImpl;
   BlockDataManagerThreadImpl *pimpl;
   
public:
   BlockDataManagerThread(const BlockDataManagerConfig &config);
   ~BlockDataManagerThread();
   
   // start the BDM thread
   void start(int mode, BDM_CallBack *callback, BDM_Inject *inject);
   
   BlockDataManager_LevelDB *bdm();
   
   // stop the BDM thread
   void shutdown();

private:
   static void* thrun(void *);
   void run();

private:
   BlockDataManagerThread(const BlockDataManagerThread&);
};

// kate: indent-width 3; replace-tabs on;

#endif
