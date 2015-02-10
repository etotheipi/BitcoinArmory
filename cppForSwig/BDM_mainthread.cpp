////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "BDM_mainthread.h"
#include "BlockUtils.h"
#include "BlockDataViewer.h"

#include <ctime>
#include <unistd.h>
#include "pthread.h"

BDM_CallBack::~BDM_CallBack()
{}

struct BDM_Inject::BDM_Inject_Impl
{
   pthread_mutex_t notifierLock;
   pthread_cond_t notifier;
   bool wantsToRun=false, failure=false;
};

BDM_Inject::BDM_Inject()
{
   pimpl = new BDM_Inject_Impl;
   pthread_mutex_init(&pimpl->notifierLock, 0);
   pthread_cond_init(&pimpl->notifier, 0);
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
   const bool f = pimpl->failure;
   pthread_mutex_unlock(&pimpl->notifierLock);
   
   if (f)
      throw BDMFailure();
}

void BDM_Inject::setFailureFlag()
{
   pimpl->failure = true;
}

struct BlockDataManagerThread::BlockDataManagerThreadImpl
{
   BlockDataManager_LevelDB *bdm=nullptr;
   BlockDataViewer *bdv = nullptr;
   BDM_CallBack *callback=nullptr;
   BDM_Inject *inject=nullptr;
   pthread_t tID=0;
   int mode=0;
   volatile bool run=false;
   bool failure=false;

   ~BlockDataManagerThreadImpl()
   {
      delete bdm;
      delete bdv;
   }
};

