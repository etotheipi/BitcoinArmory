#include "BDM_mainthread.h"
#include "BlockUtils.h"

#include <unistd.h>
#include "pthread.h"


BDM_CallBack::~BDM_CallBack()
{}

struct BDM_Inject::BDM_Inject_Impl
{
   pthread_mutex_t notifierLock;
   pthread_cond_t notifier;
   bool wantsToRun;
};

BDM_Inject::BDM_Inject()
{
   pimpl = new BDM_Inject_Impl;
   pthread_mutex_init(&pimpl->notifierLock, 0);
   pthread_cond_init(&pimpl->notifier, 0);
   pimpl->wantsToRun = false;
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
   pimpl->wantsToRun=true;
   pthread_cond_signal(&pimpl->notifier);
   pthread_mutex_unlock(&pimpl->notifierLock);
}

void BDM_Inject::wait(unsigned ms)
{
#ifdef _WIN32_
   ULONGLONG abstime = GetTickCount64();
   abstime += ms;
   
   pthread_mutex_lock(&pimpl->notifierLock);
   while (!pimpl->wantsToRun)
   {
      pthread_cond_timedwait(&pimpl->notifier, &pimpl->notifierLock, &abstime); 
      
      ULONGLONG latertime = GetTickCount64();
      if (latertime >= abstime)
         break;
   }
   if (pimpl->wantsToRun)
      run();
   pimpl->wantsToRun=false;
   pthread_cond_signal(&pimpl->notifier);
   pthread_mutex_unlock(&pimpl->notifierLock);
#else
   struct timeval abstime;
   gettimeofday(&abstime, 0);
   abstime.tv_sec += ms/1000;
   
   pthread_mutex_lock(&pimpl->notifierLock);
   while (!pimpl->wantsToRun)
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
   if (pimpl->wantsToRun)
      run();
   pimpl->wantsToRun=false;
   pthread_cond_signal(&pimpl->notifier);
   pthread_mutex_unlock(&pimpl->notifierLock);
#endif

}

void BDM_Inject::waitRun()
{
   pthread_mutex_lock(&pimpl->notifierLock);
   while (pimpl->wantsToRun)
   {
      pthread_cond_wait(&pimpl->notifier, &pimpl->notifierLock); 
   }
   pthread_mutex_unlock(&pimpl->notifierLock);
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

   {
      double lastprog=0;
      unsigned lasttime=0;
      
      const auto progress
         = [&] (double prog,unsigned time)
      {
         return;
         if (prog == lastprog && time==lasttime)
            return; // don't go to python if nothing's changed
         //callback->progress("blk", prog, time);
         lastprog = prog;
         lasttime = time;
      };
      //don't call this unless you're trying to get online
      if(pimpl->mode==0) bdm->doInitialSyncOnLoad(progress);
      else if(pimpl->mode==1) bdm->doInitialSyncOnLoad_Rescan(progress);
      else if(pimpl->mode==2) bdm->doInitialSyncOnLoad_Rebuild(progress);
   }
   
   //push 'bdm is ready' to Python
   callback->run(1, 0, bdm->getTopBlockHeight());
   
   while(pimpl->run)
   {
      if(bdm->rescanZC_)
      {
         bdm->rescanZC_ = false;
         if (bdm->parseNewZeroConfTx() == true)
         {
            bdm->scanWallets(0, 0);

            //notify ZC
            callback->run(3, 0);
         }
      }

      const uint32_t prevTopBlk = bdm->readBlkFileUpdate();
      if(prevTopBlk)
      {
         bdm->scanWallets(prevTopBlk);

         //notify Python that new blocks have been parsed
         callback->run(4,
            bdm->blockchain().top().getBlockHeight() +1
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

