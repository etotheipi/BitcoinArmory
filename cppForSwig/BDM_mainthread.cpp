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
      
      struct timeval latertime;
      gettimeofday(&latertime, 0);
      if (latertime.tv_sec >= abstime.tv_sec && latertime.tv_usec >= abstime.tv_usec)
         break;
   }
   pthread_mutex_unlock(&pimpl->notifierLock);
#endif
}

struct BlockDataManagerThread::BlockDataManagerThreadImpl
{
   BlockDataManager_LevelDB *bdm=nullptr;
   BDM_CallBack *callback=nullptr;
   BDM_Inject *inject=nullptr;
   pthread_t tID=0;
   int mode=0;
   volatile bool run=false;
};

BlockDataManagerThread::BlockDataManagerThread(const BlockDataManagerConfig &config)
{
   pimpl = new BlockDataManagerThreadImpl;
   pimpl->bdm = new BlockDataManager_LevelDB(config);
}

BlockDataManagerThread::~BlockDataManagerThread()
{
   if (pimpl->run)
   {
      LOGERR << "Destroying BlockDataManagerThread without shutting down first";
   }
   else
   {
      delete pimpl;
   }
}


void BlockDataManagerThread::start(int mode, BDM_CallBack *callback, BDM_Inject *inject)
{
   pimpl->callback = callback;
   pimpl->inject = inject;
   pimpl->mode = mode;
   
   pimpl->run = true;
   
   if (0 != pthread_create(&pimpl->tID, nullptr, thrun, this))
      throw std::runtime_error("Failed to start BDM thread");
}

BlockDataManager_LevelDB *BlockDataManagerThread::bdm()
{
   return pimpl->bdm;
}



// stop the BDM thread
void BlockDataManagerThread::shutdown()
{
   if (pimpl->run)
   {
      pimpl->run = false;
      pimpl->inject->notify();
      pthread_join(pimpl->tID, nullptr);
   }
}

void BlockDataManagerThread::run()
{
   BlockDataManager_LevelDB *const bdm = this->bdm();
   
   BDM_CallBack *const callback = pimpl->callback;

   //don't call this unless you're trying to get online
   if(pimpl->mode==0) bdm->doInitialSyncOnLoad();
   else if(pimpl->mode==1) bdm->doInitialSyncOnLoad_Rescan();
   else if(pimpl->mode==2) bdm->doInitialSyncOnLoad_Rebuild();

   //push 'bdm is ready' to Python
   callback->run(1, 0, bdm->getTopBlockHeight());
   
   while(pimpl->run)
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
      
      pimpl->inject->wait(1000);
   }
}

void* BlockDataManagerThread::thrun(void *_self)
{
   BlockDataManagerThread *const self
      = static_cast<BlockDataManagerThread*>(_self);
   self->run();
   return 0;
}


// kate: indent-width 3; replace-tabs on;

