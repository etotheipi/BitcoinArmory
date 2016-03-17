////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BDM_mainthread.h"
#include "BlockUtils.h"
#include "BlockDataViewer.h"

#include <ctime>
//#include <unistd.h>

BDM_CallBack::~BDM_CallBack()
{}

struct BlockDataManagerThread::BlockDataManagerThreadImpl
{
   BlockDataManager_LevelDB *bdm=nullptr;
   int mode=0;
   volatile bool run=false;
   bool failure=false;
   thread tID;

   ~BlockDataManagerThreadImpl()
   {
      delete bdm;
   }
};

BlockDataManagerThread::BlockDataManagerThread(const BlockDataManagerConfig &config,
   BDV_Notifier* nft) :
   notifier_(nft)
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


void BlockDataManagerThread::start(BDM_INIT_MODE mode)
{
   pimpl->mode = mode;
   pimpl->run = true;
   
   pimpl->tID = thread(thrun, this);
}

BlockDataManager_LevelDB *BlockDataManagerThread::bdm()
{
   return pimpl->bdm;
}

void BlockDataManagerThread::setConfig(const BlockDataManagerConfig &config)
{
   pimpl->bdm->setConfig(config);
}


// stop the BDM thread
void BlockDataManagerThread::shutdownAndWait()
{
   requestShutdown();
   
   if (pimpl->tID.joinable())
      pimpl->tID.join();
}

bool BlockDataManagerThread::requestShutdown()
{
   if (pimpl->run)
   {
      pimpl->run = false;
      //pimpl->inject->notify();

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
   
   //BDM_CallBack *const callback = pimpl->callback;

   /*OnFinish onFinish(
      [callback] () { callback->run(BDMAction_Exited, nullptr); }
   );*/
   
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
         //callback->progress(phase, vector<string>(), prog, time, numericProgress);

         if (!pimpl->run)
         {
            LOGINFO << "Stop requested detected";
            throw BDMStopRequest();
         }
         
      };
      
      try
      {
         //don't call this unless you're trying to get online
         //pimpl->bdm->setNotifier(pimpl->inject);

         bdm->openDatabase();

         unsigned mode = pimpl->mode & 0x00000003;
         bool clearZc = pimpl->mode & 0x00000004;

         if (mode == 0) bdm->doInitialSyncOnLoad(loadProgress);
         else if (mode == 1) bdm->doInitialSyncOnLoad_Rescan(loadProgress);
         else if (mode == 2) bdm->doInitialSyncOnLoad_Rebuild(loadProgress);
         else if (mode == 3) bdm->doInitialSyncOnLoad_RescanBalance(loadProgress);

         if (bdm->missingBlockHashes().size() || bdm->missingBlockHeaderHashes().size())
         {
            string errorMsg(
               "Armory has detected an error in the blockchain database "
               "maintained by the third-party Bitcoin software (Bitcoin-Core "
               "or bitcoind). This error is not fatal, but may lead to "
               "incorrect balances, inability to send coins, or application "
               "instability."
               "<br><br> "
               "It is unlikely that the error affects your wallets, "
               "but it <i>is</i> possible. If you experience crashing, "
               "or see incorrect balances on any wallets, it is strongly "
               "recommended you re-download the blockchain using: "
               "<i>Help</i>\"\xe2\x86\x92\"<i>Factory Reset</i>\".");
            //callback->run(BDMAction_ErrorMsg, &errorMsg, bdm->missingBlockHashes().size());
            throw;
         }

         //bdv->enableZeroConf(clearZc);

         //bdv->scanWallets();
      }
      catch (BDMStopRequest&)
      {
         LOGINFO << "UI asked build/scan thread to finish";
         return;
      }
   }
   
   topBH_ = &bdm->blockchain().top();

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
      
      /*callback->progress(
         BDMPhase_Rescan,
         wltIdVec,
         lastprog, lasttime, 0
      );*/
   };   
   
   //push 'bdm is ready' to Python
   //callback->run(BDMAction_Ready, nullptr, bdm->getTopBlockHeight());
   
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
            //callback->run(BDMAction_StartedWalletScan, &wltIDs);
         }
      }

      if (bdm->criticalError_.size())
      {
         throw runtime_error(bdm->criticalError_.c_str());
      }

      /*if(bdv->getZCflag())
      {
         bdv->flagRescanZC(false);
         auto&& newZCTxHash = bdv->parseNewZeroConfTx();
         if (newZCTxHash.size() > 0)
         {
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
      }*/

      /*if (bdv->refresh_ != BDV_dontRefresh)
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
      }*/

      const uint32_t prevTopBlk = bdm->readBlkFileUpdate();
      if(prevTopBlk > 0)
      {
         topBH_ = &bdm->blockchain().top();

         notifier_->notify();
      }
   }
}
catch (std::exception &e)
{
   LOGERR << "BDM thread failed: " << e.what();
   string errstr(e.what());
   /*pimpl->callback->run(BDMAction_ErrorMsg, &errstr);
   pimpl->inject->setFailureFlag();
   pimpl->inject->notify();*/
}
catch (...)
{
   LOGERR << "BDM thread failed: (unknown exception)";
   /*pimpl->inject->setFailureFlag();
   pimpl->inject->notify();*/
}

void* BlockDataManagerThread::thrun(void *_self)
{
   BlockDataManagerThread *const self
      = static_cast<BlockDataManagerThread*>(_self);
   self->run();
   return 0;
}


// kate: indent-width 3; replace-tabs on;

