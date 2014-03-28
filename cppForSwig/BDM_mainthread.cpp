#include "BDM_mainthread.h"
#include "pthread.h"

#include <unistd.h>


BDM_CallBack::~BDM_CallBack()
{}

struct BDM_Inject::BDM_Inject_Impl
{
   pthread_mutex_t notifierLock;
   pthread_cond_t notifier;
   bool hasSomething;
};

BDM_Inject::BDM_Inject()
{
   pimpl = new BDM_Inject_Impl;
   pthread_mutex_init(&pimpl->notifierLock, 0);
   pthread_cond_init(&pimpl->notifier, 0);
   pimpl->hasSomething = false;
}

BDM_Inject::~BDM_Inject()
{
   pthread_mutex_destroy(&pimpl->notifierLock);
   pthread_cond_destroy(&pimpl->notifier);
   delete pimpl;
}
   
void BDM_Inject::notify()
{
   pthread_mutex_lock(&pimpl->notifierLock);
   pimpl->hasSomething=true;
   pthread_cond_signal(&pimpl->notifier);
   pthread_mutex_unlock(&pimpl->notifierLock);
}

void BDM_Inject::wait(unsigned ms)
{
#ifdef _WIN32_
   ULONGLONG abstime = GetTickCount64();
   abstime += 1000;
#else
   struct timeval abstime;
   gettimeofday(&abstime, 0);
   abstime.tv_sec += 1;
#endif
   
   pthread_mutex_lock(&pimpl->notifierLock);
   while (!pimpl->hasSomething)
   {
      struct timespec abstimets;
      abstimets.tv_sec = abstime.tv_sec;
      abstimets.tv_nsec = abstime.tv_usec*1000;
      pthread_cond_timedwait(&pimpl->notifier, &pimpl->notifierLock, &abstimets); 
      
      unsigned mselapsed;
#ifdef _WIN32_
      ULONGLONG latertime = GetTickCount64();
      if (latertime <= abstime)
         break;
#else
      struct timeval latertime;
      gettimeofday(&latertime, 0);
      if (latertime.tv_sec >= abstime.tv_sec && latertime.tv_usec >= abstime.tv_usec)
         break;
#endif
   }
   pthread_mutex_unlock(&pimpl->notifierLock);
}

struct ThreadParams
{
   BlockDataManager_LevelDB *bdm;
   BDM_CallBack *callback;
   BDM_Inject *inject;
};

static void* run(void *_threadparams)
{
   ThreadParams *const threadparams = static_cast<ThreadParams*>(_threadparams);
   BlockDataManager_LevelDB *const theBDM = threadparams->bdm;
   
   BDM_CallBack *const callback = threadparams->callback;

   while(theBDM->doRun())
   {
      uint32_t currentBlock = theBDM->getBlockHeight();
      if(theBDM->rescanZC_)
      {
         theBDM->rescanWalletZeroConf();
         theBDM->rescanZC_ = false;

         //notify ZC
         callback->run(3, 0);
      }

      uint32_t newBlocks;
      if(newBlocks = theBDM->readBlkFileUpdate())
      {
         //scan registered tx
         theBDM->scanBlockchainForTx(currentBlock, theBDM->getBlockHeight(), true);
         theBDM->rescanWalletZeroConf();

         currentBlock = theBDM->getBlockHeight();
         
         //notify Python that new blocks have been parsed
         callback->run(4, newBlocks);
      }
      
      threadparams->inject->wait(1000);

   }

   theBDM->saveScrAddrHistories();
   theBDM->reset();

   delete threadparams;
   
   return 0;
}

BlockDataManager_LevelDB * startBDM(
   int mode,
   BDM_CallBack *callback,
   BDM_Inject *inject
)
{
   ThreadParams *const tp = new ThreadParams;
   tp->bdm = &BlockDataManager().getBDM();
   tp->callback = callback;
   tp->inject = inject;
   
   //don't call this unless you're trying to get online
   if(!mode) tp->bdm->doInitialSyncOnLoad();
   else if(mode==1) tp->bdm->doInitialSyncOnLoad_Rescan();
   else if(mode==2) tp->bdm->doInitialSyncOnLoad_Rebuild();
   tp->bdm->saveScrAddrHistories();

   //push 'bdm is ready' to Python
   callback->run(1, 0);

   //start maintenance thread
   pthread_t tID;
   pthread_create(&tID, 0, run, tp);
   
   return &BlockDataManager().getBDM();
}

// kate: indent-width 3; replace-tabs on;

