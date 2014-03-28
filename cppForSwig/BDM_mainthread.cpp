#include "BDM_mainthread.h"
#include "pthread.h"

#include <unistd.h>

struct ThreadParams
{
   BlockDataManager_LevelDB *bdm;
   BDM_CallBack *callback;
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

#ifdef _WIN32_
      Sleep(1);
#else
      sleep(1);
#endif
   }

   theBDM->saveScrAddrHistories();
   theBDM->reset();

   delete threadparams;
   
   return 0;
}

BlockDataManager_LevelDB * startBDM(int mode, BDM_CallBack *callback)
{
   ThreadParams *const tp = new ThreadParams;
   tp->bdm = &BlockDataManager().getBDM();
   tp->callback = callback;
   
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

