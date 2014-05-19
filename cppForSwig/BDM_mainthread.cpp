#include "BDM_mainthread.h"
#include "BlockUtils.h"
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
   
   pthread_mutex_lock(&pimpl->notifierLock);
   while (!pimpl->hasSomething)
   {
      pthread_cond_timedwait(&pimpl->notifier, &pimpl->notifierLock, &abstime); 
      
      ULONGLONG latertime = GetTickCount64();
      if (latertime >= abstime)
         break;
   }
   pthread_mutex_unlock(&pimpl->notifierLock);
#else
   struct timeval abstime;
   gettimeofday(&abstime, 0);
   abstime.tv_sec += 1;
   
   pthread_mutex_lock(&pimpl->notifierLock);
   while (!pimpl->hasSomething)
   {
      struct timespec abstimets;
      abstimets.tv_sec = abstime.tv_sec;
      abstimets.tv_nsec = abstime.tv_usec*1000;
      pthread_cond_timedwait(&pimpl->notifier, &pimpl->notifierLock, &abstimets); 
      
      unsigned mselapsed;
      struct timeval latertime;
      gettimeofday(&latertime, 0);
      if (latertime.tv_sec >= abstime.tv_sec && latertime.tv_usec >= abstime.tv_usec)
         break;
   }
   pthread_mutex_unlock(&pimpl->notifierLock);
#endif
}

static void* run(void *_threadparams)
{
   ThreadParams *const threadparams = static_cast<ThreadParams*>(_threadparams);
   BlockDataManager_LevelDB *const bdm = threadparams->bdm;
   
   BDM_CallBack *const callback = threadparams->callback;

   //don't call this unless you're trying to get online
   if(threadparams->mode==0) threadparams->bdm->doInitialSyncOnLoad();
   else if(threadparams->mode==1) threadparams->bdm->doInitialSyncOnLoad_Rescan();
   else if(threadparams->mode==2) threadparams->bdm->doInitialSyncOnLoad_Rebuild();

   //push 'bdm is ready' to Python
   callback->run(1, 0, threadparams->bdm->getTopBlockHeight());
   
   
   while(bdm->doRun())
   {
      uint32_t currentBlock = bdm->blockchain().top().getBlockHeight();
      if(bdm->rescanZC_)
      {
         bdm->scanWallets();
         bdm->rescanZC_ = false;

         //notify ZC
         callback->run(3, 0);
      }

      uint32_t prevTopBlk;
      if(prevTopBlk = bdm->readBlkFileUpdate())
      {
         bdm->scanWallets(prevTopBlk);

         currentBlock = bdm->blockchain().top().getBlockHeight();
         
         //notify Python that new blocks have been parsed
         callback->run(4,
            bdm->blockchain().top().getBlockHeight()
               - prevTopBlk, bdm->getTopBlockHeight()
         );
      }
      
      threadparams->inject->wait(1000);
   }

   delete bdm;
   
   delete threadparams;
   
   return 0;
}

BlockDataManager_LevelDB * createBDM(
   const BlockDataManagerConfig &config
)
{
   return new BlockDataManager_LevelDB(config);
}

void destroyBDM(BlockDataManager_LevelDB *bdm)
{
   delete bdm;
}

BlockDataManager_LevelDB * startBDM(
   BlockDataManager_LevelDB *bdm,
   int mode,
   BDM_CallBack *callback,
   BDM_Inject *inject
)
{
   ThreadParams *const tp = new ThreadParams;
   tp->bdm = bdm;
   tp->callback = callback;
   tp->inject = inject;
   tp->bdm->setRun(true);
   tp->mode = mode;
   
   //start maintenance thread
   pthread_create(&tp->tID, 0, run, tp);
   tp->bdm->setThreadParams(tp);
   
   return tp->bdm;
}

// kate: indent-width 3; replace-tabs on;