BlockDataManagerThread::BlockDataManagerThread(const BlockDataManagerConfig &config)
{
   pimpl = new BlockDataManagerThreadImpl;
   pimpl->bdm = new BlockDataManager_LevelDB(config);
   pimpl->bdv = new BlockDataViewer(pimpl->bdm);
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

BlockDataViewer* BlockDataManagerThread::bdv()
{
   return pimpl->bdv;
}

void BlockDataManagerThread::setConfig(const BlockDataManagerConfig &config)
{
   pimpl->bdm->setConfig(config);
}


// stop the BDM thread
void BlockDataManagerThread::shutdownAndWait()
{
   requestShutdown();
   
   if (pimpl->tID)
   {
      pthread_join(pimpl->tID, nullptr);
      pimpl->tID=0;

   }
}

bool BlockDataManagerThread::requestShutdown()
{
   if (pimpl->run)
   {
      pimpl->run = false;
      pimpl->inject->notify();

      return true;
   }

   return false;
}

namespace
{
class OnFinish
{
   const function<void()> fn;
public:
   OnFinish(const function<void()> &fn)
      : fn(fn) { }
   ~OnFinish()
   {
      fn();
   }
};


}


void BlockDataManagerThread::run()
try
{
   BlockDataManager_LevelDB *const bdm = this->bdm();
   BlockDataViewer *const bdv = this->bdv();
   
   BDM_CallBack *const callback = pimpl->callback;

   OnFinish onFinish(
      [callback] () { callback->run(BDMAction_Exited, nullptr); }
   );
   
   {
      tuple<BDMPhase, double, unsigned, unsigned> lastvalues;
      time_t lastProgressTime=0;
      
      class BDMStopRequest
      {
      public:
         virtual ~BDMStopRequest() { }
      };
     
      const auto loadProgress
         = [&] (BDMPhase phase, double prog,unsigned time, unsigned numericProgress)
      {
         const tuple<BDMPhase, double, unsigned, unsigned> currentvalues
            { phase, prog, time, numericProgress };
         if (currentvalues == lastvalues)
            return; // don't go to python if nothing's changed
         
         // also, don't go to the python if the phase is the same and it's been
         // less than 1 second since the last time this has been called
         // python is a lot slower than C++, so we don't want to invoke
         // the python interpreter to frequently
         const time_t currentProgressTime = std::time(nullptr);
         if (phase == get<0>(lastvalues)
            && currentProgressTime <= lastProgressTime+1
            && fabs(get<1>(lastvalues)-get<1>(currentvalues)) <= .01 )
            return;
            
         lastProgressTime = currentProgressTime;
         
         lastvalues = currentvalues;
         
         //pass empty walletID for main build&scan calls
         callback->progress(phase, vector<string>(), prog, time, numericProgress);

         if (!pimpl->run)
         {
            LOGINFO << "Stop requested detected";
            throw BDMStopRequest();
         }
         
      };
      
      try
      {
         //don't call this unless you're trying to get online
         pimpl->bdm->setNotifier(pimpl->inject);

         bdm->openDatabase();

         unsigned mode = pimpl->mode & 0x00000003;
         bool clearZc = pimpl->mode & 0x00000004;

         if (mode == 0) bdm->doInitialSyncOnLoad(loadProgress);
         else if (mode == 1) bdm->doInitialSyncOnLoad_Rescan(loadProgress);
         else if (mode == 2) bdm->doInitialSyncOnLoad_Rebuild(loadProgress);

         if (bdm->missingBlockHashes().size() || bdm->missingBlockHeaderHashes().size())
         {
            string errorMsg(
               "Armory has detected an error in the blockchain database "
               "maintained by the third-party Bitcoin software (Bitcoin-Qt "
               "or bitcoind). This error is not fatal, but may lead to "
               "incorrect balances, inability to send coins, or application "
               "instability."
               "<br><br> "
               "It is unlikely that the error affects your wallets, "
               "but it <i>is</i> possible. If you experience crashing, "
               "or see incorrect balances on any wallets, it is strongly "
               "recommended you re-download the blockchain using: "
               "<i>Help</i>\"\xe2\x86\x92\"<i>Factory Reset</i>\".");
            callback->run(BDMAction_ErrorMsg, &errorMsg, bdm->missingBlockHashes().size());
            throw;
         }

         bdv->enableZeroConf(clearZc);

         bdv->scanWallets();
      }
      catch (BDMStopRequest&)
      {
         LOGINFO << "UI asked build/scan thread to finish";
         return;
      }
   }
   
   double lastprog=0;
   unsigned lasttime=0;
   
   const auto rescanProgress
      = [&] (const vector<string>& wltIdVec, double prog,unsigned time)
   {
      if (prog == lastprog && time==lasttime)
         return; // don't go to python if nothing's changed
      //callback->progress("blk", prog, time);
      lastprog = prog;
      lasttime = time;
      
      callback->progress(
         BDMPhase_Rescan,
         wltIdVec,
         lastprog, lasttime, 0
      );
   };   
   
   //push 'bdm is ready' to Python
   callback->run(BDMAction_Ready, nullptr, bdm->getTopBlockHeight());
   
   while(pimpl->run)
   {
      bdm->getScrAddrFilter()->checkForMerge();

      if (bdm->sideScanFlag_ == true)
      {
         bdm->sideScanFlag_ = false;

         bool doScan = bdm->startSideScan(rescanProgress);
         
         vector<string> wltIDs = bdm->getNextWalletIDToScan();
         if (wltIDs.size() && doScan)
         {
            callback->run(BDMAction_StartedWalletScan, &wltIDs);
         }
      }

      if (bdm->criticalError_.size())
      {
         callback->run(BDMAction_ErrorMsg, &bdm->criticalError_);
         throw runtime_error("BDM encountered a critical error");
      }

      if(bdv->rescanZC_)
      {
         bdv->rescanZC_ = false;
         if (bdv->parseNewZeroConfTx() == true)
         {
            set<BinaryData> newZCTxHash = bdv->getNewZCTxHash();
            bdv->scanWallets();

            vector<LedgerEntry> newZCLedgers;

            for (const auto& txHash : newZCTxHash)
            {
               auto& le_w = bdv->getTxLedgerByHash_FromWallets(txHash);
               if (le_w.getTxTime() != 0)
                  newZCLedgers.push_back(le_w);

               auto& le_lb = bdv->getTxLedgerByHash_FromLockboxes(txHash);
               if (le_lb.getTxTime() != 0)
                  newZCLedgers.push_back(le_lb);
            }

            LOGINFO << newZCLedgers.size() << " new ZC Txn";
            //notify ZC
            callback->run(BDMAction_ZC, &newZCLedgers);
         }
      }

      if (bdv->refresh_ != BDV_dontRefresh)
      {
         unique_lock<mutex> lock(bdv->refreshLock_);

         BDV_refresh refresh = bdv->refresh_;
         bdv->refresh_ = BDV_dontRefresh;
         bdv->scanWallets(UINT32_MAX, UINT32_MAX, refresh);
         
         vector<BinaryData> refreshIDVec;
         for (const auto& refreshID : bdv->refreshIDSet_)
            refreshIDVec.push_back(refreshID);

         bdv->refreshIDSet_.clear();
         callback->run(BDMAction_Refresh, &refreshIDVec);
      }

      const uint32_t prevTopBlk = bdm->readBlkFileUpdate();
      if(prevTopBlk > 0)
      {
         bdv->scanWallets(prevTopBlk);

         //notify Python that new blocks have been parsed
         int nNewBlocks = bdm->blockchain().top().getBlockHeight() + 1
            - prevTopBlk;
         callback->run(BDMAction_NewBlock, &nNewBlocks,
            bdm->getTopBlockHeight()
         );
      }
      
      pimpl->inject->wait(1000);
   }
}
catch (std::exception &e)
{
   LOGERR << "BDM thread failed: " << e.what();
   string errstr(e.what());
   pimpl->callback->run(BDMAction_ErrorMsg, &errstr);
   pimpl->inject->setFailureFlag();
   pimpl->inject->notify();
}
catch (...)
{
   LOGERR << "BDM thread failed: (unknown exception)";
   pimpl->inject->setFailureFlag();
   pimpl->inject->notify();
}

void* BlockDataManagerThread::thrun(void *_self)
{
   BlockDataManagerThread *const self
      = static_cast<BlockDataManagerThread*>(_self);
   self->run();
   return 0;
}


// kate: indent-width 3; replace-tabs on;

