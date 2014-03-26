#include "BDM_mainthread.h"

BDM_CallBack* Caller::_callback = 0;
BlockDataManager_LevelDB *theBDM;
Caller call;

void* run(void *arg)
{
   uint32_t currentBlock = theBDM->getBlockHeight();
   uint32_t newBlocks;

   while(theBDM->doRun())
   {
      if(theBDM->rescanZC_)
      {
         theBDM->rescanWalletZeroConf();
         theBDM->rescanZC_ = false;

         //notify ZC
         call.call(3, 0);
      }

      if(newBlocks = theBDM->readBlkFileUpdate())
      {
         //scan registered tx
         theBDM->scanBlockchainForTx(currentBlock, theBDM->getBlockHeight(), true);
         theBDM->rescanWalletZeroConf();

         currentBlock = theBDM->getBlockHeight();
         
         //notify Python that new blocks have been parsed
         call.call(4, newBlocks);
      }

      Sleep(1);
   }

   theBDM->saveScrAddrHistories();
   theBDM->reset();

   return 0;
}

void startBDM(int mode)
{
   theBDM =  &(BlockDataManager().getBDM());

   //don't call this unless you're trying to get online
   if(!mode) theBDM->doInitialSyncOnLoad();
   else if(mode==1) theBDM->doInitialSyncOnLoad_Rescan();
   else if(mode==2) theBDM->doInitialSyncOnLoad_Rebuild();
   theBDM->saveScrAddrHistories();

   //push 'bdm is ready' to Python
   call.call(1, 0);

   //start maintenance thread
   pthread_t tID;
   pthread_create(&tID, 0, run, 0);
}